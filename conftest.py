# Ensure project root is on sys.path so 'import ex1' works when running pytest
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
