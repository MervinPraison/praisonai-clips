# Command line reference

Run commands in the installed environment. The global `--data-dir` option goes **before** the command.

```sh
praisonai-clips --data-dir ./data doctor
```

| Command | Behavior |
| --- | --- |
| `doctor` | Inspect Python, FFmpeg and API key presence without paid calls |
| `run VIDEO` | Create a job and process a local source with paid OpenAI calls |
| `list` | List durable jobs |
| `status JOB_ID` | Print job state |
| `cancel JOB_ID` | Request worker cancellation |
| `resume JOB_ID` | Continue a failed or cancelled job using cached analysis |
| `export-kdenlive JOB_ID` | Export source cuts through the optional Kdenlive runtime |

## Selection options

```sh
praisonai-clips run 'input/video.mp4' \
  --max-clips 3 --min-duration 30 --max-duration 60
```

Defaults are five clips, minimum 30 seconds and maximum 60 seconds. Run `praisonai-clips --help` or `praisonai-clips run --help` for the installed interface.

## Supporting tools

```sh
streamlit run app.py
python scripts/serve_preview.py
```

Native editor adapters have separate setup requirements: [Kdenlive](../KDENLIVE_LIVE_CONTROL.md) and [Resolve](../RESOLVE_LIVE_CONTROL.md).
