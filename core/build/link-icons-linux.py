#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate Linux browser icons from Fury's existing artwork, without mtime churn."""
from io import BytesIO
from pathlib import Path
import re

from PIL import Image

repo = Path(__file__).resolve().parents[2]
theme = repo / "core/src/chrome/app/theme"
master = Image.open(repo / "assets/icon-browser.png").convert("RGBA")
directories = [theme / "chromium", theme / "chromium/linux"]
directories += list(theme.glob("default_*_percent/chromium"))
updated = 0
for directory in directories:
    for path in directory.glob("product_logo_*.png"):
        if not re.fullmatch(r"product_logo_\d+", path.stem):
            continue
        with Image.open(path) as old:
            size = old.size
        data = BytesIO()
        master.resize(size, Image.Resampling.LANCZOS).save(data, format="PNG")
        if path.read_bytes() != data.getvalue():
            temporary = path.with_suffix(".fury-tmp")
            temporary.write_bytes(data.getvalue())
            temporary.replace(path)
            updated += 1
print(f"Linux Fury icons: {updated} files updated")
