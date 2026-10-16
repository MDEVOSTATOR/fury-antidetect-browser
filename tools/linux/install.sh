#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Install the matching Linux packages after verifying their local checksums.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
packages="${1:-$FURY_REPO/dist-linux}"
cd "$packages"
shopt -s nullglob
shells=(Fury_*_amd64.deb)
cores=(fury-core_*_amd64.deb)
[ "${#shells[@]}" = 1 ] && [ "${#cores[@]}" = 1 ] || {
  echo "Expected one desktop .deb and one core .deb in $packages" >&2
  exit 1
}
sha256sum -c SHA256SUMS-shell
sha256sum -c "${cores[0]}.sha256"
sudo apt-get install "$(pwd)/${shells[0]}" "$(pwd)/${cores[0]}"
