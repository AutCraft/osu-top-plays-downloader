# osu! Top Plays & Most Played Downloader

A tool to download an osu! player's most played or top performance beatmaps.

## Features
- **No login or cookie required:** Downloads directly via fast public osu! beatmap mirrors (Catboy, Sayobot, Nerinyan).
- **Supports Username, User ID, or Profile URL:** Paste either `peppy`, `2`, or `https://osu.ppy.sh/users/2`.
- **Unicode Filename Support:** Preserves Japanese, Chinese, Korean, and special characters properly.
- **Deduplication:** Automatically ignores duplicate beatmapsets across difficulties.
- **Mode Selection:** Download either **Most Played** or **Top Plays (Best pp)**.

## Requirements
- **Python 3** (3.8+)
- **requests** library:
  ```bash
  pip install requests
  ```

## Usage

### Interactive Mode
Run the script:
```powershell
python OSUDownloader.py
```
Follow the prompts:
1. **User:** Enter username, user ID, or full profile URL.
2. **Number of maps:** Number of beatmaps to fetch (e.g. `20`).
3. **Mode:** `1` for Most Played (default) or `2` for Top Plays (Best pp).

### Command Line Mode
You can also run it directly with arguments:
```powershell
python OSUDownloader.py <user> [count] [mode]
```
Example:
```powershell
python OSUDownloader.py mrekk 10 1
```

All beatmap archives (`.osz`) are downloaded into the `./songs/` folder. Simply double-click any `.osz` file to import it into osu!.