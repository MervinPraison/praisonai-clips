# PraisonAI Clips

Built with OpenAI Codex under Mervin Praison’s direction. Turn long videos into captioned vertical clips and edit framing live in DaVinci Resolve or Kdenlive with Codex.

```sh
python -m pip install praisonai-clips
praisonai-clips studio
```

Python 3.11+, compatible FFmpeg and an OpenAI API key are required for processing your own video. OpenAI API usage is billed to your account. The app includes a free example to explore.

After starting a job, open Source evidence in the dashboard to review the source video alongside its audio waveform, timed transcript, and sampled screen descriptions. Listen and inspect before accepting cuts.

For Resolve MCP tools, install `praisonai-clips[live]`. Kdenlive live control also requires the separate Mac bridge and setup described in the documentation.

[Get started](https://clips.praison.ai/getting-started/installation/) · [Connect Codex](https://clips.praison.ai/getting-started/codex/) · [Source code](https://github.com/MervinPraison/praisonai-clips)
