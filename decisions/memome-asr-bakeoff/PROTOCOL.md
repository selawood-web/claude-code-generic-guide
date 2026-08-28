# Hebrew ASR bake-off — protocol

Week-1 spike, condition 1 of the Go in
[../2026-08-28-memome-product-brief.md](../2026-08-28-memome-product-brief.md).
This is the **kill criterion**: MemoMe is voice-first, and every published Hebrew
WER number is from clean read-speech benchmarks — nobody has measured the audio
MemoMe will actually get. Measure before building.

## Why this can't be run for you

The definitive input is **your own voice**: spontaneous, rambling, code-switched
Hebrew captured on your phone in real conditions. No benchmark substitutes for it
(a sandboxed run was attempted 2026-08-28; model hosts were network-blocked, and
synthetic audio would have produced numbers worth nothing). Total cost of the real
thing: ~1-2 hours.

## Step 1 — Record 15-20 clips (the honest distribution)

Use your normal phone voice-memo app, held the way you'd actually capture. 10-30
seconds each. Speak the way you actually would — mid-thought, ums, half-sentences,
brand names in English.

| # clips | Condition |
|---------|-----------|
| 4 | Quiet room (baseline) |
| 4 | Driving, radio at normal volume |
| 3 | Street / outdoors, walking |
| 3 | Kitchen or with TV / kids in the background |
| 2 | Low voice, as if capturing during a meeting |
| 2 | Shopping-list style rapid item strings ("חלב, לחם, במבה, שקית קמח...") |

Content should cover MemoMe's real intents: tasks with dates ("לשלם ארנונה עד
חמישי"), ideas ("יש לי רעיון לאפליקציה ש..."), shopping items, multi-intent
("לקנות חלב וגם לקבוע תור לרופא").

## Step 2 — Reference transcripts

For each `clip.wav` (convert m4a: `ffmpeg -i clip.m4a clip.wav`), write `clip.txt`
with exactly what you said, including the English words. Don't clean up grammar —
the reference is what was said, not what you meant. Punctuation/niqqud don't
matter (the scorer strips them).

## Step 3 — Run

```bash
pip install faster-whisper jiwer soundfile scipy numpy requests
python run_bakeoff.py --data-dir ./samples --out report.md
# with Scribe too:
ELEVENLABS_API_KEY=... python run_bakeoff.py --data-dir ./samples \
    --engines vanilla,ivrit,elevenlabs --out report.md
```

First run downloads ~1.6 GB per local model. CPU is fine (expect a few minutes).
The harness scores each engine on your audio as-is **and** on a simulated
telephone channel with added noise — a floor for worse-than-recorded conditions.

Model ids `[UNVERIFIED — could not reach Hugging Face from the build sandbox]`:
`deepdml/faster-whisper-large-v3-turbo-ct2` (vanilla) and
`ivrit-ai/whisper-large-v3-turbo-ct2` (fine-tune). If the ivrit id 404s, pick the
current CT2 conversion from https://huggingface.co/ivrit-ai and pass
`--ivrit-model`.

## Step 4 — Decide (thresholds)

WER after Hebrew normalization, on the **original** condition (your real
recordings; `phone+n` is the stress margin, not the gate):

| Result | Call |
|--------|------|
| Best engine ≤ 10% | **Pass, comfortable.** Voice-first proceeds; pick that engine. |
| Best engine 10-15% | **Pass, tight.** Proceed; Smart Triage + preview-before-save carry the correction load — track `classification_accepted` from day one. |
| Best engine 15-25% | **Yellow.** Voice stays but text/list capture become the trust path; re-run bake-off monthly as models improve; consider ivrit.ai non-turbo large-v3 or Scribe API despite cost. |
| All engines > 25% | **Kill criterion fires.** Reopen the brief (revisit trigger 1): pivot MVP to text/list-first, voice behind a flag. |

Also record from the run: RTF (real-time factor — matters for the <8s AI budget)
and eyeball the per-clip transcripts in the report for *semantic* damage (a wrong
date or a wrong product is worse than a misspelled filler word — WER weighs them
the same, your read shouldn't).

## Step 5 — Close the loop

Paste the report table into the brief's **Outcome** section, set the verdict
line (pass / yellow / kill), and commit both. If yellow or kill, the brief's
status and MVP scope change — run `/decide` on the pivot before writing code.
