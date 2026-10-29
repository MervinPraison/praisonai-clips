# Public walkthrough assets

These screenshots show an empty workspace and the generated public example. They contain no personal recordings or credentials.

- `before-onboarding.png`: the earlier explanation-first screen.
- `after-onboarding.png`: the revised app with a main-screen upload and playable example.
- `walkthrough.mp4`: 66-second silent, captioned walkthrough. It combines the earlier screenshot, an actual Playwright recording of the revised local app, and explanatory cards.
- `verification.json`: sanitized results from the local automated test run; optional dependency skips are stated explicitly.

The recording plays the generated sample, downloads its bundle, and expands the source comparison. It does not run transcription, AI selection, or editorial review. The sample's authored timings are described in `../demo/README.md`. No personal media or paid API calls are used in this walkthrough.

To rebuild the film, capture the empty local app at 1440 × 1000 with Playwright video recording. Play the public example, download the bundle, and expand the comparison. Then run `python scripts/build_walkthrough.py /path/to/recording.webm` using FFmpeg with drawtext and H.264 support. Recordings stay outside Git; only this reviewed public output is included.

The test snapshot is evidence from one macOS run, rather than a promise about every installation. The repository's **Verify project** workflow independently checks the portable suite on Linux.
