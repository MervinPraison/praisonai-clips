from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

from .pipeline import Pipeline, default_config, validate_config
from .store import Store


def doctor():
    result = {"python": sys.version.split()[0], "openai_api_key_present": bool(os.getenv("OPENAI_API_KEY")),
              "ffmpeg": shutil.which("ffmpeg"), "ffprobe": shutil.which("ffprobe"),
              "cpu_count": os.cpu_count(), "render_backend": "CPU / libx264 (GPU not required)"}
    if result["ffmpeg"]:
        p = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
        result["subtitle_filter"] = " subtitles " in p.stdout
        result["loudnorm_filter"] = " loudnorm " in p.stdout
        p = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
        result["h264_encoder"] = "libx264" in p.stdout
    try:
        import openai
        result["openai_sdk"] = openai.__version__
        result["responses_structured_output"] = hasattr(openai.OpenAI(api_key="diagnostic-only").responses, "parse")
    except ImportError:
        result["openai_sdk"] = None
    return result


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Create reviewed vertical Shorts using OpenAI and FFmpeg")
    parser.add_argument("--data-dir", default=os.getenv("SHORTS_DATA_DIR", "data"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Check hardware, FFmpeg and API prerequisites")
    commands.add_parser("list", help="List durable jobs")
    run = commands.add_parser("run", help="Create and run a job (paid OpenAI calls)")
    run.add_argument("video", type=Path)
    run.add_argument("--max-clips", type=int, default=5)
    run.add_argument("--min-duration", type=float, default=30)
    run.add_argument("--max-duration", type=float, default=60)
    resume = commands.add_parser("resume", help="Resume a failed/cancelled job from cached analysis")
    resume.add_argument("job_id")
    cancel = commands.add_parser("cancel", help="Request worker cancellation")
    cancel.add_argument("job_id")
    export = commands.add_parser("export-kdenlive", help="Export editable source cuts with caption sidecars through optional Kdenlive MCP")
    export.add_argument("job_id")
    status = commands.add_parser("status")
    status.add_argument("job_id")
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            print(json.dumps(doctor(), indent=2))
            return
        store = Store(args.data_dir)
        if args.command == "list":
            print(json.dumps(store.list(), indent=2))
        elif args.command == "status":
            print(json.dumps(store.get(args.job_id), indent=2))
        elif args.command == "export-kdenlive":
            from .kdenlive import export_job
            print(json.dumps(export_job(store, args.job_id), indent=2))
        elif args.command == "cancel":
            store.get(args.job_id)
            store.update(args.job_id, cancel=1)
            print("Cancellation requested")
        else:
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("Set OPENAI_API_KEY in .env or the environment before running paid analysis")
            if args.command == "run":
                config = default_config(max_clips=args.max_clips, min_duration=args.min_duration,
                                        max_duration=args.max_duration)
                validate_config(config)
                job_id = store.create(args.video, config)
                print(f"Job: {job_id}", flush=True)
            else:
                job_id = args.job_id
                # Never clear cancellation while a worker still owns the job.
                import fcntl
                with (store.job_dir(job_id) / "worker.lock").open("a") as lock:
                    try:
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        raise ValueError("Worker is still active; wait for cancellation to finish")
                    store.update(job_id, cancel=0)
            result = Pipeline(store, job_id).run()
            print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
