from __future__ import annotations

import subprocess
import sys


def main() -> int:
    subprocess.check_call(["uv", "pip", "install", "--python", sys.executable, "yfinance", "pandas"])
    import yfinance as yf
    for tk in ["CE", "4471.T"]:
        print(f"=== {tk} ===")
        df = yf.download(tk, start="2015-12-01", end="2026-01-05", interval="1d", auto_adjust=False, progress=False, threads=False)
        print("rows", len(df))
        print(df.head(2).to_string())
        print(df.tail(2).to_string())
        if len(df) < 1000:
            raise RuntimeError(f"too few rows for {tk}: {len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
