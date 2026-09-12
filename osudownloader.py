import os
import re
import sys
import requests

MIRRORS = [
    ("Catboy", "https://catboy.best/d/{id}"),
    ("Sayobot", "https://dl.sayobot.cn/beatmaps/download/novideo/{id}"),
    ("Nerinyan", "https://api.nerinyan.moe/d/{id}?noVideo=true"),
]

HEADERS = {"User-Agent": "Mozilla/5.0"}


def sanitize_filename(filename: str) -> str:
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '_', filename)
    clean = clean.strip('. ')
    return clean or "beatmap"


def resolve_user_id(user_input: str) -> int:
    user_input = user_input.strip()
    match = re.search(r'/(?:users|u)/(\d+)', user_input)
    if match:
        return int(match.group(1))
    if user_input.isdigit():
        return int(user_input)

    # Username lookup via profile redirect
    resp = requests.get(
        f"https://osu.ppy.sh/users/{user_input}",
        headers=HEADERS,
        allow_redirects=True,
        timeout=10,
    )
    match = re.search(r'/(?:users|u)/(\d+)', resp.url)
    if match:
        return int(match.group(1))
    raise ValueError(f"Could not resolve user ID for: '{user_input}'")


def fetch_maps(user_id: int, count: int, mode: int = 1):
    endpoint = "beatmapsets/most_played" if mode == 1 else "scores/best"
    maps = []
    offset = 0

    while len(maps) < count:
        limit = min(100, count - len(maps))
        url = f"https://osu.ppy.sh/users/{user_id}/{endpoint}?offset={offset}&limit={limit}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"API returned HTTP {resp.status_code}")
            break
        batch = resp.json()
        if not batch:
            break
        maps.extend(batch)
        offset += len(batch)
        if len(batch) < limit:
            break

    return maps


def download_beatmapset(set_id: int, title: str, output_dir: str = "./songs") -> bool:
    safe_title = sanitize_filename(title)
    filename = f"{set_id} {safe_title}.osz"
    target_path = os.path.join(output_dir, filename)

    if os.path.exists(target_path) and os.path.getsize(target_path) > 1024:
        print(f"Already downloaded: {filename}")
        return True

    temp_path = target_path + ".tmp"
    for name, template in MIRRORS:
        url = template.format(id=set_id)
        try:
            print(f"  Downloading from {name}...", flush=True)
            with requests.get(url, headers=HEADERS, stream=True, timeout=20) as r:
                if r.status_code != 200:
                    continue
                chunks = r.iter_content(chunk_size=65536)
                first = next(chunks, b"")
                if not first.startswith(b"PK\x03\x04"):
                    continue
                with open(temp_path, "wb") as f:
                    f.write(first)
                    for chunk in chunks:
                        if chunk:
                            f.write(chunk)

            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 1024:
                if os.path.exists(target_path):
                    os.remove(target_path)
                os.rename(temp_path, target_path)
                print(f"  Saved: {filename}", flush=True)
                return True
        except Exception:
            pass
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    print(f"  Failed to download mapset {set_id} from all mirrors.", flush=True)
    return False


def run_self_check():
    print("Running self-check...")
    assert sanitize_filename('test: *?/"<>| name. ') == "test_ _ name"
    assert sanitize_filename('夜に駆ける') == "夜に駆ける"
    assert resolve_user_id("https://osu.ppy.sh/users/2") == 2
    assert resolve_user_id("2") == 2
    print("Self-check passed!")


def main():
    if "--test" in sys.argv:
        run_self_check()
        return

    os.makedirs("./songs", exist_ok=True)

    if len(sys.argv) > 1:
        raw_user = sys.argv[1]
        number_of_maps = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        mode = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    else:
        raw_user = input("Enter User ID, Profile URL, or Username: ").strip()
        num_str = input("Enter number of maps to download (default 10): ").strip()
        number_of_maps = int(num_str) if num_str else 10
        mode_str = input("Choose mode [1: Most Played (default), 2: Top Plays (Best pp)]: ").strip()
        mode = int(mode_str) if mode_str in ("1", "2") else 1

    try:
        user_id = resolve_user_id(raw_user)
    except Exception as e:
        print(f"Error: {e}")
        return

    mode_label = "Most Played" if mode == 1 else "Top Plays (Best pp)"
    print(f"\nFetching {number_of_maps} {mode_label} for user ID {user_id}...")
    raw_maps = fetch_maps(user_id, number_of_maps, mode)
    if not raw_maps:
        print("No beatmaps found.")
        return

    # Deduplicate beatmapsets
    seen = set()
    mapsets = []
    for item in raw_maps:
        set_info = item.get("beatmapset")
        if set_info and set_info["id"] not in seen:
            seen.add(set_info["id"])
            mapsets.append((set_info["id"], set_info["title"]))

    print(f"Found {len(mapsets)} unique beatmapsets to download.\n")

    success = 0
    for idx, (sid, title) in enumerate(mapsets, 1):
        print(f"[{idx}/{len(mapsets)}] Beatmapset {sid}: {title}")
        if download_beatmapset(sid, title):
            success += 1

    print(f"\nDone! Downloaded {success}/{len(mapsets)} beatmapsets into './songs/'.")


if __name__ == "__main__":
    main()