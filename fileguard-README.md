# FileGuard — Khadija's CEH Final Tool Project

**Student:** Khadija
**Project:** FileGuard
**Instructor:** Abdul Mannan
**Institute:** PNY Trainings

## How it works — 3 steps

1. **Init (baseline):** `fileguard.py` reads every file in a folder, makes a SHA-256 hash (fingerprint) for each, and saves them in `fileguard_baseline.json`.
2. **Check (scan):** Run it again later. It makes fresh hashes and compares them with the saved ones.
3. **Alert:** Hash different = file **CHANGED**. File missing = **DELETED**. File not in baseline = **NEW FILE**. One letter changed = whole hash changes, so nothing hides. Har alert ke sath time (timestamp) hota hai, screen par bhi aur `fileguard.log` file mein bhi.

## Try it in Kali (5 minutes)

```bash
# 1. A test folder banao, with 2 files
mkdir test-folder
echo "hello" > test-folder/notes.txt
echo "important" > test-folder/secret.txt

# 2. Baseline banao
python3 fileguard.py init test-folder

# 3. Check karo — kuch change nahi, to [OK] ayega
python3 fileguard.py check test-folder

# 4. Ab ek file change karo, ek delete karo, ek nayi banao
echo "changed" >> test-folder/notes.txt
rm test-folder/secret.txt
echo "new" > test-folder/added.txt

# 5. Dobara check karo — teeno alerts dikhenge, aur fileguard.log mein bhi likhe jayenge
python3 fileguard.py check test-folder
cat fileguard.log
```

Expected second check:
```
[2026-11-14 19:48:46] [!!] CHANGED: notes.txt
[2026-11-14 19:48:46] [!!] DELETED: secret.txt
[2026-11-14 19:48:46] [!!] NEW FILE: added.txt
[*] Summary: 1 changed, 1 deleted, 1 new, 1 unchanged
```

Exit code: `0` = no changes, `1` = changes found, `2` = usage error. Check with `echo $?` after a scan.

## Must-have features (PDF se) — sab kaam karte hain

| Feature | Kaise |
|---|---|
| Recursive walk, relative path → SHA-256 | `os.walk()`, har file ka hash |
| Baseline JSON save/load | `fileguard_baseline.json` |
| Added / modified / deleted / unchanged | `check` mein charon categories |
| Timestamped alerts + log file | Har alert `[date time]` ke sath screen par aur `fileguard.log` mein |
| Exclude patterns | `--exclude "*.tmp" --exclude "cache"` — aisi files/folders skip ho jati hain |
| CLI arguments | `init` / `check` / `watch`, `--baseline`, `--log`, `--hash`, `--interval` |

Stretch features bhi hain: `watch` mode (har `--interval` seconds baad dobara scan, Ctrl+C se stop) aur `--hash md5` / `--hash sha1` se hash algorithm badalna. Default SHA-256 hai.

```bash
# Watch mode — har 60 seconds baad khud check karega
python3 fileguard.py watch test-folder --interval 60

# Kuch files skip karni hon to (pattern dobara likhna hota hai)
python3 fileguard.py init test-folder --exclude "*.tmp" --exclude "cache"
python3 fileguard.py check test-folder --exclude "*.tmp" --exclude "cache"
```

Purane naam bhi chalte hain: `init` = `baseline`, `check` = `scan`.

## Second folder bhi check karna ho to

Folder ko sirf kholne ya search karne se kuch nahi hota — FileGuard real-time nahi hai, sirf jab `check` ya `watch` chalao tab check karta hai, aur sirf wohi folder jo command mein likha ho.

Har folder ki apni alag baseline honi chahiye, warna dusre folder ki `init` pehle wali `fileguard_baseline.json` ko overwrite kar degi, aur pehle folder ka check galat alerts dega (DELETED + NEW FILE, jab kuch badla hi nahi).

```bash
# Dono folders ki alag-alag baseline banao
python3 fileguard.py init test-folder --baseline test-folder-baseline.json
python3 fileguard.py init folder2 --baseline folder2-baseline.json

# Check karte waqt wahi --baseline naam dobara likhna zaroori hai
python3 fileguard.py check test-folder --baseline test-folder-baseline.json
python3 fileguard.py check folder2 --baseline folder2-baseline.json
```

Agar check mein `--baseline` bhool jao to tool default `fileguard_baseline.json` dhoondhega — ya to `[!] No baseline found` ayega, ya galat folder se compare hoga.

##  how it works

- `hashlib.sha256()` — har file ka fingerprint banata hai, file ko 8 KB chunks mein parh kar (bari files bhi theek).
- `os.walk()` — folder ke andar har file tak jata hai, sub-folders samet.
- Baseline ek JSON file hai: `{ "notes.txt": "29a6fcb6...", ... }` — is liye baseline file khud scan nahi hoti.
- `argparse` — `init`, `check` aur `watch` commands ko samajhta hai.
- `fnmatch` — `--exclude` patterns ko match karta hai.
- `datetime.now()` — har alert ke sath time likhta hai, aur alert `fileguard.log` mein bhi save hota hai.

## Deliverables

- Working tool — `fileguard.py`, command line se chalta hai.
- README — ye file.
- Short demo aur write-up — lab mein chalao, ek detected change dikhao, btao kya pakda gaya aur kyun matter karta hai.
- GitHub par publish karna — code + README + sample alert log (`fileguard.log`).

## Rules from the notice

- Working Python tool hona chahiye, sirf report nahi.
- Sirf lab mein test karo, apni files par — kisi aur ke system par nahi.
