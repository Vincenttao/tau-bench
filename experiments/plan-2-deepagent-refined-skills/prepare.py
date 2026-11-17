"""Prepare this experiment only; does not execute models or runtimes."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'shared/python'))
from experiment_plan import main

if __name__ == '__main__':
    main(HERE)
