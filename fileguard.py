#!/usr/bin/env python3
"""
FileGuard — a file integrity monitor (CEH Final Tool Project)
Khadija — PNY Trainings, deadline 25 November 2026
Instructor: Abdul Mannan

How it works, in 3 steps:
  1. INIT: read every file in a folder, make a SHA-256 hash
     (a fingerprint) for each one, and save all hashes in a file.
  2. CHECK: run it again later. It makes fresh hashes and compares
     them with the saved ones.
  3. ALERT: if a hash is different, that file CHANGED. If a file is
     missing, it was DELETED. If a new file appears, it is NEW.
     Even changing one letter changes the whole hash, so nothing hides.
     Every alert is timestamped, printed, and appended to a log file.

Only the Python standard library is used — no install needed.
Test only on your own files, in the lab.

Usage (in Kali terminal, in the folder with this file):
    python3 fileguard.py init test-folder
    python3 fileguard.py check test-folder
    python3 fileguard.py watch test-folder --interval 60

    # Old names still work: init = baseline, check = scan
    python3 fileguard.py baseline test-folder
    python3 fileguard.py scan test-folder

    # Skip files or folders, e.g. temp files and a cache folder:
    python3 fileguard.py init test-folder --exclude "*.tmp" "cache"

    # Another hash algorithm (default is sha256):
    python3 fileguard.py init test-folder --hash md5

By default the baseline is saved as fileguard_baseline.json
and alerts are appended to fileguard.log, both in the current
folder. Use --baseline / --log to choose other names.

Exit code: 0 = no changes, 1 = changes found, 2 = usage error.
"""

import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import sys
import time

DEFAULT_BASELINE = "fileguard_baseline.json"
DEFAULT_LOG = "fileguard.log"


def hash_of(path, algo="sha256"):
    """Make the fingerprint of one file, reading it in chunks."""
    hasher = hashlib.new(algo)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)  # 8 KB at a time, so big files are fine
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def is_excluded(rel_path, patterns):
    """True if a relative path matches any exclude pattern."""
    for pattern in patterns:
        # Match the full relative path, or just the file/folder name
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        if fnmatch.fnmatch(os.path.basename(rel_path), pattern):
            return True
    return False


def collect(folder, baseline_path, excludes, algo="sha256"):
    """Walk a folder and return {relative_path: hash} for every file."""
    hashes = {}
    baseline_abs = os.path.abspath(baseline_path)
    for root, dirs, files in os.walk(folder):
        # Skip excluded folders, so os.walk does not go inside them
        dirs[:] = [d for d in dirs
                   if not is_excluded(os.path.relpath(
                       os.path.join(root, d), folder), excludes)]
        for name in files:
            full = os.path.join(root, name)
            # Never hash the baseline file itself
            if os.path.abspath(full) == baseline_abs:
                continue
            rel = os.path.relpath(full, folder)
            if is_excluded(rel, excludes):
                continue
            try:
                hashes[rel] = hash_of(full, algo)
            except (OSError, PermissionError) as e:
                print(f"[!] Skipped (cannot read): {rel} — {e}")
    return hashes


def alert(message, log_path):
    """Print one timestamped alert and append the same line to the log."""
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def cmd_init(args):
    if not os.path.isdir(args.folder):
        print(f"[!] Folder not found: {args.folder}")
        return 2
    hashes = collect(args.folder, args.baseline, args.exclude, args.hash)
    with open(args.baseline, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2, sort_keys=True)
    print(f"[+] Baseline saved: {len(hashes)} file(s) from '{args.folder}'")
    print(f"[+] Saved to: {args.baseline}")
    for path in sorted(hashes):
        print(f"    {path}  {hashes[path][:16]}...")
    return 0


def cmd_check(args):
    """Compare a folder with the saved baseline. Returns an exit code."""
    if not os.path.isdir(args.folder):
        print(f"[!] Folder not found: {args.folder}")
        return 2
    if not os.path.isfile(args.baseline):
        print(f"[!] No baseline found: {args.baseline}")
        print(f"    Run this first:  python3 fileguard.py init "
              f"{args.folder}")
        return 2
    with open(args.baseline, encoding="utf-8") as f:
        old = json.load(f)
    new = collect(args.folder, args.baseline, args.exclude, args.hash)

    changed = [p for p in old if p in new and old[p] != new[p]]
    deleted = [p for p in old if p not in new]
    added = [p for p in new if p not in old]
    unchanged = len(old) - len(changed) - len(deleted)

    print(f"[*] Scanned {len(new)} file(s), baseline had {len(old)}")
    for path in sorted(changed):
        alert(f"[!!] CHANGED: {path}", args.log)
    for path in sorted(deleted):
        alert(f"[!!] DELETED: {path}", args.log)
    for path in sorted(added):
        alert(f"[!!] NEW FILE: {path}", args.log)

    total = len(changed) + len(deleted) + len(added)
    print(f"[*] Summary: {len(changed)} changed, {len(deleted)} deleted, "
          f"{len(added)} new, {unchanged} unchanged")
    if total:
        print(f"\n[ALERT] {total} change(s) found — see {args.log}")
        return 1
    print("\n[OK] No changes — all files match the baseline.")
    return 0


def cmd_watch(args):
    """Re-scan every --interval seconds until Ctrl+C."""
    print(f"[*] Watching '{args.folder}' every {args.interval}s "
          f"(Ctrl+C to stop)")
    try:
        while True:
            cmd_check(args)
            print(f"[*] Next scan in {args.interval}s...")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[*] Watch stopped.")
        return 0


def main():
    # Line-buffered output, so watch mode prints each scan at once
    # even when the output is saved to a file.
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(
        description="FileGuard — file integrity monitor (SHA-256)")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, aliases, help_text in [
            ("init", ["baseline"],
             "Save hashes of a folder as the baseline"),
            ("check", ["scan"],
             "Compare a folder with the saved baseline"),
            ("watch", [],
             "Re-scan a folder again and again, every --interval")]:
        p = sub.add_parser(name, aliases=aliases, help=help_text)
        p.add_argument("folder", help="Folder to watch, e.g. test-folder")
        p.add_argument("--baseline", default=DEFAULT_BASELINE,
                       help="Baseline file (default: "
                            f"{DEFAULT_BASELINE})")
        p.add_argument("--log", default=DEFAULT_LOG,
                       help=f"Alert log file (default: {DEFAULT_LOG})")
        p.add_argument("--exclude", action="append", default=[],
                       help="Skip files/folders matching this pattern, "
                            "e.g. --exclude '*.tmp' (repeatable)")
        p.add_argument("--hash", default="sha256",
                       choices=["sha256", "sha1", "md5"],
                       help="Hash algorithm (default: sha256)")
        if name == "watch":
            p.add_argument("--interval", type=int, default=60,
                           help="Seconds between scans (default: 60)")

    args = parser.parse_args()
    if args.command in ("init", "baseline"):
        return cmd_init(args)
    if args.command in ("check", "scan"):
        return cmd_check(args)
    return cmd_watch(args)


if __name__ == "__main__":
    sys.exit(main())
