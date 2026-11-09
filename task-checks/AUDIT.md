# Quick audit, 2026-11-09

All candidate code ran in Docker with no external network. The MCP, CLI and remote
checks ran in containers using `--network none`. The trusted pinned example checker
orchestrated its own separate offline fixture/build/runtime containers as documented
in that suite (runtime joins the offline fixture namespace). No branch code ran on
the host. Source recipes, commands, full logs and exits are retained in `audit/`,
`prepare-audit.cjs`, `run-audit.sh`, `run-examples-audit.sh`, `run-f5-audit.sh` and
`evidence/audit-*` outside the published repository.

| Suite / checks pin | Control | Deliberate defects tested | Survivors |
| --- | --- | --- | --- |
| mcp-write-body / d1ae21a4 | 16/16 pass | accept blank bodies; trim valid body bytes | 0 of 2 |
| cli-response-body / d1ae21a4 | 6/6 pass | Node body-read error exits 1; Python body-read error exits 1 | 0 of 2 |
| remote-bounty-context / 5a78333c | 2/2 pass | drop underTaskId; drop funders | 0 of 2 |
| code-example-list-tasks TypeScript / 5a78333c | pass | print closed tasks; ignore HTTP status | 0 of 2 |
| code-example-list-tasks Python / f5c019f0 | pass | print closed tasks; HTTP error exits 0 | 0 of 2 |
| code-example-list-tasks Ruby / f5c019f0 | pass | print closed tasks; HTTP error exits 0 | 0 of 2 |

These are small, test-aware samples: zero survivors is not evidence of complete
coverage. Go and Rust were not re-audited in this cycle. No fixes were needed in
these suites. Each rejection reached a behavioral assertion after successful
setup/build; it was not counted from a syntax/setup failure.

References for the first two suites are local copies of current product mains with
the minimal required fix. Remote main at 8e2c6a144d4acb74646993a841e9bf1fd7fb0442
already includes the accepted projection fix. Example references were copied from
local prior check-development artifacts (gfi113 TypeScript; gfi143 Python/Ruby).
No reference was pushed to a product repository or added to agentswarm-examples.

A displayed authorization-header redaction initially looked like a literal test
bug. Byte checks confirmed the actual expected dummy header is correct and no
literal redaction marker exists. The correct CLI reference passed. No change was
made based on the display artifact.
