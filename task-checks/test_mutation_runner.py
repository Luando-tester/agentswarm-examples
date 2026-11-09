"""Offline mutation-runner regression tests; run inside Docker --network none."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from mutation_runner import main


class MutationRunnerTests(unittest.TestCase):
    def run_fixture(self, summary='# tests 1', clean_witness=None):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source = folder / 'reference'
            source.mkdir()
            (source / 'implementation.py').write_text('value = 1\n')
            mutants = folder / 'mutants'
            mutants.mkdir()
            for index in range(5):
                recipe = {
                    'defect': f'changes value for mutant {index}',
                    'witness': f'defect witness {index}',
                    'changes': [{'file': 'implementation.py', 'old': 'value = 1', 'new': 'value = 2'}],
                }
                (mutants / f'mutant-{index}.json').write_text(json.dumps(recipe))
            # Exercise real subprocess output and real planting, without a service or network.
            checker = folder / 'checker.py'
            checker.write_text(
                'import os\nfrom pathlib import Path\nimport sys\n'
                f'print({summary!r})\n'
                "clean = (Path(os.environ['BOUNTY_REPO']) / 'implementation.py').read_text() == 'value = 1\\n'\n"
                f'clean_witness = {clean_witness!r}\n'
                'if clean and clean_witness is not None:\n    print(clean_witness)\n'
                'if not clean:\n    print("\\n".join(f"defect witness {i}" for i in range(5)))\n'
                'sys.exit(0 if clean else 1)\n'
            )
            output = io.StringIO()
            with patch.object(sys, 'argv', ['run_mutants.py', str(source)]), redirect_stdout(output):
                code = main(folder, [sys.executable, str(checker)], ['implementation.py'])
            return code, output.getvalue()

    def test_tap_summary_counts_rejections(self):
        code, output = self.run_fixture()
        self.assertEqual(code, 0, output)
        self.assertIn('rejects 5 of 5 known-bad; reference passes', output)

    def test_node_spec_summary_counts_rejections(self):
        code, output = self.run_fixture(summary='ℹ tests 1')
        self.assertEqual(code, 0, output)
        self.assertIn('rejects 5 of 5 known-bad; reference passes', output)

    def test_pytest_summary_counts_rejections(self):
        code, output = self.run_fixture(summary='1 passed in 0.01s')
        self.assertEqual(code, 0, output)
        self.assertIn('rejects 5 of 5 known-bad; reference passes', output)

    def test_clean_reference_witness_stops_before_any_mutant(self):
        # Also check the last recipe, so validation must cover every witness up front.
        for index in (0, 4):
            with self.subTest(index=index):
                code, output = self.run_fixture(clean_witness=f'defect witness {index}')
                self.assertEqual(code, 1, output)
                self.assertIn(f'BLIND: witness mutant-{index} matches the clean reference', output)
                self.assertNotIn('MUTANT ', output)
                self.assertNotIn('REJECTED:', output)
                self.assertNotIn('known-bad; reference passes', output)

    def test_uncollected_reference_is_still_blind(self):
        code, output = self.run_fixture(summary='no tests collected')
        self.assertEqual(code, 1, output)
        self.assertIn('BLIND: reference fails; no mutation score is valid', output)
        self.assertNotIn('MUTANT ', output)


if __name__ == '__main__':
    unittest.main()
