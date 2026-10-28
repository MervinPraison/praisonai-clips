#!/usr/bin/env sh
# Build only the isolated experimental editor; never replaces system Kdenlive.
set -eu
SHORTS_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$SHORTS_ROOT"
export PATH="$SHORTS_ROOT/tools/runtime/flatpak-builder-packages/root/usr/bin:$PATH"
exec "$SHORTS_ROOT/tools/runtime/flatpak-builder-packages/root/usr/bin/flatpak-builder" \
  --user --jobs=4 --build-only --force-clean \
  "$SHORTS_ROOT/tools/runtime/kdenlive-live-flatpak" \
  "$SHORTS_ROOT/scripts/kdenlive-live-flatpak.json"
