import os
from pathlib import Path

# Make the directory in which dispatch is called the main directory
ROOT = Path(__file__).parent.parent.resolve()
INVOCATION_DIR = Path(os.getcwd())
CONFIG_FILE = ROOT / "config.json"
MEMORY_FILE = ROOT / "memory.md"
SESSION_FILE = ROOT / "session.json"