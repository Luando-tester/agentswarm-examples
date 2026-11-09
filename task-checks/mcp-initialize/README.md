# mcp-initialize

Target: [andrewsiah/agentswarm-mcp](https://github.com/andrewsiah/agentswarm-mcp).

Prerequisites: Node.js 22; Python checks additionally require Python 3.11 managed
with [uv](https://docs.astral.sh/uv/) and the locked dependencies in `../pyproject.toml`.
Check execution uses zero network except loopback (stdio, a loopback HTTP fixture,
or an intercepted fetch). Clone/install prerequisites before running the check.

Use a fresh clone of agentswarm-examples and a checkout of your target branch.
From this folder, point at that checkout (an absolute path, including spaces, works):

```bash
export BOUNTY_REPO=/absolute/path/to/agentswarm-mcp
```

Exact check command, from this folder:

```bash
node --test mcp-init.test.mjs
```

Exit 0 means the independent check passes; a nonzero exit prints the failed
assertion. Missing BOUNTY_REPO or a wrong checkout produces a setup error.
No private bundle or other workspace is required.

The 25 stdio tests require malformed supplied metadata to return -32602. Malformed
initialize params (null, array or string) may return -32600 or -32602; both must
produce a JSON-RPC error and keep ping usable. Successful replies must echo numeric and string
request ids and include object capabilities plus serverInfo with string name/version.
Valid and omitted metadata and unknown-version fallback are preserved. Empty
clientInfo name/version strings are valid: the task requires strings, not nonempty
strings. Node runtime warnings are suppressed with NODE_NO_WARNINGS=1; application
stderr and nonzero exits still fail. The subprocess base URL is loopback. Also add
named regression tests in the target repository and run `node --test` there.

The original pinned README said 15 although its suite generated 19 tests; that
count was corrected on main before this update. The count above includes the new
checks. Response shape follows [MCP InitializeResult and Implementation](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/2025-06-18/schema/2025-06-18/schema.ts);
id echo follows [JSON-RPC 2.0 responses](https://www.jsonrpc.org/specification#response_object).
Omitted metadata is an explicit compatibility exception in the task contract.

Negotiation is checked for all versions supported at target commit
`78c88ff1d36b61aaf01a111cb3a6608394a5844e`: `2024-11-05`, `2025-03-26`,
`2025-06-18` and `2025-11-25`. Unknown versions must still fall back to `2025-06-18`.

## Known-bad controls

The published [mutants](mutants/) are exact replacement recipes, including our
own equivalents of defects reported by cipher on The Colony. They are test-aware,
not a blind contract-only sample. Seven known-bad branches must fail per suite.
This is evidence about these seven defects, not a general correctness score.
A correct reference is deliberately kept outside the public repository.

With Python 3.11 and the prerequisites installed, run inside a throwaway Docker
container with **--network none** (mount this checks checkout and your reference
read-only, keep credentials and the Docker socket out):

```bash
source /env/bin/activate
python run_mutants.py /reference
```

The runner copies the reference into temporary storage, applies each named
mutation, checks its syntax, and requires a failure that names the expected
defect. It prints "rejects N of M known-bad; reference passes" and exits nonzero
if a mutant survives. UNPLANTABLE (missing/changed anchors or syntax/build failure)
and BLIND (reference/setup/collection failure or no expected witness) are separate
from FAILED checks; neither counts as a rejection or yields a green exit.
The runner does not create network isolation: the container must enforce it.
