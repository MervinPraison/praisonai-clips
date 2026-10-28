"""Build a local Qt bridge and an isolated, ad-hoc signed Kdenlive app copy."""
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys


def build(runtime: Path, application: Path) -> tuple[Path, Path]:
    if sys.platform != "darwin":
        raise RuntimeError("The native bridge is macOS-only")
    runtime.mkdir(parents=True, exist_ok=True)
    qmake = shutil.which("qmake6") or shutil.which("qmake")
    if not qmake:
        raise RuntimeError("Qt 6 development headers are required (brew install qt)")
    qt_version = subprocess.check_output([qmake, "-query", "QT_VERSION"], text=True).strip()
    info = application / "Contents/Frameworks/QtCore.framework/Resources/Info.plist"
    app_version = plistlib.loads(info.read_bytes())["CFBundleShortVersionString"]
    if qt_version.split(".")[:2] != app_version.split(".")[:2]:
        raise RuntimeError(f"Qt headers {qt_version} must match app's Qt {app_version} major/minor")
    qt_lib = subprocess.check_output([qmake, "-query", "QT_INSTALL_LIBS"], text=True).strip()
    library = runtime / "libpraison-live.dylib"
    run = lambda args: subprocess.run(args, check=True)
    run(["clang++", "-std=c++17", "-dynamiclib", str(Path(__file__).with_name("bridge.cpp")),
         "-o", str(library), "-F" + qt_lib, "-framework", "QtCore", "-framework", "QtWidgets",
         "-framework", "QtNetwork", "-framework", "QtGui",
         "-Wl,-rpath,@executable_path/../Frameworks"])
    dependencies = subprocess.check_output(["otool", "-L", str(library)], text=True)
    for line in dependencies.splitlines()[1:]:
        dependency = line.strip().split(" (", 1)[0]
        for name in ("QtCore", "QtWidgets", "QtNetwork", "QtGui"):
            if f"/{name}.framework/" in dependency:
                run(["install_name_tool", "-change", dependency,
                     f"@executable_path/../Frameworks/{name}.framework/Versions/A/{name}", str(library)])
    run(["codesign", "--force", "--sign", "-", str(library)])
    isolated_app = runtime / "Praison-Kdenlive-Live.app"
    if not isolated_app.exists():
        # APFS clone avoids storing a second full copy of the media frameworks.
        run(["cp", "-cR", str(application), str(isolated_app)])
        run(["codesign", "--force", "--deep", "--sign", "-", str(isolated_app)])
    return isolated_app, library
