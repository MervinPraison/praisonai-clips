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


def main(argv=None):
    load_dotenv()
    parser = argparse.ArgumentParser(description="Create reviewed vertical Shorts using OpenAI and FFmpeg")
    parser.add_argument("--data-dir", default=os.getenv("SHORTS_DATA_DIR", "data"))
    commands = parser.add_subparsers(dest="command", required=True)
    diagnostic = commands.add_parser("doctor", help="Check hardware, FFmpeg and API prerequisites")
    diagnostic.add_argument("--check", action="store_true", help="Exit 1 if processing prerequisites are missing")
    commands.add_parser("list", help="List durable jobs")
    commands.add_parser("studio", help="Launch the local dashboard")
    workflow = commands.add_parser("workflow", help="Run or resume a staged workflow from YAML")
    workflow.add_argument("file", type=Path)
    run = commands.add_parser("run", help="Create and run a job (paid OpenAI calls)")
    run.add_argument("video", type=Path)
    run.add_argument("--max-clips", type=int, default=5)
    run.add_argument("--min-duration", type=float, default=30)
    run.add_argument("--max-duration", type=float, default=60)
    run.add_argument("--until", choices=["evidence", "selection", "render"], default="render", help="Stop after evidence, selected moments, or rendered clips")
    resume = commands.add_parser("resume", help="Resume a failed/cancelled job from cached analysis")
    resume.add_argument("job_id")
    resume.add_argument("--until", choices=["evidence", "selection", "render"], default="render", help="Continue through this stage")
    cancel = commands.add_parser("cancel", help="Request worker cancellation")
    cancel.add_argument("job_id")
    export = commands.add_parser("export-kdenlive", help="Export editable source cuts with caption sidecars through optional Kdenlive MCP")
    export.add_argument("job_id")
    status = commands.add_parser("status")
    status.add_argument("job_id")
    from .live.cli import configure as configure_resolve
    configure_resolve(commands.add_parser("resolve", help="Live Resolve SDK operations and MCP server"))
    from .live.kdenlive_cli import configure as configure_kdenlive
    configure_kdenlive(commands.add_parser("kdenlive", help="Native guarded macOS Kdenlive controls"))
    example = commands.add_parser("example", help="Export the generated public example without an API key")
    example.add_argument("--output", type=Path, required=True, help="New ZIP destination")
    preview = commands.add_parser("preview", help="Generate or serve local HTML previews")
    preview.add_argument("--serve", action="store_true", help="Serve this workspace on localhost until Ctrl-C")
    preview.add_argument("--port", type=int, default=8787)
    manifest = commands.add_parser("manifest", help="Read accepted clips, uncertain drafts and review evidence")
    manifest.add_argument("job_id")
    for name in ("bundle", "artifact"):
        command = commands.add_parser(name, help="Export a clip ZIP" if name == "bundle" else "Read a clip's named artifact")
        command.add_argument("job_id")
        command.add_argument("clip_id")
        command.add_argument("--draft", action="store_true", help="Select an uncertain draft explicitly")
        if name == "bundle":
            command.add_argument("--output", type=Path, required=True)
        else:
            command.add_argument("name", choices=["edl.json", "review.json", "words.json", "captions.srt", "captions.ass"])
    args = parser.parse_args(argv)
    try:
        if args.command == "workflow":
            from .workflow import workflow_arguments
            return main(["--data-dir", args.data_dir, *workflow_arguments(args.file)])
        if args.command == "studio":
            raise SystemExit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(Path(__file__).with_name("studio.py"))]))
        if args.command == "doctor":
            from .onboarding import processing_issues
            checks = doctor()
            issues = processing_issues(checks)
            print(json.dumps({**checks, "ready": not issues, "issues": issues}, indent=2))
            if args.check and issues:
                raise SystemExit(1)
            return
        if args.command == "kdenlive":
            from .live.kdenlive_cli import execute
            execute(args)
            return
        if args.command == "resolve":
            from .live.cli import execute
            execute(args)
            return
        if args.command == "example":
            from .onboarding import example_bundle, example_directory
            from .artifacts import write_new
            print(json.dumps({"path": str(write_new(args.output, example_bundle(example_directory())))}))
            return
        store = Store(args.data_dir)
        if args.command == "preview":
            from .preview import generate
            path = generate(store)
            if args.serve:
                from functools import partial
                from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
                with ThreadingHTTPServer(("127.0.0.1", args.port), partial(SimpleHTTPRequestHandler, directory=str(store.root))) as server:
                    print(json.dumps({"path": str(path), "url": f"http://127.0.0.1:{server.server_port}/preview/index.html"}), flush=True)
                    try:
                        server.serve_forever()
                    except KeyboardInterrupt:
                        pass
            else:
                print(json.dumps({"path": str(path)}))
        elif args.command == "manifest":
            from .artifacts import manifest
            print(json.dumps(manifest(store, args.job_id), indent=2))
        elif args.command in {"bundle", "artifact"}:
            from .artifacts import artifact_path, clip_bundle, clip_folder, write_new
            folder = clip_folder(store, args.job_id, args.clip_id, drafts=args.draft)
            if args.command == "bundle":
                print(json.dumps({"path": str(write_new(args.output, clip_bundle(folder)))}))
            else:
                source = artifact_path(folder, args.name)
                print(source.read_text(), end="")
        elif args.command == "list":
            print(json.dumps(store.list(), indent=2))
        elif args.command == "status":
            print(json.dumps(store.get(args.job_id), indent=2))
        elif args.command == "export-kdenlive":
            from .kdenlive import export_job
            print(json.dumps(export_job(store, args.job_id), indent=2))
        elif args.command == "cancel":
            store.get(args.job_id)
            store.update(args.job_id, cancel=1)
            print(json.dumps({"job_id": args.job_id, "cancellation_requested": True}))
        else:
            from .onboarding import processing_issues
            issues = processing_issues(doctor(), until=args.until)
            if issues:
                raise ValueError(" ".join(issues))
            if args.command == "run":
                config = default_config(max_clips=args.max_clips, min_duration=args.min_duration,
                                        max_duration=args.max_duration)
                validate_config(config)
                job_id = store.create(args.video, config)
                print(f"Job: {job_id}", file=sys.stderr, flush=True)
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
            result = Pipeline(store, job_id).run(until=args.until)
            print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
