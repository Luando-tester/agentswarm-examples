# cli-task-filter

Target: [andrewsiah/agentswarm-cli](https://github.com/andrewsiah/agentswarm-cli).

Prerequisites: Node.js 22; Python checks additionally require Python 3.11 managed
with [uv](https://docs.astral.sh/uv/) and the locked dependencies in `../pyproject.toml`.
Check execution uses zero network except loopback (stdio, a loopback HTTP fixture,
or an intercepted fetch). Clone/install prerequisites before running the check.

Use a fresh clone of agentswarm-examples and a checkout of your target branch.
From this folder, point at that checkout (an absolute path, including spaces, works):

```bash
export BOUNTY_REPO=/absolute/path/to/agentswarm-cli
```

For this Python check, prepare the shared environment from this folder:

```bash
uv sync --project .. --locked --python 3.11
source ../.venv/bin/activate
```

The first dependency install may need a package index; use a populated uv cache
and `uv sync --offline --project .. --locked --python 3.11` for offline setup.
The check itself has no external network dependency.

Exact check command, from this folder:

```bash
python -m pytest -q test_cli_task_filter.py
```

Exit 0 means the independent check passes; a nonzero exit prints the failed
assertion. Missing BOUNTY_REPO or a wrong checkout produces a setup error.
No private bundle or other workspace is required.

The 16 tests run both binaries against a local HTTP fixture. Tasks --task must
send type=task&task=post_parent and preserve the actual non-empty response items
and nextCursor. The fixture selects task types and parents from mixed feed data;
existing client status filtering (open/accepted, or closed too with --all) is
preserved. Plain tasks, other filters, empty matches and an explicit --before
follow-up are covered. Paging is manual: one invocation requests one page, not
an automatic drain of nextCursor. Retired --mission must exit 2 before HTTP;
task help must name --task. No target package installation is required: Python
uses the checkout through PYTHONPATH. Also update README examples and both
repository test suites, and run those suites.

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
