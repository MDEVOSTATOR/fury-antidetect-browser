#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Package only runtime files, never object files, build paths or a proprietary CDM.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
build_dir="${1:-$FURY_REPO/core/src/out/linux-x64.noindex}"
version="$(sed -n '/^\[workspace.package\]/,/^\[/p' "$FURY_REPO/Cargo.toml" | sed -n 's/^version = "\([^"]*\)"/\1/p')"
[ -n "$version" ] || { echo "Cannot determine Fury version" >&2; exit 1; }
"$build_dir/chrome" --version
stage="$(mktemp -d "$FURY_REPO/.build/core-package.XXXXXX")"
trap 'rm -rf "$stage"' EXIT
mkdir "$stage/Fury"
for name in chrome chrome_crashpad_handler icudtl.dat resources.pak chrome_100_percent.pak chrome_200_percent.pak locales; do
  [ -e "$build_dir/$name" ] || { echo "Missing runtime resource: $name" >&2; exit 1; }
  cp -a "$build_dir/$name" "$stage/Fury/"
done
cp "$build_dir/chrome_sandbox" "$stage/Fury/chrome-sandbox"
chmod 755 "$stage/Fury/chrome-sandbox"
shopt -s nullglob
for path in "$build_dir"/*.so* "$build_dir"/v8_context_snapshot.bin "$build_dir"/vk_swiftshader_icd.json; do
  [ ! -e "$path" ] || cp -a "$path" "$stage/Fury/"
done
shopt -u nullglob
find "$stage/Fury" -type d -exec chmod 755 {} +
find "$stage/Fury" -type f -exec chmod 644 {} +
chmod 755 "$stage/Fury/chrome" "$stage/Fury/chrome_crashpad_handler" "$stage/Fury/chrome-sandbox"
install -m 644 "$FURY_REPO/core/src/LICENSE" "$stage/Fury/LICENSE.chromium"
install -m 644 "$FURY_REPO/core/patches/LICENSE" "$stage/Fury/LICENSE.fury-patches"
install -m 644 "$FURY_REPO/NOTICE" "$stage/Fury/NOTICE.fury"
# Chromium's generated credit page also remains available through chrome://credits.
if [ -f "$build_dir/gen/components/resources/about_credits.html" ]; then
  install -m 644 "$build_dir/gen/components/resources/about_credits.html" "$stage/Fury/LICENSES.chromium.html"
fi
mkdir -p "$FURY_REPO/dist-linux"
archive="fury-core-$version-linux-x64.tar.xz"
tar -cJf "$FURY_REPO/dist-linux/$archive" -C "$stage" Fury
(cd "$FURY_REPO/dist-linux" && sha256sum "$archive" > "$archive.sha256")
echo "$FURY_REPO/dist-linux/$archive"

# A root-owned installation lets Chromium use its setuid sandbox on Ubuntu
# hosts where AppArmor denies user namespaces to arbitrary downloaded binaries.
# Never setuid a helper inside a user-writable build or profile directory.
debroot="$stage/deb"
mkdir -p "$debroot/usr/lib/fury-core" "$debroot/DEBIAN"
cp -a "$stage/Fury/." "$debroot/usr/lib/fury-core/"
mkdir -p "$debroot/usr/share/doc/fury-core"
cat "$stage/Fury/LICENSE.chromium" "$stage/Fury/LICENSE.fury-patches" > "$debroot/usr/share/doc/fury-core/copyright"
chmod 644 "$debroot/usr/share/doc/fury-core/copyright"
install -m 644 "$FURY_REPO/NOTICE" "$debroot/usr/share/doc/fury-core/NOTICE"
cat > "$debroot/DEBIAN/control" <<EOF
Package: fury-core
Version: $version+linux1
Architecture: amd64
Maintainer: Fury Linux port <noreply@localhost>
Section: web
Priority: optional
Depends: libc6, libnss3, libnspr4, libatk1.0-0t64, libatk-bridge2.0-0t64, libcups2t64, libdbus-1-3, libdrm2, libexpat1, libgbm1, libglib2.0-0t64, libgtk-3-0t64, libpango-1.0-0, libasound2t64, libx11-6, libxcb1, libxcomposite1, libxdamage1, libxext6, libxfixes3, libxkbcommon0, libxrandr2
Description: Fury patched Chromium core for Ubuntu 24.04 x86_64
 Browser core with a root-owned Chromium sandbox helper.
EOF
cat > "$debroot/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -eu
if [ "${1:-}" = configure ]; then
  chown root:root /usr/lib/fury-core/chrome-sandbox
  chmod 4755 /usr/lib/fury-core/chrome-sandbox
fi
EOF
chmod 755 "$debroot/DEBIAN/postinst"
find "$debroot" -type d -exec chmod 755 {} +
debname="fury-core_${version}+linux1_amd64.deb"
dpkg-deb --build --root-owner-group "$debroot" "$FURY_REPO/dist-linux/$debname"
(cd "$FURY_REPO/dist-linux" && sha256sum "$debname" > "$debname.sha256")
