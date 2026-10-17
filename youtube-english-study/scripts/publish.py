#!/usr/bin/env python3
"""Upload a finished 精读本 page to the GitHub repo (via gh, no local clone needed).

usage: python3 publish.py <page.html> [--repo owner/name] [--dir pages]

Creates or updates <dir>/<filename> on the default branch and prints the file's URL.
Requires the gh CLI, logged in (`gh auth status`).
"""
import base64
import json
import os
import subprocess
import sys
import urllib.parse

REPO = "Jalensuggs/youtube-english-study"
DIR = "pages"


def gh(args, data=None, check=True):
    p = subprocess.run(["gh", *args], capture_output=True, text=True,
                       input=json.dumps(data) if data is not None else None)
    if check and p.returncode != 0:
        print("ERROR: gh failed:\n" + (p.stderr or p.stdout).strip()[-1200:], file=sys.stderr)
        sys.exit(1)
    return p


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    page = args[0]
    repo = args[args.index("--repo") + 1] if "--repo" in args else REPO
    sub = args[args.index("--dir") + 1] if "--dir" in args else DIR
    if not os.path.isfile(page):
        sys.exit(f"ERROR: no such file: {page}")

    if subprocess.run(["which", "gh"], capture_output=True).returncode != 0:
        sys.exit("ERROR: the gh CLI is not installed — skip publishing and tell the user.")
    if gh(["auth", "status"], check=False).returncode != 0:
        sys.exit("ERROR: gh is not logged in (`gh auth login`) — skip publishing and tell the user.")

    name = os.path.basename(page)
    path = f"{sub}/{name}"
    api_path = "/".join(urllib.parse.quote(p) for p in path.split("/"))
    endpoint = f"repos/{repo}/contents/{api_path}"

    cur = gh(["api", endpoint, "--jq", ".sha"], check=False)
    sha = cur.stdout.strip() if cur.returncode == 0 else None
    body = {
        "message": ("Update " if sha else "Add ") + name,
        "content": base64.b64encode(open(page, "rb").read()).decode(),
    }
    if sha:
        body["sha"] = sha
    r = gh(["api", "-X", "PUT", endpoint, "--input", "-"], data=body)
    url = json.loads(r.stdout)["content"]["html_url"]
    print(("updated " if sha else "added ") + path)
    print(url)


main()
