import os
import re
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests

# --- osu! Dark Theme Colors ---
BG_COLOR = "#1e1b24"
CARD_BG = "#2a2438"
INPUT_BG = "#181520"
ACCENT_PINK = "#ff66aa"
ACCENT_HOVER = "#ff85be"
TEXT_COLOR = "#ffffff"
SUBTEXT_COLOR = "#b8b0c4"
BORDER_COLOR = "#443859"
SUCCESS_COLOR = "#70e090"
WARN_COLOR = "#ffbb55"

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


def fetch_maps(user_id: int, count: int, mode: int = 1, cancel_check=None):
    endpoint = "beatmapsets/most_played" if mode == 1 else "scores/best"
    maps = []
    offset = 0

    while len(maps) < count:
        if cancel_check and cancel_check():
            break
        limit = min(100, count - len(maps))
        url = f"https://osu.ppy.sh/users/{user_id}/{endpoint}?offset={offset}&limit={limit}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            break
        batch = resp.json()
        if not batch:
            break
        maps.extend(batch)
        offset += len(batch)
        if len(batch) < limit:
            break

    return maps


class OsuDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("osu! Beatmap Downloader")
        self.root.geometry("560x700")
        self.root.minsize(500, 640)
        self.root.configure(bg=BG_COLOR)

        self.is_downloading = False
        self.cancel_requested = False

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Osu.Horizontal.TProgressbar",
            troughcolor=INPUT_BG,
            background=ACCENT_PINK,
            borderwidth=0,
            thickness=12,
        )

    def _build_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg=BG_COLOR, padx=24, pady=16)
        header_frame.pack(fill="x")

        title_lbl = tk.Label(
            header_frame,
            text="osu! Beatmap Downloader",
            font=("Segoe UI", 18, "bold"),
            fg=ACCENT_PINK,
            bg=BG_COLOR,
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            header_frame,
            text="Download Most Played & Top Performance Beatmaps",
            font=("Segoe UI", 9),
            fg=SUBTEXT_COLOR,
            bg=BG_COLOR,
        )
        subtitle_lbl.pack(anchor="w", pady=(2, 0))

        # Main Card Frame
        card = tk.Frame(self.root, bg=CARD_BG, padx=20, pady=20, highlightthickness=1, highlightbackground=BORDER_COLOR)
        card.pack(fill="x", padx=24, pady=(0, 16))

        # 1. User Input
        user_lbl = tk.Label(
            card,
            text="Player (Username, ID, or Profile URL)",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_COLOR,
            bg=CARD_BG,
        )
        user_lbl.pack(anchor="w")

        self.user_entry = tk.Entry(
            card,
            font=("Segoe UI", 11),
            bg=INPUT_BG,
            fg=TEXT_COLOR,
            insertbackground=ACCENT_PINK,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_PINK,
        )
        self.user_entry.pack(fill="x", pady=(6, 14), ipady=6)
        self.user_entry.insert(0, "Aut_Cratf")

        # 2. Number of Maps & Mode in 2 columns
        options_frame = tk.Frame(card, bg=CARD_BG)
        options_frame.pack(fill="x", pady=(0, 14))

        # Left: Count
        count_frame = tk.Frame(options_frame, bg=CARD_BG)
        count_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        count_lbl = tk.Label(
            count_frame,
            text="Number of maps",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_COLOR,
            bg=CARD_BG,
        )
        count_lbl.pack(anchor="w")

        self.count_spin = tk.Spinbox(
            count_frame,
            from_=1,
            to=1000,
            font=("Segoe UI", 11),
            bg=INPUT_BG,
            fg=TEXT_COLOR,
            buttonbackground=BORDER_COLOR,
            insertbackground=ACCENT_PINK,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_PINK,
        )
        self.count_spin.pack(fill="x", pady=(6, 0), ipady=5)
        self.count_spin.delete(0, "end")
        self.count_spin.insert(0, "10")

        # Right: Mode
        mode_frame = tk.Frame(options_frame, bg=CARD_BG)
        mode_frame.pack(side="right", fill="x", expand=True, padx=(10, 0))

        mode_lbl = tk.Label(
            mode_frame,
            text="Download Mode",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_COLOR,
            bg=CARD_BG,
        )
        mode_lbl.pack(anchor="w")

        self.mode_var = tk.IntVar(value=1)
        radio_row = tk.Frame(mode_frame, bg=CARD_BG)
        radio_row.pack(anchor="w", pady=(6, 0))

        r1 = tk.Radiobutton(
            radio_row,
            text="Most Played",
            variable=self.mode_var,
            value=1,
            fg=TEXT_COLOR,
            bg=CARD_BG,
            selectcolor=INPUT_BG,
            activebackground=CARD_BG,
            activeforeground=ACCENT_PINK,
            font=("Segoe UI", 9),
        )
        r1.pack(side="left", padx=(0, 10))

        r2 = tk.Radiobutton(
            radio_row,
            text="Top Plays",
            variable=self.mode_var,
            value=2,
            fg=TEXT_COLOR,
            bg=CARD_BG,
            selectcolor=INPUT_BG,
            activebackground=CARD_BG,
            activeforeground=ACCENT_PINK,
            font=("Segoe UI", 9),
        )
        r2.pack(side="left")

        # 3. osu! Songs Folder Path (Destination)
        path_header = tk.Frame(card, bg=CARD_BG)
        path_header.pack(fill="x", pady=(0, 4))

        path_lbl = tk.Label(
            path_header,
            text="osu! Songs Folder (Destination Path)",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_COLOR,
            bg=CARD_BG,
        )
        path_lbl.pack(side="left")

        auto_btn = tk.Button(
            path_header,
            text="Auto-detect",
            font=("Segoe UI", 8, "underline"),
            bg=CARD_BG,
            fg=ACCENT_PINK,
            activebackground=CARD_BG,
            activeforeground=ACCENT_HOVER,
            relief="flat",
            cursor="hand2",
            bd=0,
            command=self._auto_detect_path,
        )
        auto_btn.pack(side="right")

        path_input_row = tk.Frame(card, bg=CARD_BG)
        path_input_row.pack(fill="x", pady=(0, 16))

        self.path_entry = tk.Entry(
            path_input_row,
            font=("Segoe UI", 10),
            bg=INPUT_BG,
            fg=TEXT_COLOR,
            insertbackground=ACCENT_PINK,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_PINK,
        )
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=5)
        self.path_entry.insert(0, self._detect_songs_path())

        browse_btn = tk.Button(
            path_input_row,
            text="Browse...",
            font=("Segoe UI", 9),
            bg=BORDER_COLOR,
            fg=TEXT_COLOR,
            activebackground=ACCENT_PINK,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=12,
            command=self._browse_path,
        )
        browse_btn.pack(side="right", padx=(8, 0), ipady=3)

        # 4. Big Action Button
        self.download_btn = tk.Button(
            card,
            text="Start Download",
            font=("Segoe UI", 12, "bold"),
            bg=ACCENT_PINK,
            fg="#ffffff",
            activebackground=ACCENT_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            command=self._toggle_download,
        )
        self.download_btn.pack(fill="x", ipady=8)

        # Bottom Frame: Status & Progress Logs
        bottom_frame = tk.Frame(self.root, bg=BG_COLOR, padx=24)
        bottom_frame.pack(fill="both", expand=True, pady=(0, 16))

        status_row = tk.Frame(bottom_frame, bg=BG_COLOR)
        status_row.pack(fill="x", pady=(0, 6))

        self.status_lbl = tk.Label(
            status_row,
            text="Status: Ready",
            font=("Segoe UI", 9),
            fg=SUBTEXT_COLOR,
            bg=BG_COLOR,
        )
        self.status_lbl.pack(side="left")

        self.progress = ttk.Progressbar(
            bottom_frame,
            style="Osu.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
        )
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress["value"] = 0

        # Beatmap List / Log Box
        self.log_box = tk.Listbox(
            bottom_frame,
            font=("Consolas", 9),
            bg=INPUT_BG,
            fg=TEXT_COLOR,
            selectbackground=CARD_BG,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
        )
        self.log_box.pack(fill="both", expand=True, pady=(0, 10))

        # Footer Buttons
        footer_frame = tk.Frame(bottom_frame, bg=BG_COLOR)
        footer_frame.pack(fill="x")

        folder_btn = tk.Button(
            footer_frame,
            text="Open Selected Folder",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=TEXT_COLOR,
            activebackground=BORDER_COLOR,
            activeforeground=TEXT_COLOR,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._open_songs_folder,
        )
        folder_btn.pack(side="left")

        clear_btn = tk.Button(
            footer_frame,
            text="Clear",
            font=("Segoe UI", 9),
            bg=CARD_BG,
            fg=SUBTEXT_COLOR,
            activebackground=BORDER_COLOR,
            activeforeground=TEXT_COLOR,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._clear_logs,
        )
        clear_btn.pack(side="right")

    def _detect_songs_path(self):
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            candidate = os.path.join(local_appdata, "osu!", "Songs")
            if os.path.isdir(candidate):
                return os.path.abspath(candidate)

        for drive in ["C:", "D:", "E:", "F:"]:
            candidate = os.path.join(drive, os.sep, "osu!", "Songs")
            if os.path.isdir(candidate):
                return os.path.abspath(candidate)

        return os.path.abspath("./songs")

    def _browse_path(self):
        current = self.path_entry.get().strip() or "./songs"
        chosen = filedialog.askdirectory(
            title="Select osu! Songs Folder",
            initialdir=current if os.path.isdir(current) else "./songs",
        )
        if chosen:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, os.path.abspath(chosen))

    def _auto_detect_path(self):
        detected = self._detect_songs_path()
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, detected)
        self._update_status(f"Auto-detected path: {os.path.basename(detected)}", ACCENT_PINK)

    def _open_songs_folder(self):
        target = self.path_entry.get().strip() or "./songs"
        os.makedirs(target, exist_ok=True)
        os.startfile(os.path.abspath(target))

    def _clear_logs(self):
        if not self.is_downloading:
            self.log_box.delete(0, "end")
            self.progress["value"] = 0
            self._update_status("Status: Ready", SUBTEXT_COLOR)

    def _update_status(self, text, fg=None):
        self.root.after(0, lambda: self.status_lbl.config(text=text, fg=fg or SUBTEXT_COLOR))

    def _update_progress(self, val):
        self.root.after(0, lambda: self.progress.configure(value=val))

    def _append_log(self, text):
        def _add():
            self.log_box.insert("end", text)
            self.log_box.see("end")
        self.root.after(0, _add)

    def _toggle_download(self):
        if self.is_downloading:
            # Request cancel
            self.cancel_requested = True
            self.download_btn.config(text="Stopping...", state="disabled")
            self._update_status("Cancelling download...", WARN_COLOR)
            return

        # Start download
        raw_user = self.user_entry.get().strip()
        if not raw_user:
            messagebox.showwarning("Input Required", "Please enter a player username, user ID, or profile URL.")
            return

        try:
            count = int(self.count_spin.get().strip())
            if count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Count", "Please enter a valid positive number for maps.")
            return

        dest_dir = self.path_entry.get().strip() or "./songs"
        os.makedirs(dest_dir, exist_ok=True)

        mode = self.mode_var.get()
        self.is_downloading = True
        self.cancel_requested = False
        self.download_btn.config(text="Cancel Download", bg="#e04060", activebackground="#ff5070")

        # Launch download in background thread
        thread = threading.Thread(
            target=self._run_download_thread,
            args=(raw_user, count, mode, dest_dir),
            daemon=True,
        )
        thread.start()

    def _run_download_thread(self, raw_user, count, mode, dest_dir):
        mode_label = "Most Played" if mode == 1 else "Top Plays"
        self._update_status(f"Resolving player '{raw_user}'...", ACCENT_PINK)
        self._append_log(f"--- Starting Download for {raw_user} ({count} {mode_label}) ---")

        try:
            user_id = resolve_user_id(raw_user)
        except Exception as e:
            self._update_status(f"Error: {e}", "#ff5555")
            self._append_log(f"Error: {e}")
            self._finish_download(0, 0, 0)
            return

        self._update_status(f"Fetching {count} {mode_label} for ID {user_id}...", ACCENT_PINK)
        raw_maps = fetch_maps(user_id, count, mode, cancel_check=lambda: self.cancel_requested)

        if self.cancel_requested:
            self._update_status("Download cancelled by user.", WARN_COLOR)
            self._finish_download(0, 0, 0)
            return

        if not raw_maps:
            self._update_status("No beatmaps found.", WARN_COLOR)
            self._append_log("No beatmaps found for this user.")
            self._finish_download(0, 0, 0)
            return

        # Deduplicate beatmapsets
        seen = set()
        mapsets = []
        for item in raw_maps:
            set_info = item.get("beatmapset")
            if set_info and set_info["id"] not in seen:
                seen.add(set_info["id"])
                mapsets.append((set_info["id"], set_info["title"]))

        total_difficulties = len(raw_maps)
        total_unique = len(mapsets)
        self._append_log(f"Found {total_unique} unique beatmapsets ({total_difficulties} total difficulties/plays).")

        success = 0
        for idx, (sid, title) in enumerate(mapsets, 1):
            if self.cancel_requested:
                self._append_log(f"Stopped by user at [{idx}/{total_unique}].")
                break

            pct = int(((idx - 1) / total_unique) * 100)
            self._update_progress(pct)
            self._update_status(f"[{idx}/{total_unique}] Downloading: {title}", TEXT_COLOR)

            ok, msg = self._download_single_beatmap(sid, title, dest_dir)
            if ok:
                success += 1
                self._append_log(f"  [{idx}/{total_unique}] {sid}: {title} ({msg})")
            else:
                self._append_log(f"  [{idx}/{total_unique}] {sid}: {title} (FAILED: {msg})")

        self._update_progress(100)
        status_msg = f"Done! Downloaded {success}/{total_unique} ({total_difficulties} difficulties) into destination."
        self._update_status(status_msg, SUCCESS_COLOR)
        self._append_log(f"--- {status_msg} ---")
        self._finish_download(success, total_unique, total_difficulties)

    def _download_single_beatmap(self, set_id: int, title: str, output_dir: str):
        safe_title = sanitize_filename(title)
        filename = f"{set_id} {safe_title}.osz"
        target_path = os.path.join(output_dir, filename)

        if os.path.exists(target_path) and os.path.getsize(target_path) > 1024:
            return True, "Already downloaded"

        temp_path = target_path + ".tmp"
        for name, template in MIRRORS:
            if self.cancel_requested:
                break
            url = template.format(id=set_id)
            try:
                with requests.get(url, headers=HEADERS, stream=True, timeout=25) as r:
                    if r.status_code != 200:
                        continue
                    chunks = r.iter_content(chunk_size=65536)
                    first = next(chunks, b"")
                    if not first.startswith(b"PK\x03\x04"):
                        continue
                    with open(temp_path, "wb") as f:
                        f.write(first)
                        for chunk in chunks:
                            if self.cancel_requested:
                                break
                            if chunk:
                                f.write(chunk)

                if self.cancel_requested:
                    break

                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 1024:
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    os.rename(temp_path, target_path)
                    return True, f"Saved from {name}"
            except Exception:
                pass
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass

        return False, "All mirrors failed"

    def _finish_download(self, success, total_unique, total_diffs):
        def _reset_btn():
            self.is_downloading = False
            self.cancel_requested = False
            self.download_btn.config(
                text="Start Download",
                bg=ACCENT_PINK,
                activebackground=ACCENT_HOVER,
                state="normal",
            )
        self.root.after(0, _reset_btn)


if __name__ == "__main__":
    root = tk.Tk()
    app = OsuDownloaderGUI(root)
    root.mainloop()
