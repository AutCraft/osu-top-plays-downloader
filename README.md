# osu! Top Plays & Most Played Downloader

A tool to download an osu! player's most played or top performance beatmaps. Supports **Windows Double-Click**, **Bash (macOS/Linux)**, **Bun**, **Node.js**, and **Python**.

## Features
- **No login or cookie required:** Downloads directly via fast public osu! beatmap mirrors (Catboy, Sayobot, Nerinyan).
- **Supports Username, User ID, or Profile URL:** Paste either `peppy`, `2`, or `https://osu.ppy.sh/users/2`.
- **Unicode Filename Support:** Preserves Japanese, Chinese, Korean, and special characters properly.
- **Deduplication:** Automatically ignores duplicate beatmapsets across difficulties.
- **Mode Selection:** Download either **Most Played** or **Top Plays (Best pp)**.
- **Zero-Dependency in Node.js / Bun / Bash:** Runs on native standard libraries (no `npm install` needed).

---

## 1. Quick Start (Windows)
Just double-click **`run.bat`**!
- Automatically detects and runs with **Bun**, **Node.js**, or **Python**
- Prompts for player name/ID and downloads beatmaps
- Automatically asks to open the `./songs/` folder when finished

---

## 2. Bash Script (macOS / Linux / WSL / Git Bash)
Uses native `curl`:
```bash
chmod +x OSUDownloader.sh

# Interactive
./OSUDownloader.sh

# Or with arguments
./OSUDownloader.sh mrekk 10 1
```

---

## 3. Bun (Blazing Fast)
Run directly with Bun (starts in ~10ms):
```bash
bun OSUDownloader.js mrekk 10 1
```
Or compile into a standalone portable `.exe`:
```bash
bun build --compile OSUDownloader.js --outfile osu-downloader.exe
```

---

## 4. Node.js
Requires Node.js 18+ (no npm packages needed):
```powershell
node OSUDownloader.js
# or with arguments
node OSUDownloader.js mrekk 10 1
```

---

## 5. Python
Requires Python 3.8+ and `requests`:
```powershell
pip install requests
python OSUDownloader.py
# or with arguments
python OSUDownloader.py mrekk 10 1
```

---

All beatmap archives (`.osz`) are downloaded into the `./songs/` folder. Simply double-click any `.osz` file to import it into osu!.