"""Run only inside a throwaway container with --network none; never on the host."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def main(suite, command, required_files):
    folder = Path(suite).resolve()
    source = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else None
    if source is None or not all((source / f).is_file() for f in required_files):
        print('UNPLANTABLE: pass an existing known-good reference checkout', flush=True)
        return 1
    mutants = sorted((folder / 'mutants').glob('*.json'))
    if len(mutants) < 5:
        print('BLIND: expected at least five published mutant recipes', flush=True)
        return 1

    def check(repo):
        try:
            result = subprocess.run(command, cwd=folder, env=dict(os.environ, BOUNTY_REPO=str(repo)),
                                    capture_output=True, text=True, timeout=120)
            output = result.stdout + result.stderr
            print(output, end='', flush=True)
            # A checker that fails before collecting tests cannot reject a mutant.
            collected = bool(re.search(r'(?:#|ℹ) tests \d+|\d+ (?:passed|failed)', output))
            blind = not collected or bool(re.search(r'ERROR collecting|SyntaxError|ModuleNotFoundError', output))
            return result.returncode, output, blind
        except (OSError, subprocess.TimeoutExpired) as error:
            print('BLIND: ' + type(error).__name__, flush=True)
            return None, '', True

    code, reference_output, blind = check(source)
    if code != 0 or blind:
        print('BLIND: reference fails; no mutation score is valid', flush=True)
        return 1
    recipes = [(recipe_file, json.loads(recipe_file.read_text())) for recipe_file in mutants]
    for recipe_file, recipe in recipes:
        if re.search(recipe['witness'], reference_output):
            print(f'BLIND: witness {recipe_file.stem} matches the clean reference', flush=True)
            return 1
    rejected = 0
    for recipe_file, recipe in recipes:
        print('\nMUTANT ' + recipe_file.stem + ': ' + recipe['defect'], flush=True)
        with tempfile.TemporaryDirectory(prefix='task-mutant-') as temp:
            repo = Path(temp) / 'repo'
            shutil.copytree(source, repo, ignore=shutil.ignore_patterns('.git', '.venv', 'node_modules', '__pycache__'))
            try:
                for change in recipe['changes']:
                    target = repo / change['file']
                    if not target.resolve().is_relative_to(repo):
                        raise ValueError('mutation path escapes checkout')
                    if 'source' in change:
                        target.write_text((folder / 'mutants' / change['source']).read_text())
                    else:
                        text = target.read_text()
                        if text.count(change['old']) != 1 or change['old'] == change['new']:
                            raise ValueError('mutation anchor absent, ambiguous or unchanged')
                        target.write_text(text.replace(change['old'], change['new']))
                for relative in {c['file'] for c in recipe['changes']}:
                    target = repo / relative
                    syntax = ['node', '--check', str(target)] if target.suffix == '.js' else [sys.executable, '-m', 'py_compile', str(target)]
                    subprocess.run(syntax, check=True, capture_output=True, timeout=10)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                print('UNPLANTABLE: ' + type(error).__name__, flush=True)
                continue
            code, output, blind = check(repo)
            if blind or code is None:
                print('BLIND: check could not measure this mutant', flush=True)
            elif code == 0:
                print('SURVIVED: known-bad branch passed', flush=True)
            elif not re.search(recipe['witness'], output):
                print('BLIND: failed without the expected defect witness', flush=True)
            else:
                rejected += 1
                print('REJECTED: FAILED check at the named defect witness', flush=True)
    print(f'rejects {rejected} of {len(mutants)} known-bad; reference passes', flush=True)
    return 0 if rejected == len(mutants) else 1
