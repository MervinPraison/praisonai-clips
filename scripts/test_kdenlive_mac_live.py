"""Real MCP crop/undo/redo/save test, restricted to our disposable Mac demo."""
import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/mac-live"
PROJECT = OUT / "live-review.kdenlive"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def saved_rect():
    tree = ET.parse(PROJECT)
    entries = tree.findall(".//playlist/entry")
    rects = [p.text for entry in entries for effect in entry.findall("filter")
             if effect.findtext("property[@name='kdenlive_id']") == "qtblend"
             for p in effect.findall("property[@name='rect']")]
    assert len(rects) == 1, rects
    return [float(n) for n in rects[0].rsplit("=", 1)[1].split()][:4]


def render(label):
    image = OUT / f"{label}.png"
    # Native MLT renders the saved active sequence, including the live-saved Transform.
    with (OUT / f"{label}-render.log").open("w") as log:
        subprocess.run(["/Applications/kdenlive.app/Contents/MacOS/melt", str(PROJECT), "in=644", "out=644",
                        "-consumer", f"avformat:{image}", "vcodec=png", "an=1", "real_time=-1"],
                       check=True, stdout=log, stderr=log, timeout=60)
    assert image.exists()
    return sha(image)


async def main():
    state = json.loads((OUT / "connection.json").read_text())
    if Path(state["project"]).resolve() != PROJECT:
        raise RuntimeError("Refusing to edit a project other than our disposable live demo")
    report = {"success": False, "project": str(PROJECT), "operations": []}
    try:
        async with stdio_client(StdioServerParameters(command=str(ROOT / "scripts/kdenlive-mac-live"), args=["mcp"], cwd=str(ROOT))) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                report["tools"] = [t.name for t in (await session.list_tools()).tools]

                async def call(name, args=None):
                    response = await session.call_tool(name, args or {})
                    text = "\n".join(c.text for c in response.content if c.type == "text")
                    if response.isError:
                        raise RuntimeError(text)
                    result = json.loads(text)
                    report["operations"].append({"tool": name, "arguments": args or {}})
                    print(name, "OK", flush=True)
                    return result

                status = await call("get_live_status")
                source = next(t for t in status["timelines"] if t["title"] == "02 Editable source framing")
                clip = next(c for c in source["clips"] if not c["audio"])
                original_sha = sha(clip["resource"])
                report["source_sha256_before"] = original_sha
                await call("select_sequence", {"index": source["index"]})
                await call("seek", {"frame": 644})
                await call("save_project")
                assert saved_rect() == [0, 0, 1080, 1920], "Demo must start at full-frame fit"
                baseline = render("baseline")
                report["baseline_frame_sha256"] = baseline
                framing = dict(clip_id=clip["item"], x=-135, y=-240, width=1350, height=2400)
                changed = await call("set_framing", framing)
                assert "Transform" in changed["history"]["undoText"]
                assert changed["history"]["canUndo"]
                await call("save_project")
                assert saved_rect() == [-135, -240, 1350, 2400]
                zoomed = render("zoom125")
                report["zoom_frame_sha256"] = zoomed
                assert zoomed != baseline, "Saved native edit did not change the rendered frame"
                await call("undo")
                await call("save_project")
                assert saved_rect() == [0, 0, 1080, 1920]
                assert render("undo") == baseline
                await call("redo")
                await call("save_project")
                assert saved_rect() == [-135, -240, 1350, 2400]
                assert render("redo") == zoomed
                await call("undo")
                await call("save_project")
                assert saved_rect() == [0, 0, 1080, 1920]
                assert render("restored") == baseline
                # Native model and document stay live, with the original framing restored.
                final = await call("get_live_status")
                report["source_sha256_after"] = sha(clip["resource"])
                assert report["source_sha256_after"] == original_sha
                assert final["history"]["clean"]
                report["final_status"] = final
                report["success"] = True
    finally:
        (OUT / "live-validation.json").write_text(json.dumps(report, indent=2))
    print("PASS: live MCP framing, native undo/redo, save, rendered parity and unchanged source")


if __name__ == "__main__":
    asyncio.run(main())
