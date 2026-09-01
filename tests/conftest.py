import sys
from pathlib import Path

# Ensure the project root is importable by pytest regardless of the working directory.
# This keeps tests stable when they are launched from the repo root or from inside the
# tests folder itself.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
