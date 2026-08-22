from __future__ import annotations

import base64
import contextlib
import gzip
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

OLD_COMMIT = "f7c0294ad29cc2f82e264cb48e3f737a55f17f19"
RAW_URL = (
    "https://raw.githubusercontent.com/myu65/myuux/"
    + OLD_COMMIT
    + "/backend/scripts/codex_checks.py"
)


def main() -> int:
    subprocess.check_call(
        ["uv", "pip", "install", "--python", sys.executable, "yfinance", "pandas", "numpy"]
    )
    wrapper = urllib.request.urlopen(RAW_URL, timeout=30).read().decode("utf-8")
    match = re.search(r'payload="([A-Za-z0-9+/=]+)"', wrapper)
    if not match:
        raise RuntimeError("could not extract known-good embedded analysis payload")
    src = gzip.decompress(base64.b64decode(match.group(1))).decode("utf-8")
    src = src.replace("full=w.reindex(JP,fill_value=0)", "full=w.reindex(list(JP),fill_value=0)")
    src = src.replace("W[dn]=ws['PCA_SUB'].reindex(JP,fill_value=0); S[dn]=sub.reindex(JP)",
                      "W[dn]=ws['PCA_SUB'].reindex(list(JP),fill_value=0); S[dn]=sub.reindex(list(JP))")
    src = src.replace("y=p['oc'].loc[d,JP]", "y=p['oc'].loc[d,list(JP)]")
    src = src.replace("p['oc'].loc[W.index,JP]", "p['oc'].loc[W.index,list(JP)]")
    src = src.replace("p['close'][JP]*p['volume'][JP]",
                      "p['close'][list(JP)]*p['volume'][list(JP)]")

    started = time.time()
    out_path = Path("/tmp/chem_analysis_stdout.txt")
    ns = {"__name__": "__main__"}
    with out_path.open("w", encoding="utf-8") as fh, contextlib.redirect_stdout(fh):
        exec(compile(src, "chem_full_yf_patched.py", "exec"), ns, ns)

    print("=== ANALYSIS_STDOUT_TAIL ===")
    text = out_path.read_text(encoding="utf-8", errors="replace")
    print(text[-60000:])
    print("=== END_ANALYSIS_STDOUT_TAIL ===")

    print("=== RESULT_FILES ===")
    seen = set()
    for root in (Path.cwd(), Path("/tmp")):
        for suffix in ("*.json", "*.csv", "*.txt"):
            for p in root.rglob(suffix):
                try:
                    rp = p.resolve()
                    st = p.stat()
                except OSError:
                    continue
                if rp in seen or st.st_mtime < started - 2 or p == out_path:
                    continue
                seen.add(rp)
                print(f"FILE {rp} SIZE {st.st_size}")
                if st.st_size <= 1000000:
                    try:
                        body = p.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    print(body)
                    print(f"END_FILE {rp}")
    print("=== END_RESULT_FILES ===")

    print("=== RESULT_GLOBALS ===")
    for name in sorted(ns):
        if name.startswith("__"):
            continue
        value = ns[name]
        typename = type(value).__name__
        shape = getattr(value, "shape", None)
        if shape is not None:
            print(f"GLOBAL {name} TYPE {typename} SHAPE {shape}")
        elif isinstance(value, (str, int, float, bool, type(None))):
            print(f"GLOBAL {name} TYPE {typename} VALUE {value!r}")
        elif isinstance(value, (dict, list, tuple)):
            print(f"GLOBAL {name} TYPE {typename} LEN {len(value)}")
            try:
                dumped = json.dumps(value, ensure_ascii=False, default=str)
                if len(dumped) <= 30000:
                    print(dumped)
            except Exception:
                pass
    print("=== END_RESULT_GLOBALS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
