import sys
import os

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_backend = os.path.join(_root, "backend")

for _p in [_root, _backend]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Import the FastAPI application instance
import main

# Vercel requires a top-level variable named pp
app = main.app
