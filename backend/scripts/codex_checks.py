from __future__ import annotations

import urllib.request


def main() -> int:
    urls = [
        "https://static.stooq.com/db/h/d_us_txt.zip",
        "https://static.stooq.com/db/h/d_jp_txt.zip",
        "https://static.stooq.com/db/h/d_world_txt.zip",
    ]
    for url in urls:
        req = urllib.request.Request(
            url,
            headers={"Range": "bytes=0-1023", "User-Agent": "Mozilla/5.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                chunk = resp.read(1024)
                print(
                    "STOOQ_TEST",
                    url,
                    resp.status,
                    resp.headers.get("Content-Length"),
                    resp.headers.get("Content-Type"),
                    resp.headers.get("Content-Range"),
                    len(chunk),
                    chunk[:16].hex(),
                    flush=True,
                )
        except Exception as exc:
            print("STOOQ_TEST_ERROR", url, repr(exc), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
