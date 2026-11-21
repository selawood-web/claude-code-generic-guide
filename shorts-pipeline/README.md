# shorts-pipeline

Automated faceless short-form video production: one 1080x1920 video every N days
(default 3), written, voiced, illustrated, captioned, rendered and published without
a human in the loop.

```
topic ──► script (Claude) ──► voice (ElevenLabs, word timings)
                 │                       │
                 └──► visuals (fal.ai / Pexels)
                                         │
      ffmpeg: Ken Burns + concat + word-highlight captions + loudnorm ◄──┘
                                         │
                     YouTube Shorts · Instagram Reels · TikTok
```

Each stage is a provider behind a Protocol (`providers/base.py`). Swap a tool by
changing one line of `config.yaml`; the pipeline never knows which tool ran.

## Quick start (offline, no keys)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"          # needs ffmpeg >= 6 on PATH
shorts --mock run                # renders data/jobs/<id>/final.mp4 with mock providers
shorts --mock status
```

## Production

1. `cp config.example.yaml config.yaml` and `cp .env.example .env`; fill in the keys for
   the providers you chose. `shorts doctor` lists exactly what is missing.
2. `shorts run` produces and publishes one video now.
3. `shorts serve` keeps running: a health/media server on `$PORT` plus the scheduler,
   which publishes whenever the last successful publish is `every_days` old and resumes
   any job that crashed mid-way before starting a new one.

### Commands

| Command | Does |
|---|---|
| `shorts run [--job-id X]` | Script, voice, visuals, render, publish. Prints the MP4 path and per-platform result. |
| `shorts resume <job-id>` | Continue from the last completed stage (a failed publish does not re-render). |
| `shorts status` | Job list, last publish, next due time. |
| `shorts doctor` | ffmpeg present, every required key for the configured providers set. |
| `shorts serve [--once]` | Deployed entry point: `/health`, `/runs`, `/media/<job>/final.mp4`, scheduler loop. |

Every job lives in `data/jobs/<job-id>/` with a `manifest.json` recording completed
stages, the script, word timings, visuals, the final video and publish results.

## Platform prerequisites (one-time, outside this code)

| Platform | What you need | Notes |
|---|---|---|
| YouTube | Google Cloud project with YouTube Data API v3, OAuth client (desktop), a refresh token with `youtube.upload` scope | `videos.insert` costs 1,600 of the 10,000 daily quota units; one upload every 3 days is nowhere near the limit. Vertical and under 3 min = Short. |
| Instagram | Instagram Business/Creator account linked to a Facebook Page, Meta app with `instagram_content_publish`, long-lived token | Instagram downloads the video from a public URL, so the service must be reachable (`SHORTS_PUBLIC_BASE_URL`). 100 API posts / 24h. |
| TikTok | TikTok developer app with Content Posting API and `video.publish` scope | Until TikTok audits the app, every post is forced private. Keep `tiktok_privacy: SELF_ONLY` until approved, then switch to `PUBLIC_TO_EVERYONE`. ~15 posts/day/creator. |

Token refresh for Instagram (60-day long-lived tokens) and TikTok (24h access tokens with
refresh tokens) is not automated here; use a secrets manager or rotate via a small job.

## Deploy (Railway)

`railway.toml` and the `Dockerfile` describe one service. Attach a volume at `/app/data`,
set the environment variables from `.env.example`, upload `config.yaml` (or bake it into the
image), and the health check at `/health` reports the next due time.

Restart path: `railway up` redeploys; the scheduler resumes unfinished jobs from the volume
on start. Locally: `shorts serve`.

A GitHub Actions alternative is in `deploy/github-actions-every-3-days.yml`.

## Cost per video (order of magnitude, verify against live pricing)

Claude script ≈ cents; ElevenLabs ≈ 1,000 characters per 40-second video; fal.ai FLUX
schnell ≈ a few cents for 5–6 images; stock video via Pexels is free. Publishing APIs are free.

## Development

```bash
ruff check . && ruff format --check . && mypy && pytest
```

The end-to-end test renders a real MP4 with mock providers; the publisher tests replay
each platform's documented request sequence against an in-memory HTTP transport.
