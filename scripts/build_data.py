# -*- coding: utf-8 -*-
"""Build data/issues.json from the HelloGitHub repository.

Usage:
    python scripts/build_data.py [--out data/issues.json] [--source auto|tarball|raw]

Download strategies (tried in order unless --source is given):
  1. tarball : download https://codeload.github.com/521xueweihan/HelloGitHub/tar.gz/refs/heads/master
               (one request, fast), extract content/HelloGitHubNNN.md in memory.
               Only the top-level content/ directory is used; content/en/
               (English translations) is ignored.
  2. raw     : list issue ids via the GitHub git-trees API (1 request), then
               download each content/HelloGitHubNNN.md from raw.githubusercontent.com
               concurrently; if the API is unavailable, probe sequential ids.

Only the Python standard library is used.
"""

import argparse
import io
import json
import os
import re
import socket
import sys
import tarfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parser as hg_parser  # noqa: E402

REPO = "521xueweihan/HelloGitHub"
BRANCH = "master"
TARBALL_URL = "https://codeload.github.com/%s/tar.gz/refs/heads/%s" % (REPO, BRANCH)
RAW_BASE = "https://raw.githubusercontent.com/%s/%s/content/HelloGitHub" % (REPO, BRANCH)
TREE_URL = "https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (REPO, BRANCH)
MAX_ISSUE = 999
UA = "codex-hellogithub-build"
TARBALL_FILE_RE = re.compile(r"^[^/]+/content/HelloGitHub(\d+)\.md$")


def _force_ipv4():
    """Prefer IPv4; codeload/raw can fail on some networks when IPv6 is tried first."""
    orig = socket.getaddrinfo

    def v4(host, port, *args, **kwargs):
        res = orig(host, port, *args, **kwargs)
        return [r for r in res if r[0] == socket.AF_INET] or res

    socket.getaddrinfo = v4


_force_ipv4()


def _fetch(url, timeout=90, tries=4):
    """GET a URL with retries (raw/codeload are flaky on some networks)."""
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise last


def fetch_from_tarball():
    """Return {issue_id: markdown_text} via the codeload tarball."""
    data = _fetch(TARBALL_URL)
    archive = tarfile.open(fileobj=io.BytesIO(data), mode="r:gz")
    files = {}
    for member in archive.getmembers():
        if not member.isfile():
            continue
        match = TARBALL_FILE_RE.match(member.name.replace("\\", "/"))
        if match:
            raw = archive.extractfile(member).read()
            files[int(match.group(1))] = raw.decode("utf-8", errors="replace")
    return files


def _fetch_raw(issue_id):
    """Fetch one issue file from raw.githubusercontent; 404 -> (issue_id, None)."""
    url = "%s%02d.md" % (RAW_BASE, issue_id)
    try:
        return issue_id, _fetch(url, timeout=60)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return issue_id, None
        raise


def _list_ids_via_api():
    """Return sorted issue ids listed in the repo tree (1 API request)."""
    data = json.loads(_fetch(TREE_URL, timeout=60).decode("utf-8"))
    ids = []
    for item in data.get("tree", []):
        match = re.match(r"content/HelloGitHub(\d+)\.md$", item.get("path", ""))
        if match:
            ids.append(int(match.group(1)))
    return sorted(set(ids))


def _probe_ids():
    """Fallback: probe sequential issue numbers until several 404s in a row."""
    ids = []
    misses = 0
    n = 1
    while n <= MAX_ISSUE:
        try:
            _, text = _fetch_raw(n)
        except Exception:  # noqa: BLE001
            break
        if text is None:
            misses += 1
            if misses >= 5:
                break
        else:
            misses = 0
            ids.append(n)
        n += 1
    return ids


def fetch_from_raw():
    """Return {issue_id: markdown_text} via API listing + concurrent raw downloads."""
    try:
        ids = _list_ids_via_api()
    except Exception:  # noqa: BLE001
        ids = _probe_ids()
    if not ids:
        raise RuntimeError("could not determine HelloGitHub issue list")

    files = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for issue_id, text in pool.map(_fetch_raw, ids):
            if text is not None:
                files[issue_id] = text
    return files


def fetch_issues(source):
    if source == "tarball":
        return fetch_from_tarball()
    if source == "raw":
        return fetch_from_raw()

    errors = []
    for name, fn in (("tarball", fetch_from_tarball), ("raw", fetch_from_raw)):
        try:
            print("fetching issues via %s ..." % name)
            return fn()
        except Exception as exc:  # noqa: BLE001
            errors.append("%s: %r" % (name, exc))
            print("  %s failed, trying next source" % name, file=sys.stderr)
    raise RuntimeError("all download sources failed: %s" % "; ".join(errors))


def build_data(files):
    """Parse all issues and return the final JSON-serializable structure."""
    issues = [hg_parser.parse_issue(files[iid], iid) for iid in sorted(files)]
    return {
        "updatedAt": datetime.now().strftime("%Y-%m-%d"),
        "source": "https://github.com/%s" % REPO,
        "issues": issues,
    }


def main(argv=None):
    argp = argparse.ArgumentParser(description="Build data/issues.json from HelloGitHub")
    argp.add_argument("--out", default=os.path.join("data", "issues.json"))
    argp.add_argument("--source", choices=("auto", "tarball", "raw"), default="auto")
    args = argp.parse_args(argv)

    files = fetch_issues(args.source)
    print("downloaded %d issues" % len(files))
    data = build_data(files)

    out_path = args.out
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    total = sum(len(c["projects"]) for issue in data["issues"] for c in issue["categories"])
    print("wrote %s: %d issues, %d projects" % (out_path, len(data["issues"]), total))
    print("latest issue: %d" % max(issue["id"] for issue in data["issues"]))


if __name__ == "__main__":
    main()