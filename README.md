# osu! Top Plays & Most Played Downloader

A modern tool to download an osu! player's most played or top performance (pp) beatmaps.

Supports **Desktop GUI**, **Windows One-Click Launcher (`run.bat`)**, **Bash (macOS / Linux)**, **Node.js**, **Bun**, and **Python**.

---

## Features
- **No Login or Cookie Required:** Downloads beatmaps directly via fast public osu! mirrors (Catboy, Sayobot, Nerinyan) without rate-limits or Cloudflare captcha blocks.
- **Flexible Player Input:** Accepts username (e.g. `Aut_Cratf`), numeric User ID (`19992487`), or full profile URL.
- **Custom Destination Folder:** Auto-detects your local osu! `Songs` directory, with a manual browse option to save directly into the game.
- **Unicode Filename Support:** Safely preserves Japanese, Korean, Thai, and special characters.
- **Deduplication:** Automatically groups difficulties from the same beatmapset into a single `.osz` download.
- **Dual Modes:** Download either **Most Played** or **Top Plays (Best pp)**.
- **Zero-Dependency Support:** Node.js, Bun, and Bash scripts use only native standard libraries.

---

## 1. Desktop GUI (Recommended)

### Windows
- **Option 1 (Recommended - Bypasses Smart App Control):** Double-click **`gui.bat`** (runs cleanly via signed pythonw without a console window).
- **Option 2 (Standalone Executable):** Double-click **`osu-downloader.exe`** (no Python required; if prompted by Windows Smart App Control, open Properties and check "Unblock").
- **Option 3 (Terminal):**
  ```powershell
  python gui.py
  ```

### macOS / Linux / Git Bash
```bash
chmod +x gui.sh
./gui.sh
```

---

## 2. Command Line (CLI) Options

### Windows One-Click (`run.bat`)
Double-click **`run.bat`**:
- Automatically detects and runs with **Bun**, **Node.js**, or **Python**.
- Prompts for player and options interactively.
- Offers to open the songs folder when finished.

### Bash Script (macOS / Linux / WSL / Git Bash)
Uses native `curl`:
```bash
chmod +x OSUDownloader.sh

# Interactive mode
./OSUDownloader.sh

# With arguments: ./OSUDownloader.sh <user> [count] [mode]
./OSUDownloader.sh Aut_Cratf 10 1
```

### Node.js / Bun
Requires Node.js 18+ (no `npm install` needed):
```powershell
node OSUDownloader.js Aut_Cratf 10 1

# Or with Bun (starts in ~10ms):
bun OSUDownloader.js Aut_Cratf 10 1
```

### Python
Requires Python 3.8+ and `requests`:
```powershell
pip install requests
python OSUDownloader.py Aut_Cratf 10 1
```

---

## How to Import Downloaded Beatmaps

If you selected your `osu!/Songs` directory as the destination:
- Open osu! and press **F5** in song select to reload and import the songs automatically.

If saved to `./songs/`:
- Double-click any `.osz` file, or select all files and drag them into the active osu! game window.

---

## License
MIT