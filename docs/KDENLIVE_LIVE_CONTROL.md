# Live Kdenlive control

The optional live adapter targets a running scripting-enabled Kdenlive window. It is separate from the stable FFmpeg renderer and the existing headless Kdenlive source-cut exporter.

## Native Mac live bridge

macOS has a separate live control path, implemented in
`scripts/mac-live/`. It loads a small local Qt bridge into an isolated APFS copy
of the installed Kdenlive app. The installed `/Applications/kdenlive.app` is
untouched. The local copy is ad-hoc signed so it can load the bridge. This is our
custom bridge, not an official stock Kdenlive scripting API.

The bridge accepts authenticated requests on an ephemeral IPv4 loopback port.
Its random bearer token is stored only in the ignored runtime directory, in a
mode-0600 connection file. Requests execute native Qt methods on the editor's
main thread. The MCP client binds to the launched process and the document's
native undo-stack identity, and refuses edits after a different document opens.
It does not send mouse, keyboard, or accessibility events and does not edit XML
behind an open document.

Requirements: macOS, Xcode command-line tools, Qt 6 development headers matching
the app's Qt major/minor version, and this project's optional `live` dependency.
The tested app is Kdenlive 26.08.2 with Qt 6.11, using Homebrew Qt 6.11.2 headers.

```sh
uv pip install --python .venv/bin/python 'mcp>=1,<2'
scripts/kdenlive-mac-live build
scripts/kdenlive-mac-live launch /absolute/path/to/project-copy.kdenlive
scripts/kdenlive-mac-live status
scripts/kdenlive-mac-live mcp
```

The last command serves standard stdio MCP. Seven tools are exposed:
`get_live_status`, `select_sequence`, `seek`, `set_framing`, `undo`, `redo`, and
`save_project`. Use IDs returned by the current live status; IDs change between
editor sessions. `set_framing` requires exactly one native Transform effect on
the selected video clip, and changes its rectangle in project pixels. On the
current 1080×1920 project, `(0,0,1080,1920)` is the original full-frame fit and
`(-135,-240,1350,2400)` is a centered 125% zoom. A simple command-line client is
also available:

```sh
scripts/kdenlive-mac-live call select_sequence '{"index":1}'
scripts/kdenlive-mac-live call seek '{"frame":644}'
scripts/kdenlive-mac-live call transform '{"clip_id":12,"x":-135,"y":-240,"width":1350,"height":2400}'
scripts/kdenlive-mac-live call undo
scripts/kdenlive-mac-live call save
```

The default runtime is `data/mac-live/`. Keep the isolated editor closed when
rebuilding the bridge. This integration depends on Kdenlive's
internal Qt method signatures; revalidate after editor updates. It is deliberately
limited to the tested framing workflow, rather than claiming general editor API
coverage. The clean-source sequence has no editable captions; the reference
sequence preserves the exact captioned MP4.

### Actual Mac validation, 28 October 2026

`scripts/test_kdenlive_mac_live.py` used a real MCP client against the running
native editor and passed all seven exposed tools. It selected the source
sequence, sought to frame 644, applied a 125% Transform, saved using the native
Save action, and verified the actual saved effect values. Native undo restored
the original rectangle; redo restored the zoom. Native MLT rendered each saved
state: zoom differed from baseline, undo matched baseline exactly, and redo
matched zoom exactly. A final undo/save restored the baseline and left the
document clean. The normalized source SHA-256 was unchanged.

Evidence is in `data/mac-live/live-validation.json`, `mcp-test.log`, and the
baseline/zoom125/undo/redo/restored PNG frames. Select an explicit disposable
project under `data/mac-live/` when running the test:

```sh
.venv/bin/python scripts/test_kdenlive_mac_live.py --project data/mac-live/live-review.kdenlive
```

The named project must already exist and match the running bridge connection.
The test requires the demo's source sequence and original framing, and makes
real temporary edits. Use only a disposable copy prepared for this test.

The initial generated source Transform had been attached to a media chain,
which Kdenlive did not expose as an editable timeline effect. The live demo was
prepared with a native timeline-entry Transform instead, and the stale chain
filter was removed from the demo copy before launch. Subsequent tested edits
were made through the running editor.

## Sources and isolation

- Editor fork: https://github.com/D-Ogi/kdenlive at `8312f5ef03a5bd1fbb177d0e1696948bcb1b9b3a`.
- Python API: https://github.com/D-Ogi/kdenlive-api at `d1f87baa127d2950d89b923f7a0206defb124073`.
- MCP server: https://github.com/D-Ogi/mcp-kdenlive at `afe585143f631fa00f62a1d22207d85df06a0d74`.
- Isolated KDE SDK and platform: user-scoped Flatpak 6.10; exact commits in data/kdenlive-live-test/versions.json.
- No system Kdenlive replacement or root package installation. The stock Debian toolchain lacks the required Qt/KDE/MLT versions. User-scoped SDK/runtime downloads and build files use several GB of disk.

The experimental build uses `scripts/kdenlive-live-flatpak.json`. MLT 7.36.0, Imath 3.1.12, OpenTimelineIO 0.18.1 and KDDockWidgets 2.4.0 are built into its private prefix. Optional Rubber Band, SoX and vid.stab modules are disabled; their features are not part of this test. Kdenlive is compiled at O1 without debug information to reduce memory use during the experimental build.

## Local patches

`scripts/patches/kdenlive-live-build-fixes.patch` removes an identical appended block of 45 C++ method implementations, an extra scene-detection implementation, and duplicate method declarations. It also fixes mixed designated/positional QuickJS aggregate initializers rejected by GCC in C++20 mode. The unpatched fork does not compile on this toolchain.

`scripts/patches/kdenlive-live-api-instance.patch` adds explicit `KDENLIVE_DBUS_SERVICE` selection and preserves boolean/integer/float types in the command-line D-Bus parser. In particular, a failed native edit returning boolean false must not become the truthy string "false".

These patches are separate from the earlier headless server's Linux X11 patch. Do not apply them to the existing headless MCP checkout.

## Build and launch

On Debian Linux with Flatpak available, `scripts/setup_kdenlive_live.sh` installs the user-scoped SDK/runtime, fetches the pinned sources, applies the saved patches once, and unpacks local build helpers. Then:

```sh
scripts/build_kdenlive_live.sh
```

For the existing retained build tree, `scripts/resume_kdenlive_live_build.sh` resumes compilation and installation without rebuilding completed dependencies. Build logs are in data/kdenlive-live-test/.

Once built:

```sh
scripts/kdenlive-live /absolute/path/to/a/project-copy.kdenlive
.venv/bin/python scripts/kdenlive_live_status.py
scripts/kdenlive-live-mcp
```

The final command is a standard stdio MCP server, not a user-interactive terminal. It exposes 177 registered tools. The status helper uses read-only D-Bus introspection and selects only an instance with the live scripting methods. The endpoint is persisted in data/kdenlive-live-test/service.txt and passed explicitly to the API. If multiple scripting-enabled instances exist, select KDENLIVE_DBUS_SERVICE explicitly rather than guessing.

Flatpak gives the editor access to this project root, display/audio, and its own exact D-Bus names. Older service names use PID 2 in this build's namespace. The installed KDE Frameworks also uses names under org.kde.kdenlive.kdbus-…, so the launcher permits ownership of org.kde.kdenlive.*. It does not expose the whole session bus. The API's temporary preview path is inside the shared project root so returned images are accessible both inside and outside the runtime.

## Validation boundary

The initial upstream Python suite returned 85 passed, 5 failed and 3 skipped. The failures include a stale D-Bus interface expectation, missing marker methods in the test mock, and code-quality checks inconsistent with the current code. The complete failures are preserved in data/kdenlive-live-test/upstream-tests.log; they have not been silently marked passing.

Three application regression tests verify scalar types, video-track booleans and explicit instance targeting without connecting to an editor. These do not prove the live GUI works.

`scripts/test_kdenlive_live.py` is an actual MCP integration test. It refuses to edit any document other than data/kdenlive-live-test/live-demo.kdenlive, then checks the live clip counts across split, undo and redo, saves that copy, renders a frame, captures the application window, and verifies the main source SHA is unchanged. Its live-validation.json and screenshots are the evidence for successful live operation, when present. Do not equate the 177-tool inventory with 177 validated operations.

Existing GUI changes are not automatically imported into the Shorts application's EDL or review manifest. Final deliveries still use the established FFmpeg captions, source/output mapping and acceptance workflow until live export parity is verified.

This independent PraisonAI Clips repository uses the internal src/praisonai_shorts_studio/ package. Its primary CLI is praisonai-clips.

## Actual live result, 28 October 2026

The patched editor compiled, installed and launched successfully. A standard MCP client discovered all 177 tools and exercised project settings, media import, clip insertion, seeking, live splits, grouping, native undo/redo, save, composited frame rendering and window capture. The first video test verified one clip → two clips → undo to one → redo to two. The linked A/V test then verified aligned video and audio splits at 5 and 10 seconds, undo/redo on both tracks, 1044 total frames at 30fps, and an empty unused video track. Source media was unchanged.

The running native project is data/kdenlive-live-test/live-demo.kdenlive. Evidence remains local: live-validation.json, linked-av-validation.json, before.jpg, after_split.jpg, linked-av-final.jpg and the saved native project. The final frame and screenshots were visually inspected and contain the real video and its burned-in captions, not an INVALID placeholder.

This successful test uses the accepted rendered MP4, imported into a fresh native project. Captions are already burned in; they are not editable subtitle text in this demo. Opening the other headless backend's exported .kdenlive project crashed this experimental build, so cross-backend project import is not approved. The new_project MCP tool can report failure for a successfully created untitled project because the native method returns an empty filename; actual project metadata must be verified. No claim is made that all 177 tools work.

A further patch, scripts/patches/kdenlive-live-mcp-summary.patch, sorts timeline clips by position before detecting overlaps; the original tool incorrectly reported transitions when native clip IDs were not in time order. A regression test covers this case. Four focused adapter tests now cover local fixes; the initial upstream 85-pass/5-fail/3-skip result remains recorded honestly.

To reproduce safely, launch a fresh editor, create a new native project, set it to 1080×1920 at 30fps, import an accepted MP4, insert its video and audio on separate tracks, group them and save a new copy. Use audio-only bin prefix A<bin_id> when inserting audio to avoid creating an additional mirrored video layer. Then select the verified service and use the guarded MCP client. The demo integration test requires a fresh copy starting with one video clip and refuses other documents.
