#!/usr/bin/env sh
# Optional Linux setup. Downloads private build dependencies, never replaces system Kdenlive.
set -eu
SHORTS_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$SHORTS_ROOT"
command -v flatpak >/dev/null
command -v git >/dev/null
flatpak --user remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak --user install -y --noninteractive flathub org.kde.Sdk//6.10 org.kde.Platform//6.10
ensure_source() {
  SHORTS_URL=$1
  SHORTS_DEST=$2
  SHORTS_COMMIT=$3
  if [ ! -d "$SHORTS_DEST" ]; then
    git clone --no-checkout --depth 1 "$SHORTS_URL" "$SHORTS_DEST"
    git -C "$SHORTS_DEST" fetch --depth 1 origin "$SHORTS_COMMIT"
    git -C "$SHORTS_DEST" checkout --detach "$SHORTS_COMMIT"
  fi
  if [ "$(git -C "$SHORTS_DEST" rev-parse HEAD)" != "$SHORTS_COMMIT" ]; then
    echo "Preserving a different existing checkout at $SHORTS_DEST; expected $SHORTS_COMMIT" >&2
    exit 1
  fi
}
ensure_source https://github.com/D-Ogi/kdenlive.git tools/kdenlive-live-src 8312f5ef03a5bd1fbb177d0e1696948bcb1b9b3a
ensure_source https://github.com/D-Ogi/kdenlive-api.git tools/kdenlive-live-api d1f87baa127d2950d89b923f7a0206defb124073
ensure_source https://github.com/D-Ogi/mcp-kdenlive.git tools/kdenlive-live-mcp afe585143f631fa00f62a1d22207d85df06a0d74
apply_once() {
  SHORTS_SOURCE=$1
  SHORTS_PATCH=$2
  if git -C "$SHORTS_SOURCE" apply --reverse --check "$SHORTS_PATCH" 2>/dev/null; then
    return
  fi
  git -C "$SHORTS_SOURCE" apply --check "$SHORTS_PATCH"
  git -C "$SHORTS_SOURCE" apply "$SHORTS_PATCH"
}
apply_once tools/kdenlive-live-src "$SHORTS_ROOT/tools/kdenlive-live-build-fixes.patch"
apply_once tools/kdenlive-live-api "$SHORTS_ROOT/tools/kdenlive-live-api-instance.patch"
apply_once tools/kdenlive-live-mcp "$SHORTS_ROOT/tools/kdenlive-live-mcp-summary.patch"
if [ ! -e tools/kdenlive-api ]; then ln -s kdenlive-live-api tools/kdenlive-api; fi
if [ ! -x tools/runtime/flatpak-builder-packages/root/usr/bin/flatpak-builder ]; then
  command -v apt-get >/dev/null
  command -v dpkg-deb >/dev/null
  mkdir -p tools/runtime/flatpak-builder-packages/root
  (
    cd tools/runtime/flatpak-builder-packages
    apt-get download flatpak-builder elfutils debugedit
    for archive in ./*.deb; do dpkg-deb -x "$archive" root; done
  )
fi
.venv/bin/pip install -e '.[studio,dev,live]'
printf 'Setup complete. Build with scripts/build_kdenlive_live.sh\n'
