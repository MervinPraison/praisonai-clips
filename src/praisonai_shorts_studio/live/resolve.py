"""Transport-independent Resolve operations. All mutations check project identity."""
from dataclasses import asdict
from pathlib import Path

from .lua import guard_project, lua_number, lua_string, validate_envelope
from .models import ClipTarget, Framing, framing_changes
from .transports import LuaTransport, MacOSConsoleTransport


class ResolveClient:
    def __init__(self, transport: LuaTransport | None = None):
        self.transport = transport if transport is not None else MacOSConsoleTransport()

    def _execute(self, code: str) -> dict:
        return validate_envelope(self.transport.execute(code))

    def run_lua(self, code: str, *, expected_project_id: str) -> dict:
        """Guarded escape hatch. A Lua error can follow partial changes; no retries."""
        return self._execute(guard_project(expected_project_id, code))

    def status(self) -> dict:
        return self._execute("local p=resolve:GetProjectManager():GetCurrentProject(); "
                             "return {alive=true,product=resolve:GetProductName(),version=resolve:GetVersionString(),"
                             "project=p and {name=p:GetName(),id=p:GetUniqueId()} or nil}")["result"]

    def project_info(self) -> dict:
        return self._execute("local p=assert(resolve:GetProjectManager():GetCurrentProject(),'No project'); "
                             "return {name=p:GetName(),id=p:GetUniqueId(),timeline_count=p:GetTimelineCount()}")["result"]

    def timeline_items(self, track_index: int = 1) -> list[dict]:
        if type(track_index) is not int or track_index < 1:
            raise ValueError("track_index must be a positive integer")
        result = self._execute("local p=assert(resolve:GetProjectManager():GetCurrentProject(),'No project'); "
                               "local t=assert(p:GetCurrentTimeline(),'No timeline'); local result={}; "
                               f"for i,c in ipairs(t:GetItemListInTrack('video',{track_index}) or {{}}) do "
                               "result[#result+1]={target={project_id=p:GetUniqueId(),timeline_id=t:GetUniqueId(),"
                               f"clip_id=c:GetUniqueId(),track_index={track_index},clip_index=i}},"
                               "name=c:GetName(),properties=c:GetProperties()} end; return result")["result"]
        # The upstream serializer encodes an empty Lua table as {}, not [].
        return [] if result == {} else result

    @staticmethod
    def _clip_code(target: ClipTarget, code: str) -> str:
        return ("local t=assert(guarded_project:GetCurrentTimeline(),'No timeline'); "
                "assert(t:GetUniqueId()==" + lua_string(target.timeline_id) + ", 'Timeline changed'); "
                f"local c=assert((t:GetItemListInTrack('video',{target.track_index}) or {{}})[{target.clip_index}], 'Clip missing'); "
                "assert(c:GetUniqueId()==" + lua_string(target.clip_id) + ", 'Clip changed'); " + code)

    def get_framing(self, target: ClipTarget) -> Framing:
        result = self.run_lua(self._clip_code(target, "return c:GetProperties()"),
                              expected_project_id=target.project_id)["result"]
        return Framing.from_properties(result)

    def set_framing(self, target: ClipTarget, **changes: float) -> dict:
        """Apply a partial framing change; return before/after values for restoration.

        Zoom axes are independent in this API: provide both for uniform scaling.
        """
        properties = framing_changes(changes)
        table = "{" + ",".join(f"{key}={lua_number(value)}" for key,value in properties.items()) + "}"
        checks = " and ".join(f"math.abs(after.{key}-{lua_number(value)})<0.0001" for key,value in properties.items())
        code = ("local before=c:GetProperties(); assert(c:SetProperties(" + table + "), 'Framing change rejected'); "
                "local after=c:GetProperties(); assert(" + checks + ", 'Framing readback mismatch'); "
                "return {before=before,after=after}")
        result = self.run_lua(self._clip_code(target, code), expected_project_id=target.project_id)["result"]
        return {"target": asdict(target), "before": Framing.from_properties(result["before"]).to_dict(),
                "after": Framing.from_properties(result["after"]).to_dict()}

    def restore_framing(self, target: ClipTarget, original: Framing) -> dict:
        return self.set_framing(target, **original.to_dict())

    def save_project(self, expected_project_id: str) -> bool:
        return self.run_lua("assert(resolve:GetProjectManager():SaveProject(),'Save failed'); return true",
                            expected_project_id=expected_project_id)["result"]

    def export_frame(self, expected_project_id: str, path: Path) -> Path:
        path = Path(path).expanduser().resolve()
        if path.suffix.lower() != ".png":
            raise ValueError("Use a .png path for a native frame export")
        if path.exists():
            raise FileExistsError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.run_lua("assert(guarded_project:ExportCurrentFrameAsStill(" + lua_string(str(path)) +
                     "), 'Frame export failed'); return true", expected_project_id=expected_project_id)
        if not path.is_file():
            raise RuntimeError("Resolve reported success but the exported frame is missing")
        return path

    def plan_silence(self, target, **options):
        from .silence import plan_silence
        return plan_silence(self, target, **options)

    def apply_silence_plan(self, plan, *, timeline_name):
        from .silence import apply_silence_plan
        return apply_silence_plan(self, plan, timeline_name=timeline_name)
