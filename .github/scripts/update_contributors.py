"""Regenerate the README contributors table from GitHub and contributors.json."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
DEVICES = ROOT / ".github" / "contributors.json"
REPO = os.environ.get("GITHUB_REPOSITORY", "krasnoukhov/homeassistant-tesy")
START = "<!-- contributors:start -->"
END = "<!-- contributors:end -->"


def fetch_contributors() -> list[dict]:
    """Commit authors, most commits first, without bots."""
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    result, page = [], 1
    while True:
        url = (
            f"https://api.github.com/repos/{REPO}/contributors?per_page=100&page={page}"
        )
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
            batch = json.load(r)
        if not batch:
            return [c for c in result if c["type"] != "Bot"]
        result += batch
        page += 1


def describe(device: dict) -> str:
    model = device.get("model", "Unknown model")
    if device.get("id"):
        model += f" ({device['id']})"
    return f"{model}, {device['api']} API"


def render(contributors: list[dict], devices: dict[str, list[dict]]) -> str:
    # People in contributors.json who have no commits yet go last
    logins = [c["login"] for c in contributors]
    logins += sorted(set(devices) - set(logins), key=str.lower)
    rows = ["| Contributor | Devices |", "|---|---|"]
    for login in logins:
        avatar = (
            f'<img src="https://github.com/{login}.png?size=40" width="20" height="20">'
        )
        listed = "<br>".join(describe(d) for d in devices.get(login, [])) or "—"
        rows.append(f"| {avatar} [@{login}](https://github.com/{login}) | {listed} |")
    return "\n".join(rows)


def main() -> int:
    devices = json.loads(DEVICES.read_text())
    table = render(fetch_contributors(), devices)
    text = README.read_text()
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        sys.exit(f"{START} / {END} markers not found in README.md")
    updated = pattern.sub(lambda _: f"{START}\n{table}\n{END}", text)
    if updated != text:
        README.write_text(updated)
        print("README.md updated")
    else:
        print("README.md already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
