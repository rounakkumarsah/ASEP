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
    url = settings.DATABASE_URL
    if "@" in url:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            masked_netloc = f"{parsed.username}:*****@{parsed.hostname}"
            if parsed.port:
                masked_netloc += f":{parsed.port}"
            url = parsed._replace(netloc=masked_netloc).geturl()
        except Exception:
            url = "[MASKED]"
    print(f"Loaded DATABASE_URL: {url}")

if __name__ == "__main__":
    verify()
