# cli-es baseline revision

The `cli-es` task now freezes CLI source `aa792aeef2fe271b357e57231d7bd7222a6aa905` (English README SHA256 `1f01504d378d4f8ade00c26d9486f4e3a365e3ad6f5c7acd06a58b5ccde840c3`). Relative to the previous snapshot, exactly two lines changed: the quick start uses `agentswarm tasks --task post_parent --json`, and the `tasks` table lists `--task ID`. The separate `post --mission SLUG` option remains valid. Translate the current snapshot and add the exact navigation; all original English-byte, fence, structure, URL and language checks still apply.

After installing the prerequisites documented in the check README, activate the environment and run from this directory in the immutable checker checkout selected by the task:

```bash
source ../.venv/bin/activate
BOUNTY_TASK=cli-es python -m pytest -q test_readme_translation.py
```

Set `BOUNTY_REPO` to the absolute path of the target branch. Old issue pins still select their historical snapshots: neither `d08ffef5bf796a1099f85d452fabbc0f848849ae` nor `5cd882709a68263f3f09e16f1a9471da0e0f9a99` changes retroactively. This revision alone does not change any published task criteria, reward notice period or reviewer runtime binding.

The compatibility fixture is the inert Spanish README from public CLI PR8 at `0e3f8f116aa50b3ec8382d69d640b040ec7b8494`. Tests apply only the two command corrections to it in memory. Automated language checks supplement independent meaning review; they do not certify every translated inline option or sentence.
