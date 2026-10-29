"""Typed live controls over the experimental local native Qt bridge.

All editing happens in the running editor, on its main thread. No mouse events,
keyboard events, accessibility actions, or external XML edits are used here.
"""
from pathlib import Path
import json
import math
import os
import urllib.request


class LiveClient:
    def __init__(self, connection: Path):
        self.connection = connection
        self.state = json.loads(connection.read_text())

    def request(self, **payload):
        os.kill(self.state["pid"], 0)
        request = urllib.request.Request(
            f'http://127.0.0.1:{self.state["port"]}/',
            data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + self.state["token"], "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
        if not result.get("ok"):
            raise RuntimeError(result.get("error", "Native bridge operation failed"))
        return result

    def objects(self, class_name):
        return [o for o in self.request(op="objects", match=class_name)["objects"] if o["class"] == class_name]

    def inspect(self, obj):
        return self.request(op="inspect", id=obj["id"])

    def invoke(self, obj, method, *args):
        return self.request(op="invoke", id=obj["id"], method=method, args=args).get("result")

    def one(self, class_name):
        objects = self.objects(class_name)
        if len(objects) != 1:
            raise RuntimeError(f"Expected exactly one {class_name}; found {len(objects)}")
        return objects[0]

    def undo_stack(self):
        return self.inspect(self.one("QUndoView"))["stack"]

    def guard(self):
        main = self.inspect(self.one("MainWindow"))
        stem = Path(self.state["project"]).stem
        if not main["properties"]["windowTitle"].startswith(stem + " "):
            raise RuntimeError("The running editor has a different document open")
        stack = self.undo_stack()
        if stack["id"] != self.state.get("document_stack"):
            raise RuntimeError("Document identity changed; launch a fresh guarded connection")
        return main

    def bind(self):
        """Only called after launch, before permitting edits."""
        self.state["document_stack"] = self.undo_stack()["id"]
        self.guard()
        self.connection.write_text(json.dumps(self.state, indent=2))
        self.connection.chmod(0o600)

    def timelines(self):
        self.guard()
        tabs = self.inspect(self.one("TimelineTabs"))
        controllers = {o["parent"]: o for o in self.objects("TimelineController")}
        models = {}
        for obj in self.objects("QSortFilterProxyModel"):
            info = self.inspect(obj)
            model = info.get("sourceModel", {})
            if model.get("class") == "TimelineItemModel":
                models[obj["parent"]] = model
        result = []
        for tab in tabs["tabs"]:
            parent = tab["widget"]["id"]
            model = models[parent]
            tracks = self.request(op="rows", id=model["id"])["rows"]
            clips = []
            for track in tracks:
                for clip in self.request(op="rows", id=model["id"], parent=[track["row"]])["rows"]:
                    clips.append({key: clip.get(key) for key in
                                  ("item", "name", "resource", "trackId", "start", "duration", "in", "out", "audio", "effectNames")})
            result.append(dict(index=tab["index"], title=tab["title"],
                               active=tab["index"] == tabs["properties"]["currentIndex"],
                               controller=controllers[parent], clips=clips))
        return result

    def status(self):
        main = self.guard()
        return dict(pid=self.state["pid"], project=self.state["project"],
                    modified=main["properties"]["windowModified"],
                    history=self.inspect(self.undo_stack())["properties"], timelines=self.timelines())

    def select_sequence(self, index: int):
        if index not in [t["index"] for t in self.timelines()]:
            raise ValueError("Unknown sequence index")
        self.invoke(self.one("TimelineTabs"), "setCurrentIndex(int)", index)
        return self.status()

    def active(self):
        return next(t for t in self.timelines() if t["active"])

    def seek(self, frame: int):
        timeline = self.active()
        duration = max((c["start"] + c["duration"] for c in timeline["clips"]), default=0)
        if not 0 <= frame < duration:
            raise ValueError(f"Frame must be between 0 and {duration - 1}")
        self.invoke(timeline["controller"], "setPosition(int)", frame)
        return dict(frame=frame)

    def transform(self, clip_id: int, x: float, y: float, width: float, height: float):
        if not all(math.isfinite(value) for value in (x, y, width, height)):
            raise ValueError("Frame rectangle must contain finite numbers")
        if not 0 < width <= 20000 or not 0 < height <= 20000 or max(abs(x), abs(y)) > 20000:
            raise ValueError("Invalid frame rectangle")
        timeline = self.active()
        clip = next((c for c in timeline["clips"] if c["item"] == clip_id and not c["audio"]), None)
        if clip is None:
            raise ValueError("clip_id must be a video clip in the active sequence")
        controller = timeline["controller"]
        self.invoke(controller, "selectItems(QList<int>)", [clip_id])
        # The GeometryWidget belongs to the active native Transform editor.
        # More than one effect would make this ambiguous: refuse instead of guessing.
        names = [n for n in (clip["effectNames"] or "").split("/") if n]
        if names != ["Transform"]:
            raise RuntimeError(f"Clip must have exactly one native Transform effect; found {names}")
        self.invoke(controller, "showAsset(int)", clip_id)
        geometry = self.one("GeometryWidget")
        self.invoke(geometry, "slotUpdateGeometryRect(QRectF)", [x, y, width, height])
        return dict(clip_id=clip_id, rect=[x, y, width, height],
                    history=self.inspect(self.undo_stack())["properties"])

    def undo(self):
        self.guard()
        self.invoke(self.undo_stack(), "undo()")
        return self.status()

    def redo(self):
        self.guard()
        self.invoke(self.undo_stack(), "redo()")
        return self.status()

    def save(self):
        self.guard()
        actions = []
        for action in self.objects("QAction"):
            p = self.inspect(action)["properties"]
            if p.get("text", "").replace("&", "") == "Save":
                actions.append(action)
        if len(actions) != 1:
            raise RuntimeError(f"Expected one native Save action, found {len(actions)}")
        self.invoke(actions[0], "trigger()")
        status = self.status()
        if not status["history"]["clean"]:
            raise RuntimeError("Native save did not finish cleanly")
        return status
