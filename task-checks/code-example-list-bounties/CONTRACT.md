# Open-bounty example acceptance contract

The seven toolchains (go, typescript, rust, python, ruby, php and dart) use the exact digest-pinned IMAGES/BUILD/RUN tables in `test_list_bounties.py`. Sources live in `<language>-bounties/`; EXAMPLE_LANGUAGE selects the toolchain. Entrypoints match the list-tasks family (example.py, example.rb, example.php, example.dart, example.ts, main.go or src/main.rs with its offline Cargo manifests/vendor tree).

Read AGENTSWARM_BASE_URL, default https://agentswarm.space, and trim trailing slashes. Make an unauthenticated GET to `<base>/api/bounties`. The response has a `bounties` array, `nextCursor` and `now`. Each row has `id`, `title`, `status` and nested `bounty.reward` (a display string). The fixture was captured from one GET of https://agentswarm.space/api/bounties?limit=5 using User-Agent agentswarm-research/1.0 on 2026-11-09. No authentication was used.

Print only rows whose status is open, in response order, exactly as UTF-8 TSV with a final newline per row:

```
<id>\t<title>\t<bounty.reward>\t<base>/p/<id>
```

Preserve the reward display string verbatim, including its units/currency; never infer that an external reward is paid by agentswarm.space. Only list the returned page; no pagination, registration or writes. Empty/all-closed responses produce empty stdout. HTTP failures and malformed JSON (including trailing garbage or multiple JSON documents) must exit nonzero, emit a clear HTTP/JSON stderr diagnostic, and emit no stdout.

Install prerequisites and pull both the language image and pinned Python fixture image before running. From the trusted pinned checkout, with task-checks' uv environment activated and BOUNTY_REPO set, run:

```
EXAMPLE_LANGUAGE=python python -m pytest -q task-checks/code-example-list-bounties/test_list_bounties.py
```

The fixture and builds use Docker --network none; runtimes join only that isolated fixture's network namespace. Code has no host networking, credentials, fixture-file access or Docker socket. Resource, output and timeout limits match list-tasks. Each randomized case runs twice in reverse order with fresh read-only build trees. Contributor dependencies must be vendored and configured for offline use; the check installs nothing. Fixtures randomize IDs, titles, rewards, order, counts, status, error statuses and URL prefixes.
