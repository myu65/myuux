from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parts = sorted((repo_root / "chatgpt_tmp_chem").glob("p*.b64"))
    if len(parts) != 6:
        raise RuntimeError(f"expected 6 runner parts, got {len(parts)}")
    payload = "".join(p.read_text(encoding="utf-8").strip() for p in parts)
    runner = Path("/tmp/chem_leadlag_full.py")
    runner.write_bytes(base64.b64decode(payload))
    subprocess.check_call([
        "uv", "pip", "install", "--python", sys.executable,
        "numpy", "pandas", "requests",
    ])
    subprocess.check_call([sys.executable, str(runner)], cwd=repo_root)
    bundle = repo_root / "chatgpt_chem_results" / "out" / "analysis_bundle.json"
    print("===CHATGPT_ANALYSIS_BUNDLE_BEGIN===")
    print(bundle.read_text(encoding="utf-8"))
    print("===CHATGPT_ANALYSIS_BUNDLE_END===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
