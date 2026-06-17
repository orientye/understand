#!/usr/bin/env python3
"""
check-urls.py — Check HTTP/HTTPS URLs in .asc documentation files.

Usage:
  python tools/check-urls.py path/to/file.asc
  python tools/check-urls.py path/to/file.asc --timeout 15 --concurrency 10
  python tools/check-urls.py path/to/file.asc --verbose
"""

import argparse
import concurrent.futures
import io
import re
import sys
import time
import urllib.error
import urllib.request
from typing import List, Tuple

# URLs that are definitely not externally accessible
_SKIP_PATTERNS = re.compile(
    r"https?://(?:"
    r"localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|"
    r"\[::1\]|example\.(?:com|org|net)"
    r")(?::\d+)?(?:/|$)",
    re.IGNORECASE,
)

_URL_RE = re.compile(r"https?://[^\s\"'\]\)><,]+")


def extract_urls(text: str) -> List[str]:
    """Extract unique HTTP/HTTPS URLs from text, skipping local/internal hosts."""
    seen = set()
    urls = []
    for m in _URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;:!?")
        if url in seen:
            continue
        if _SKIP_PATTERNS.match(url):
            continue
        seen.add(url)
        urls.append(url)
    return urls


def check_url(url: str, timeout: int) -> Tuple[str, str, int, str]:
    """
    Check a single URL.
    Returns (url, status_category, status_code_or_error, detail_message).
    status_category: "ok" | "redirect" | "dead"
    """
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                code = resp.status
                if 200 <= code < 300:
                    return (url, "ok", code, "")
                elif 300 <= code < 400:
                    return (url, "redirect", code, "")
                else:
                    continue
        except urllib.error.HTTPError as e:
            code = e.code
            if method == "HEAD" and code in (400, 403, 405):
                continue
            elif code == 429:
                return (url, "dead", code, "rate limited (429)")
            else:
                return (url, "dead", code, urllib.request.HTTPError.__name__)
        except urllib.error.URLError as e:
            reason = str(e.reason) if e.reason else "unknown error"
            if method == "HEAD":
                continue
            return (url, "dead", 0, reason)
        except Exception as e:
            if method == "HEAD":
                continue
            return (url, "dead", 0, type(e).__name__)
    return (url, "dead", 0, "HEAD and GET both failed")


def run_check(filepath: str, timeout: int, concurrency: int, verbose: bool) -> int:
    """Run URL check on a file. Returns exit code (0=all good, 1=dead links)."""
    start = time.time()

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    urls = extract_urls(text)
    total = len(urls)

    if total == 0:
        print("No external HTTP/HTTPS URLs found.")
        return 0

    print("=" * 80)
    print(f"URL Check Report: {filepath}")
    print("=" * 80)

    ok_list: List[str] = []
    redirect_list: List[str] = []
    dead_list: List[Tuple[str, int, str]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        fut_map = {executor.submit(check_url, url, timeout): url for url in urls}
        for fut in concurrent.futures.as_completed(fut_map):
            url = fut_map[fut]
            try:
                _url, cat, code, detail = fut.result()
            except Exception as e:
                dead_list.append((url, 0, str(e)))
                continue
            if cat == "ok":
                ok_list.append(url)
            elif cat == "redirect":
                redirect_list.append(url + f" ({code})")
            else:
                dead_list.append((url, code, detail))

    elapsed = time.time() - start

    print()
    if ok_list:
        ok_count = len(ok_list)
        print(f"[OK] 有效 ({ok_count})")
        if verbose:
            for u in ok_list:
                print(f"  {u}")

    if redirect_list:
        redir_count = len(redirect_list)
        print(f"[WARN] 重定向 ({redir_count})")
        for u in redirect_list:
            print(f"  {u}")

    if dead_list:
        dead_count = len(dead_list)
        print(f"[FAIL] 失效 ({dead_count})")
        for url, code, detail in dead_list:
            if code:
                print(f"  [{code}] {url}")
            else:
                print(f"  [{detail}] {url}")

    print()
    print("─" * 80)
    print(f"总计: {total} 个 URL"
          f" | [OK] 有效 {len(ok_list)}"
          f" | [WARN] 重定向 {len(redirect_list)}"
          f" | [FAIL] 失效 {len(dead_list)}")
    print(f"    耗时: {elapsed:.1f}s")
    print("=" * 80)

    return 1 if dead_list else 0


def main() -> None:
    # Force UTF-8 output on Windows (GBK cannot encode many Unicode chars)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    parser = argparse.ArgumentParser(description="Check HTTP/HTTPS URLs in .asc documentation files.")
    parser.add_argument("path", help="Path to the .asc file")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent requests (default: 5)")
    parser.add_argument("--verbose", action="store_true", help="Show all URLs including successful ones")
    args = parser.parse_args()

    exit_code = run_check(args.path, args.timeout, args.concurrency, args.verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
