import sys
import os
from pathlib import Path

# Add backend to sys.path so we can import src
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from src.config.settings import get_settings

def verify():
    settings = get_settings()
    print(f"CWD: {os.getcwd()}")
    print(f"Loaded DATABASE_URL: {settings.DATABASE_URL}")

if __name__ == "__main__":
    verify()
