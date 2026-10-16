#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
cd "$FURY_REPO/desktop"
[ "$(uname -s)" = Linux ] || { echo "Linux host required" >&2; exit 1; }
version="$(sed -n '/^\[workspace.package\]/,/^\[/p' "$FURY_REPO/Cargo.toml" | sed -n 's/^version = "\([^"]*\)"/\1/p')"
# System-installed cores rely on Debian's versioned dependency, not a user-tree stamp.
node --input-type=module - "$version" <<'JS'
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const config = JSON.parse(readFileSync('src-tauri/tauri.linux.conf.json', 'utf8'));
assert(config.bundle.linux.deb.depends.includes(`fury-core (= ${process.argv[2]}+linux1)`),
  'Update the Linux core dependency to match the workspace version before building');
JS
command -v cargo >/dev/null
pkg-config --exists gtk+-3.0 webkit2gtk-4.1 libsecret-1
npm ci
npm run app:build -- --config src-tauri/tauri.linux.conf.json --bundles deb
mkdir -p "$FURY_REPO/dist-linux"
cp "$FURY_REPO"/target/release/bundle/deb/*.deb "$FURY_REPO/dist-linux/"
(cd "$FURY_REPO/dist-linux" && sha256sum Fury_*.deb > SHA256SUMS-shell)
