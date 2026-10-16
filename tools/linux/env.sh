#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Source this to use a project-local Rust installation without changing login files.
# A build must not inherit realtime scheduling from an interactive tmux session.
if [ "$(uname -s)" = Linux ] && [ -x /usr/bin/chrt ]; then
  /usr/bin/chrt --other --pid 0 "$$"
  FURY_INHERITED_NICE="$(/usr/bin/ps -o ni= -p "$$")"
  if [ "$FURY_INHERITED_NICE" -lt 0 ]; then
    /usr/bin/renice --priority 0 --pid "$$" >/dev/null
  fi
  unset FURY_INHERITED_NICE
fi
FURY_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ -x "$FURY_REPO/.build/cargo/bin/rustup" ]; then
  export CARGO_HOME="$FURY_REPO/.build/cargo"
  export RUSTUP_HOME="$FURY_REPO/.build/rustup"
  export PATH="$CARGO_HOME/bin:$PATH"
fi
# Limit compiler concurrency on a workstation shared with other projects.
export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-6}"
# Some workstations have a shell helper called cc ahead of the C compiler.
export CC="${FURY_CC:-/usr/bin/gcc}"
export CXX="${FURY_CXX:-/usr/bin/g++}"
export CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER="$CC"
