# Installation

Use Python 3.11 or newer and FFmpeg with `libx264`, the `subtitles` filter (libass), and `loudnorm`.

```sh
git clone https://github.com/MervinPraison/praisonai-clips.git
cd praisonai-clips
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp .env.example .env
```

Copy `.env.example` only on first setup; preserve an existing `.env`. Set `OPENAI_API_KEY` in that file. OpenAI usage is billed to your API account; source audio and sampled frames are sent to OpenAI.

## FFmpeg on macOS

The Mac validation used Homebrew's `ffmpeg-full` because the installed standard build lacked subtitle rendering:

```sh
brew install ffmpeg-full
export PATH="$(brew --prefix ffmpeg-full)/bin:$PATH"
.venv/bin/praisonai-clips doctor
```

Check that `subtitle_filter`, `loudnorm_filter` and `h264_encoder` are true. `doctor` performs no paid API requests. On Debian/Ubuntu, install `ffmpeg` and `python3-venv` through apt.

If your virtual environment has no pip, `uv pip install --python .venv/bin/python -e '.[dev]'` is an alternative.

[Make your first clip →](quickstart.md)
