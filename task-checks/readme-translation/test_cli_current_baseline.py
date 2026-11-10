"""Offline compatibility proof for the cli-es baseline revision; fixture is data only."""
import hashlib
import json
from pathlib import Path

import pytest

from translation_check import check_translation, load_task

HERE = Path(__file__).parent
OLD = (HERE / 'baselines/factory-cli-93643b1d.md').read_bytes()
# Public Primuez PR8 head 0e3f8f116aa50b3ec8382d69d640b040ec7b8494,
# README.es.md: copied as inert text, never imported or executed.
SPANISH = (HERE / 'fixtures/cli-es-pr8-0e3f8f11.txt').read_text()
QUICK_OLD = 'agentswarm tasks --mission first-budget --json'
QUICK_NEW = 'agentswarm tasks --task post_parent --json'


def corrected_spanish():
    return SPANISH.replace(QUICK_OLD, QUICK_NEW, 1).replace(
        '| `tasks` | Tareas abiertas, las más recientes primero. `--mission SLUG`',
        '| `tasks` | Tareas abiertas, las más recientes primero. `--task ID`', 1)


def candidate(tmp_path, baseline=None, translated=None):
    config, current = load_task('cli-es')
    first, rest = (current if baseline is None else baseline).decode().split('\n', 1)
    (tmp_path / 'README.md').write_text(first + '\n\n' + config['navigation'] + '\n' + rest)
    (tmp_path / 'README.es.md').write_text(corrected_spanish() if translated is None else translated)
    return config, current


def test_current_baseline_identity_and_exact_two_line_revision():
    config, current = load_task('cli-es')
    assert config['commit'] == 'aa792aeef2fe271b357e57231d7bd7222a6aa905'
    assert hashlib.sha256(current).hexdigest() == '1f01504d378d4f8ade00c26d9486f4e3a365e3ad6f5c7acd06a58b5ccde840c3'
    assert hashlib.sha1(b'blob ' + str(len(current)).encode() + b'\0' + current).hexdigest() == '6b90389696458cafad2aba3ef6f5d9a61f0a741d'
    assert hashlib.sha256(OLD).hexdigest() == '661579237b35643c3451dc74f80d2c70d75a08d87aa957998d7a691a40100d2a'
    expected = OLD.decode().replace(QUICK_OLD, QUICK_NEW, 1).replace(
        '| `tasks` | Open tasks, newest first. `--mission SLUG`',
        '| `tasks` | Open tasks, newest first. `--task ID`', 1)
    assert current.decode() == expected
    assert len([1 for old, new in zip(OLD.splitlines(), current.splitlines()) if old != new]) == 2
    mappings = json.loads((HERE / 'baseline_blobs.json').read_text())
    assert mappings['baselines/factory-cli-93643b1d.md'] == '98369940b8c5411d17169e394c7f2f60ce4e6c3e'
    # Every other CLI language retains its original snapshot.
    for name, row in json.loads((HERE / 'tasks.json').read_text()).items():
        if name.startswith('cli-') and name != 'cli-es':
            assert row['sha256'] == hashlib.sha256(OLD).hexdigest()


def test_corrected_english_and_two_spanish_fixes_pass(tmp_path):
    config, current = candidate(tmp_path)
    assert corrected_spanish().count('--mission SLUG') == 1  # post still uses mission
    check_translation(tmp_path, config, current)


def test_old_pr_head_fails_new_pin(tmp_path):
    config, current = candidate(tmp_path, OLD, SPANISH)
    with pytest.raises(AssertionError, match='English README changed'):
        check_translation(tmp_path, config, current)


def test_old_spanish_fence_fails_even_with_current_english(tmp_path):
    config, current = candidate(tmp_path, translated=SPANISH)
    with pytest.raises(AssertionError, match='Fenced blocks must be byte-identical'):
        check_translation(tmp_path, config, current)


def test_corrected_candidate_fails_historical_baseline(tmp_path):
    config, _ = candidate(tmp_path)
    with pytest.raises(AssertionError, match='English README changed'):
        check_translation(tmp_path, config, OLD)


def test_main_without_translation_fails(tmp_path):
    config, current = load_task('cli-es')
    (tmp_path / 'README.md').write_bytes(current)
    with pytest.raises(AssertionError, match='Missing README.es.md'):
        check_translation(tmp_path, config, current)


@pytest.mark.parametrize('before,after', [
    (QUICK_NEW, 'agentswarm tasks --task other --json'),
    ('`post` | Creates a post.', '`post` | Changes a post.'),
    ('--mission SLUG', '--task ID'),
    ('https://agentswarm.space', 'https://example.org'),
])
def test_unrelated_english_changes_fail(tmp_path, before, after):
    config, current = candidate(tmp_path)
    path = tmp_path / 'README.md'
    original = path.read_text()
    assert before in original
    path.write_text(original.replace(before, after, 1))
    with pytest.raises(AssertionError, match='English README changed'):
        check_translation(tmp_path, config, current)


@pytest.mark.parametrize('before,after,witness', [
    ('agentswarm login', 'agentswarm login --json', 'Fenced blocks'),
    (QUICK_NEW, QUICK_OLD, 'Fenced blocks'),
    ('https://agentswarm.space/skill.md', 'https://example.org/skill.md', 'Missing URLs'),
    (next(p for p in SPANISH.split('\n\n') if p.startswith('La clave solo se envía')), '', 'Preserve every paragraph'),
    (next(p for p in SPANISH.split('\n\n') if p.startswith('La CLI nunca actúa')), '', 'Preserve every paragraph'),
    ('## La clave', '## La clave\n\n<script>oculto</script>', 'Raw HTML'),
    ('## La clave', '## La clave\n\n[oculto]: texto oculto', 'Reference definitions'),
])
def test_spanish_command_url_caveat_and_hiding_mutations_fail(tmp_path, before, after, witness):
    original = corrected_spanish()
    assert before in original
    config, current = candidate(tmp_path, translated=original.replace(before, after, 1))
    with pytest.raises(AssertionError, match=witness):
        check_translation(tmp_path, config, current)
