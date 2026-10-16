#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo"
if [ -f .build/linux-core.error ]; then cat .build/linux-core.error; fi
if [ -f .build/linux-core.phase ]; then
  printf 'Core phase: '; cat .build/linux-core.phase
else
  echo 'Core phase: initial dependency fetch (see chromium-fetch.log)'
fi
progress=core/src/out/linux-x64.noindex/build-progress.log
if [ -f "$progress" ]; then tail -3 "$progress"; fi
if [ -f .build/logs/core-build.log ]; then
  tail -3 .build/logs/core-build.log
elif [ -f .build/logs/chromium-fetch.log ]; then
  tail -3 .build/logs/chromium-fetch.log
fi
find dist-linux -maxdepth 1 -type f -name '*.deb' -printf '%f %s bytes\n'
