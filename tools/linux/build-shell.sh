#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
cd "$FURY_REPO/desktop"
[ "$(uname -s)" = Linux ] || { echo "Linux host required" >&2; exit 1; }
command -v cargo >/dev/null
pkg-config --exists gtk+-3.0 webkit2gtk-4.1 libsecret-1
npm ci
npm run app:build -- --config src-tauri/tauri.linux.conf.json --bundles deb
mkdir -p "$FURY_REPO/dist-linux"
cp "$FURY_REPO"/target/release/bundle/deb/*.deb "$FURY_REPO/dist-linux/"
(cd "$FURY_REPO/dist-linux" && sha256sum Fury_*.deb > SHA256SUMS-shell)
