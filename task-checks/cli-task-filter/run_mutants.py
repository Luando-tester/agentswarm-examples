"""Usage (inside an offline container): python run_mutants.py /private/reference."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mutation_runner import main

if __name__ == '__main__':
    sys.exit(main(Path(__file__).parent, [sys.executable, '-m', 'pytest', '-q', 'test_cli_task_filter.py'], ['node/bin/agentswarm.js', 'python/src/agentswarm_cli/__main__.py']))
