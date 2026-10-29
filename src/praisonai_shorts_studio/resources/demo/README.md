# Public onboarding example

These files are generated illustrations, not user recordings. They contain no private footage, personal information, API responses, or third-party media. `example.json` describes their provenance and validation boundary.

The source is a silent 16-second graphic recording. An authored edit selects seconds 2–14, applies a centered portrait crop, and burns captions using the application's production caption exporter and FFmpeg renderer. Word times are scripted fixture data. No AI selection, transcription, visual analysis, or editorial acceptance was performed.

Rebuild from the repository root with the package installed and FFmpeg on PATH, including libass and drawtext support:

```sh
python scripts/build_demo.py
```

On the documented macOS setup, put Homebrew's `ffmpeg-full` binary directory on PATH before running the script. The builder checks the result with the application's technical media reviewer, including full decode, dimensions, codecs, duration, and A/V start times. The app and documentation share these same files.
