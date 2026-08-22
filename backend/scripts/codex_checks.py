from __future__ import annotations

import base64
import gzip
import re
import subprocess
import sys
import urllib.request

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
    ns = {"__name__": "__main__"}
    exec(compile(src, "chem_full_yf_patched.py", "exec"), ns, ns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
