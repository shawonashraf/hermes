"""Keeps the host copy of Hermes's restore data (data/core) in step with its
home volume (/opt/data). See docker-compose.yml.

    sync.py restore   copy BACKUP into HOME if HOME has no state.db yet
    sync.py backup    snapshot HOME into BACKUP every INTERVAL s and on SIGTERM

SQLite databases are copied with the backup API, so a snapshot taken while
Hermes writes is still consistent. Their -wal/-shm sidecars are not copied.
"""

import filecmp
import os
import shutil
import signal
import sqlite3
import sys
import time
from pathlib import Path

HOME = Path("/opt/data")
BACKUP = Path("/backup")
INTERVAL = int(os.environ.get("CORE_SYNC_INTERVAL", "60"))

# What Hermes needs to come back as it was: sessions and messages
# (state.db), memories, persona, config, cron jobs, skills, plans, pairings.
# Everything else in HOME (caches, installs, logs, the tool home) is rebuilt.
FILES = [
    "state.db", "kanban.db", "projects.db", "response_store.db",
    "SOUL.md", "config.yaml", ".env", "channel_directory.json",
]
DIRS = [
    "memories", "cron", "skills", "plans", "pairing", "platforms",
    "hooks", "skins", "workspace", "kanban", "sessions",
]
SKIP_SUFFIXES = ("-wal", "-shm", "-journal", ".lock")


def log(msg):
    print(f"core-sync: {msg}", file=sys.stderr, flush=True)


def copy_file(src, dst):
    """Copy src to dst atomically; leave dst untouched if nothing changed."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f".{dst.name}.tmp")
    if src.suffix == ".db":
        source = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=30)
        target = sqlite3.connect(tmp)
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        shutil.copystat(src, tmp)
    else:
        shutil.copy2(src, tmp)
    if dst.is_file() and filecmp.cmp(tmp, dst, shallow=False):
        tmp.unlink()
        shutil.copymode(src, dst)
    else:
        os.replace(tmp, dst)


def wanted(path):
    return path.is_file() and not path.is_symlink() and not path.name.endswith(SKIP_SUFFIXES)


def mirror_dir(src, dst):
    """Make dst hold exactly src's wanted files."""
    keep = set()
    for path in src.rglob("*"):
        if wanted(path):
            rel = path.relative_to(src)
            keep.add(rel)
            copy_file(path, dst / rel)
    if dst.is_dir():
        for path in sorted(dst.rglob("*"), reverse=True):
            rel = path.relative_to(dst)
            if path.is_file() and rel not in keep:
                path.unlink()
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()


def backup():
    for name in FILES:
        src, dst = HOME / name, BACKUP / name
        if wanted(src):
            copy_file(src, dst)
        elif dst.is_file():
            dst.unlink()
    for name in DIRS:
        src, dst = HOME / name, BACKUP / name
        if src.is_dir():
            mirror_dir(src, dst)
        elif dst.is_dir():
            shutil.rmtree(dst)


def restore():
    if (HOME / "state.db").exists():
        log("home volume already has state.db; nothing restored")
        return
    if not (BACKUP / "state.db").is_file():
        log("no backup in data/core; starting fresh")
        return
    for path in BACKUP.rglob("*"):
        if path.is_file() and not path.name.endswith(".tmp"):
            dst = HOME / path.relative_to(BACKUP)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)
    log("restored the home volume from data/core")


def run_backups():
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    log(f"snapshotting every {INTERVAL}s")
    while True:
        if (HOME / "state.db").exists():
            try:
                backup()
            except (OSError, sqlite3.Error) as e:
                log(f"snapshot failed: {e}")
        if stopping:
            log("final snapshot written")
            return
        deadline = time.monotonic() + INTERVAL
        while not stopping and time.monotonic() < deadline:
            time.sleep(0.5)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "restore":
        restore()
    elif mode == "backup":
        run_backups()
    else:
        sys.exit("usage: sync.py restore|backup")
