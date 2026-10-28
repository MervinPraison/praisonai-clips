# Experimental live Kdenlive control

The optional live adapter targets a running scripting-enabled Kdenlive window. It is separate from the stable FFmpeg renderer and the existing headless Kdenlive source-cut exporter.

## Sources and isolation

- Editor fork: https://github.com/D-Ogi/kdenlive at `8312f5ef03a5bd1fbb177d0e1696948bcb1b9b3a`.
- Python API: https://github.com/D-Ogi/kdenlive-api at `d1f87baa127d2950d89b923f7a0206defb124073`.
- MCP server: https://github.com/D-Ogi/mcp-kdenlive at `afe585143f631fa00f62a1d22207d85df06a0d74`.
- Isolated KDE SDK and platform: user-scoped Flatpak 6.10; exact commits in data/kdenlive-live-test/versions.json.
- No system Kdenlive replacement or root package installation. The stock Debian toolchain lacks the required Qt/KDE/MLT versions. User-scoped SDK/runtime downloads and build files use several GB of disk.

The experimental build uses `scripts/kdenlive-live-flatpak.json`. MLT 7.36.0, Imath 3.1.12, OpenTimelineIO 0.18.1 and KDDockWidgets 2.4.0 are built into its private prefix. Optional Rubber Band, SoX and vid.stab modules are disabled; their features are not part of this test. Kdenlive is compiled at O1 without debug information to reduce memory use during the experimental build.

## Local patches

`tools/kdenlive-live-build-fixes.patch` removes an identical appended block of 45 C++ method implementations, an extra scene-detection implementation, and duplicate method declarations. It also fixes mixed designated/positional QuickJS aggregate initializers rejected by GCC in C++20 mode. The unpatched fork does not compile on this toolchain.

`tools/kdenlive-live-api-instance.patch` adds explicit `KDENLIVE_DBUS_SERVICE` selection and preserves boolean/integer/float types in the command-line D-Bus parser. In particular, a failed native edit returning boolean false must not become the truthy string "false".

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

Flatpak gives the editor access to this project root, display/audio, and its own exact D-Bus names. In this build's PID namespace the editor runs as PID 2, hence the exact org.kde.kdenlive-2 permission. The API's temporary preview path is inside the shared project root so returned images are accessible both inside and outside the runtime.

## Validation boundary

The initial upstream Python suite returned 85 passed, 5 failed and 3 skipped. The failures include a stale D-Bus interface expectation, missing marker methods in the test mock, and code-quality checks inconsistent with the current code. The complete failures are preserved in data/kdenlive-live-test/upstream-tests.log; they have not been silently marked passing.

Three application regression tests verify scalar types, video-track booleans and explicit instance targeting without connecting to an editor. These do not prove the live GUI works.

`scripts/test_kdenlive_live.py` is an actual MCP integration test. It refuses to edit any document other than data/kdenlive-live-test/live-demo.kdenlive, then checks the live clip counts across split, undo and redo, saves that copy, renders a frame, captures the application window, and verifies the main source SHA is unchanged. Its live-validation.json and screenshots are the evidence for successful live operation, when present. Do not equate the 177-tool inventory with 177 validated operations.

Existing GUI changes are not automatically imported into the Shorts application's EDL or review manifest. Final deliveries still use the established FFmpeg captions, source/output mapping and acceptance workflow until live export parity is verified.

This independent PraisonAI Clips repository uses the internal src/praisonai_shorts_studio/ package. Its primary CLI is praisonai-clips. The existing praisonai-shorts repository remains unchanged; its fetched reference is kept only in the ignored .upstream-reference/ directory locally.
