"""Project-relative configuration; environment variables override YAML defaults."""
import os
from functools import lru_cache
from pathlib import Path
import yaml
from dotenv import load_dotenv
# Anchor paths to the checkout so launch commands work from other directories.
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)
@lru_cache(maxsize=1)
def settings():
    with (ROOT / "config.yaml").open() as handle:
        return yaml.safe_load(handle) or {}
def option(name, default=None):
    return os.getenv(name.upper(), settings().get(name, default))
