#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Resume the Linux core build, refusing to discard any source edits.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
cd "$FURY_REPO"
mkdir -p .build/logs dist-linux
exec 9> .build/linux-core-build.lock
flock -n 9 || { echo "A Linux core build is already running" >&2; exit 1; }
phase() { printf '%s\n' "$1" | tee .build/linux-core.phase; }
trap 'status=$?; printf "Build failed with exit %s; inspect core-build.log\n" "$status" > .build/linux-core.error; exit "$status"' ERR
rm -f .build/linux-core.error
patch_stamp=core/src/.fury-linux-patches.sha256
series_hash="$(cat core/CHROMIUM_VERSION core/patches/series core/patches/*.patch | sha256sum | cut -d' ' -f1)"
if [ -f "$patch_stamp" ] && [ "$(cat "$patch_stamp")" != "$series_hash" ]; then
  echo "Patch series changed; rebase the existing Chromium tree explicitly" >&2
  exit 1
fi
if [ "${FURY_SKIP_FETCH:-0}" != 1 ] && [ ! -f "$patch_stamp" ]; then
  phase fetch
  core/build/fetch.sh "$(cat core/CHROMIUM_VERSION)"
fi
phase patches
if [ -f "$patch_stamp" ]; then
  [ "$(cat "$patch_stamp")" = "$series_hash" ] || {
    echo "Patch series changed; rebase the existing Chromium tree explicitly" >&2
    exit 1
  }
else
  [ -z "$(git -C core/src status --porcelain --untracked-files=no --ignore-submodules=all)" ] || {
    echo "Chromium has source edits; refusing to overwrite them" >&2
    exit 1
  }
  core/build/apply.sh
  printf '%s\n' "$series_hash" > "$patch_stamp"
fi
phase compile
nice -n 10 env J="${J:-8}" core/build/build.sh linux-x64
phase package
tools/linux/package-core.sh
phase built-needs-browser-validation
