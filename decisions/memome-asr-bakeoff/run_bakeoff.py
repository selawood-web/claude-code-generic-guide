#!/usr/bin/env python3
"""MemoMe week-1 spike: Hebrew ASR bake-off.

Implements condition 1 of the Go verdict in
decisions/2026-08-28-memome-product-brief.md: measure Hebrew transcription
accuracy on REAL noisy phone audio before committing to a voice-first MVP.

Usage:
  python run_bakeoff.py --data-dir ./samples --out report.md
  python run_bakeoff.py --data-dir ./samples --engines vanilla,ivrit,elevenlabs
  python run_bakeoff.py --self-test

Data layout: for every clip, two files with the same stem —
  samples/foo.wav   16-bit PCM, any sample rate, mono or stereo
  samples/foo.txt   reference transcript (plain Hebrew text, one clip = one file)

Each clip is evaluated in three conditions:
  original   the file as recorded
  phone      band-limited 300-3400 Hz, resampled to 8 kHz (telephone channel)
  phone+n    phone channel + additive noise at --snr-db (default 5 dB)

Engines:
  vanilla     faster-whisper, openai large-v3-turbo   (local, CPU ok)
  ivrit       faster-whisper, ivrit.ai Hebrew fine-tune (local, CPU ok)
  elevenlabs  Scribe API — needs ELEVENLABS_API_KEY    (original audio only
              is NOT enough: degraded conditions are uploaded too)

Install: pip install faster-whisper jiwer soundfile scipy numpy requests
"""

import argparse
import os
import re
import sys
import tempfile
import time
import unicodedata

import numpy as np

# ---------------------------------------------------------------------------
# Model registry. The ivrit.ai CT2 repo id is the best-known name as of
# 2026-08; if HF returns 404, list https://huggingface.co/ivrit-ai and pass
# the current CT2 conversion via --ivrit-model.
# ---------------------------------------------------------------------------
VANILLA_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"
IVRIT_MODEL = "ivrit-ai/whisper-large-v3-turbo-ct2"

HEBREW_DIACRITICS = re.compile(r"[֑-ׇ]")
PUNCT = re.compile(r"[^\w\sא-ת]", re.UNICODE)


def normalize_hebrew(text: str) -> str:
    """Normalize for WER: strip niqqud/teamim, punctuation, excess space.

    Final letters are kept — they are orthography, not noise. Digits and
    Latin are kept — Hebrew speech code-switches and the ASR must handle it.
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    text = unicodedata.normalize("NFC", text)
    text = HEBREW_DIACRITICS.sub("", text)
    text = PUNCT.sub(" ", text)
    return " ".join(text.split()).strip()


def load_audio(path: str):
    import soundfile as sf

    audio, sr = sf.read(path, dtype="float32", always_2d=True)
    return audio.mean(axis=1), sr  # downmix to mono


def degrade_phone(audio: np.ndarray, sr: int, snr_db=None, seed=0):
    """Telephone-channel simulation: 300-3400 Hz bandpass, 8 kHz, optional noise.

    Returns (audio, 8000). snr_db=None -> clean phone channel.
    """
    from scipy.signal import butter, resample_poly, sosfilt

    if audio.size == 0:
        raise ValueError("empty audio")
    nyq = sr / 2.0
    high = min(3400.0, nyq * 0.99)
    sos = butter(4, [300.0 / nyq, high / nyq], btype="band", output="sos")
    band = sosfilt(sos, audio)
    out_sr = 8000
    band = resample_poly(band, out_sr, sr)
    if snr_db is not None:
        rng = np.random.default_rng(seed)
        # Pink-ish noise: filtered white noise approximates babble/street floor
        noise = rng.standard_normal(band.shape[0]).astype(np.float32)
        noise = np.cumsum(noise)
        noise -= noise.mean()
        noise /= (np.abs(noise).max() + 1e-9)
        sig_pow = float(np.mean(band**2)) + 1e-12
        noise_pow = float(np.mean(noise**2)) + 1e-12
        target = sig_pow / (10 ** (snr_db / 10.0))
        band = band + noise * np.sqrt(target / noise_pow)
    peak = np.abs(band).max()
    if peak > 1.0:
        band = band / peak
    return band.astype(np.float32), out_sr


# ---------------------------------------------------------------------------
# Engines
# ---------------------------------------------------------------------------
class FasterWhisperEngine:
    def __init__(self, model_id: str, name: str):
        from faster_whisper import WhisperModel

        self.name = name
        self.model = WhisperModel(model_id, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray, sr: int) -> str:
        import soundfile as sf

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, sr)
            path = f.name
        try:
            segments, _ = self.model.transcribe(path, language="he", beam_size=5)
            return " ".join(s.text for s in segments)
        finally:
            os.unlink(path)


class ElevenLabsEngine:
    name = "elevenlabs-scribe"

    def __init__(self):
        self.key = os.environ.get("ELEVENLABS_API_KEY")
        if not self.key:
            raise RuntimeError("ELEVENLABS_API_KEY not set")

    def transcribe(self, audio: np.ndarray, sr: int) -> str:
        import io

        import requests
        import soundfile as sf

        buf = io.BytesIO()
        sf.write(buf, audio, sr, format="WAV")
        buf.seek(0)
        r = requests.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": self.key},
            data={"model_id": "scribe_v1", "language_code": "he"},
            files={"file": ("clip.wav", buf, "audio/wav")},
            timeout=120,
        )
        r.raise_for_status()
        return r.json().get("text", "")


class StubEngine:
    """Self-test engine: echoes the reference (set per-clip by the harness)."""

    name = "stub"
    reference = ""

    def transcribe(self, audio, sr):
        return self.reference


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------
def collect_clips(data_dir: str):
    clips = []
    for fn in sorted(os.listdir(data_dir)):
        if fn.lower().endswith(".wav"):
            stem = fn[:-4]
            ref = os.path.join(data_dir, stem + ".txt")
            if not os.path.exists(ref):
                print(f"skip {fn}: no {stem}.txt reference", file=sys.stderr)
                continue
            with open(ref, encoding="utf-8") as f:
                text = f.read()
            if not normalize_hebrew(text):
                print(f"skip {fn}: empty reference", file=sys.stderr)
                continue
            clips.append((stem, os.path.join(data_dir, fn), text))
    if not clips:
        raise SystemExit(f"no (wav, txt) pairs found in {data_dir}")
    return clips


def evaluate(engines, clips, snr_db):
    import jiwer

    rows = []  # (engine, condition, wer, cer, rtf)
    details = []
    for engine in engines:
        for cond in ("original", "phone", "phone+n"):
            refs, hyps, audio_sec, wall = [], [], 0.0, 0.0
            for stem, wav, ref_text in clips:
                audio, sr = load_audio(wav)
                if cond == "phone":
                    audio, sr = degrade_phone(audio, sr)
                elif cond == "phone+n":
                    audio, sr = degrade_phone(audio, sr, snr_db=snr_db)
                if isinstance(engine, StubEngine):
                    engine.reference = ref_text
                t0 = time.time()
                hyp = engine.transcribe(audio, sr)
                wall += time.time() - t0
                audio_sec += len(audio) / sr
                r, h = normalize_hebrew(ref_text), normalize_hebrew(hyp)
                refs.append(r)
                hyps.append(h if h else "*")  # jiwer rejects empty hypotheses
                details.append((engine.name, cond, stem, r, h))
            wer = jiwer.wer(refs, hyps)
            cer = jiwer.cer(refs, hyps)
            rtf = wall / audio_sec if audio_sec else float("inf")
            rows.append((engine.name, cond, wer, cer, rtf))
            print(f"{engine.name:>20} | {cond:>8} | WER {wer:6.1%} | "
                  f"CER {cer:6.1%} | RTF {rtf:5.2f}")
    return rows, details


def write_report(path, rows, details, n_clips, snr_db):
    lines = [
        "# Hebrew ASR bake-off — results",
        "",
        f"- Clips: {n_clips}  |  noisy condition SNR: {snr_db} dB",
        f"- Date: {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "| Engine | Condition | WER | CER | RTF |",
        "|--------|-----------|-----|-----|-----|",
    ]
    for name, cond, wer, cer, rtf in rows:
        lines.append(f"| {name} | {cond} | {wer:.1%} | {cer:.1%} | {rtf:.2f} |")
    lines += [
        "",
        "Decision thresholds (see PROTOCOL.md): pass = WER ≤ 15% on phone+n for",
        "at least one engine; kill/pivot = all engines > 25% on phone+n.",
        "",
        "## Per-clip transcripts",
        "",
    ]
    for name, cond, stem, ref, hyp in details:
        lines += [f"### {name} / {cond} / {stem}", f"- ref: {ref}", f"- hyp: {hyp}", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"report written: {path}")


def self_test():
    """Offline check of everything except real model inference."""
    import jiwer

    # normalize: niqqud stripped, punctuation stripped
    assert normalize_hebrew("שָׁלוֹם, עוֹלָם!") == "שלום עולם"
    # final letters preserved
    assert normalize_hebrew("שולחן") == "שולחן"
    # code-switch and digits preserved
    assert normalize_hebrew("תקנה 3 חלב ב-AM:PM") == "תקנה 3 חלב ב AM PM"
    # empty and whitespace-only input
    assert normalize_hebrew("") == "" and normalize_hebrew("  ,.  ") == ""
    # wrong type fails loudly
    try:
        normalize_hebrew(None)
        raise AssertionError("expected TypeError")
    except TypeError:
        pass
    # WER sanity on Hebrew
    assert jiwer.wer("שלום עולם", "שלום עולם") == 0.0
    assert abs(jiwer.wer("קנה חלב ולחם", "קנה חלב") - 1 / 3) < 1e-9
    # degradation: output is 8 kHz, same duration ±1%, finite, within [-1, 1]
    sr = 44100
    t = np.linspace(0, 2.0, 2 * sr, endpoint=False)
    tone = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    for snr in (None, 5, 0):
        out, out_sr = degrade_phone(tone, sr, snr_db=snr)
        assert out_sr == 8000
        assert abs(len(out) / out_sr - 2.0) < 0.02
        assert np.isfinite(out).all() and np.abs(out).max() <= 1.0
    # noise actually lowers SNR: noisy differs from clean phone channel
    clean, _ = degrade_phone(tone, sr)
    noisy, _ = degrade_phone(tone, sr, snr_db=0)
    assert float(np.mean((clean - noisy) ** 2)) > 1e-6
    # empty audio fails loudly
    try:
        degrade_phone(np.array([], dtype=np.float32), sr)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    # end-to-end harness with stub engine on generated clips
    import soundfile as sf

    with tempfile.TemporaryDirectory() as d:
        for i, text in enumerate(["תקנה חלב ולחם", "פגישה עם רופא ביום שלישי"]):
            sf.write(os.path.join(d, f"c{i}.wav"), tone, sr)
            with open(os.path.join(d, f"c{i}.txt"), "w", encoding="utf-8") as f:
                f.write(text)
        # a wav without a reference must be skipped, not crash
        sf.write(os.path.join(d, "orphan.wav"), tone, sr)
        clips = collect_clips(d)
        assert len(clips) == 2
        rows, details = evaluate([StubEngine()], clips, snr_db=5)
        assert all(wer == 0.0 for _, _, wer, _, _ in rows)
        report = os.path.join(d, "r.md")
        write_report(report, rows, details, len(clips), 5)
        assert os.path.getsize(report) > 0
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", help="directory of wav+txt pairs")
    ap.add_argument("--out", default="bakeoff-report.md")
    ap.add_argument("--engines", default="vanilla,ivrit",
                    help="comma list: vanilla,ivrit,elevenlabs")
    ap.add_argument("--snr-db", type=float, default=5.0)
    ap.add_argument("--vanilla-model", default=VANILLA_MODEL)
    ap.add_argument("--ivrit-model", default=IVRIT_MODEL)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.data_dir:
        ap.error("--data-dir is required (or use --self-test)")

    engines = []
    for name in args.engines.split(","):
        name = name.strip()
        if name == "vanilla":
            engines.append(FasterWhisperEngine(args.vanilla_model, "whisper-v3-turbo"))
        elif name == "ivrit":
            engines.append(FasterWhisperEngine(args.ivrit_model, "ivrit-v3-turbo"))
        elif name == "elevenlabs":
            engines.append(ElevenLabsEngine())
        else:
            ap.error(f"unknown engine: {name}")

    clips = collect_clips(args.data_dir)
    print(f"{len(clips)} clips, engines: {[e.name for e in engines]}")
    rows, details = evaluate(engines, clips, args.snr_db)
    write_report(args.out, rows, details, len(clips), args.snr_db)


if __name__ == "__main__":
    main()
