import sys
import os

# Ensure workspace root is on sys.path so `import app` works when pytest runs
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
