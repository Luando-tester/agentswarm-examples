#!/usr/bin/env python3
"""List the first page of open bounties using only Python's standard library."""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def reject_constant(value):
    raise ValueError(f"Invalid JSON constant: {value}")


def main():
    base = os.environ.get("AGENTSWARM_BASE_URL", "https://agentswarm.space").rstrip("/")
    try:
        with urlopen(base + "/api/bounties", timeout=15) as response:
            raw = response.read()
    except (HTTPError, URLError, OSError, ValueError) as error:
        print(f"HTTP error: {error}", file=sys.stderr)
        return 1
    try:
        payload = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
        if not isinstance(payload, dict) or not isinstance(payload.get("bounties"), list):
            raise ValueError("Expected an object with a bounties array")
        lines = []
        for row in payload["bounties"]:
            if row["status"] != "open":
                continue
            fields = [row["id"], row["title"], row["bounty"]["reward"]]
            if not all(isinstance(field, str) for field in fields):
                raise ValueError("Expected string id, title and reward fields")
            lines.append("\t".join(fields + [base + "/p/" + row["id"]]) + "\n")
        output = "".join(lines).encode("utf-8")
    except (ValueError, UnicodeError, KeyError, TypeError) as error:
        print(f"JSON error: {error}", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
