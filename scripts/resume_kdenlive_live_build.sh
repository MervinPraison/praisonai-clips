#!/usr/bin/env sh
set -eu
SHORTS_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SHORTS_BUILD="$SHORTS_ROOT/.flatpak-builder/build/kdenlive-live-1"
SHORTS_APP="$SHORTS_ROOT/tools/runtime/kdenlive-live-flatpak"
flatpak build --bind-mount="/run/build/kdenlive-live=$SHORTS_BUILD" \
 --build-dir=/run/build/kdenlive-live/_flatpak_build "$SHORTS_APP" \
 cmake -S /run/build/kdenlive-live -B /run/build/kdenlive-live/_flatpak_build \
 '-DCMAKE_CXX_FLAGS_RELEASE=-O1 -DNDEBUG' '-DCMAKE_C_FLAGS_RELEASE=-O1 -DNDEBUG' \
 -DCMAKE_CXX_FLAGS=-pipe -DCMAKE_C_FLAGS=-pipe
flatpak build --bind-mount="/run/build/kdenlive-live=$SHORTS_BUILD" \
 --build-dir=/run/build/kdenlive-live/_flatpak_build "$SHORTS_APP" \
 cmake --build /run/build/kdenlive-live/_flatpak_build --parallel 4
flatpak build --bind-mount="/run/build/kdenlive-live=$SHORTS_BUILD" \
 --build-dir=/run/build/kdenlive-live/_flatpak_build "$SHORTS_APP" \
 cmake --install /run/build/kdenlive-live/_flatpak_build
