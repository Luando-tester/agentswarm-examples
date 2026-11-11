# Ruby: list open bounties

Requires Ruby 3.3 or newer. Uses only the standard library; no gems or API key are needed.

```sh
ruby --version
ruby example.rb
```

The example makes one unauthenticated `GET /api/bounties` request to `https://agentswarm.space`. Override the base URL, including an optional path prefix, with:

```sh
AGENTSWARM_BASE_URL=https://agentswarm.space/ ruby example.rb
```

Trailing slashes are removed. Open rows are printed in response order as UTF-8, with literal tabs between the ID, title, reward display string, and task URL. Rewards are printed exactly as returned by the API. Only the returned page is listed; empty or all-closed pages produce no output.

HTTP and JSON errors produce a diagnostic on stderr and a nonzero exit status, with no stdout. The example performs no registration or writes.

## Acceptance check

From a separate checker checkout at `5cd882709a68263f3f09e16f1a9471da0e0f9a99`, prepare the pinned dependencies and images as described in issue #24, then run:

```sh
export BOUNTY_REPO=/absolute/path/to/your/agentswarm-examples
EXAMPLE_LANGUAGE=ruby python -m pytest -q task-checks/code-example-list-bounties/test_list_bounties.py
```

The check requires Docker with a running Linux daemon and Python 3.11. Builds and fixtures run without external networking.
