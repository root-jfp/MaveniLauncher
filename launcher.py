from __future__ import annotations

import hashlib
import json
import os
import queue
import subprocess
import threading
import urllib.request
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "launcher.json"
DEFAULT_CONFIG = {
    "manifest_url": "https://example.invalid/maveni/manifest.json",
    "install_dir": str(ROOT / "game"),
    "game_exe": "metin2client.exe",
    "game_args": [],
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {**DEFAULT_CONFIG, **data}


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def download_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "MaveniLauncher/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class Launcher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Maveni Launcher")
        self.geometry("720x430")
        self.minsize(620, 360)
        self.configure(bg="#0b0d0e")
        self.config_data = load_config()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.manifest: dict | None = None
        self.status = tk.StringVar(value="Ready")
        self.version = tk.StringVar(value="Installed version: unknown")
        self._build_ui()
        self.after(100, self._drain_events)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Maveni.TButton", padding=10, foreground="#f5e8ca", background="#704719")
        style.configure("Maveni.TLabel", foreground="#d8c6a2", background="#0b0d0e")
        style.configure("Maveni.TEntry", fieldbackground="#171b1a", foreground="#f2eee5")

        header = tk.Frame(self, bg="#121617", height=100)
        header.pack(fill="x")
        tk.Label(header, text="MAVENI", fg="#ddbb74", bg="#121617", font=("Georgia", 28, "bold")).pack(anchor="w", padx=30, pady=(22, 0))
        tk.Label(header, text="METIN2 CLIENT LAUNCHER", fg="#aaa89f", bg="#121617", font=("Segoe UI", 9)).pack(anchor="w", padx=32)

        body = tk.Frame(self, bg="#0b0d0e")
        body.pack(fill="both", expand=True, padx=30, pady=24)
        tk.Label(body, textvariable=self.version, fg="#ddbb74", bg="#0b0d0e", font=("Segoe UI", 11)).pack(anchor="w")
        tk.Label(body, textvariable=self.status, fg="#aaa89f", bg="#0b0d0e", wraplength=650, justify="left").pack(anchor="w", pady=(10, 20))
        self.news = tk.Text(body, height=8, bg="#121617", fg="#d8d2c6", relief="flat", state="disabled", wrap="word")
        self.news.pack(fill="both", expand=True)

        actions = tk.Frame(self, bg="#0b0d0e")
        actions.pack(fill="x", padx=30, pady=(0, 25))
        ttk.Button(actions, text="Check for updates", style="Maveni.TButton", command=self.check_updates).pack(side="left")
        ttk.Button(actions, text="Update client", style="Maveni.TButton", command=self.update_client).pack(side="left", padx=10)
        ttk.Button(actions, text="Settings", style="Maveni.TButton", command=self.settings_window).pack(side="right")
        ttk.Button(actions, text="Play", style="Maveni.TButton", command=self.launch_game).pack(side="right", padx=10)

    def _drain_events(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "status":
                    self.status.set(str(value))
                elif kind == "manifest":
                    self.manifest = value
                    self.version.set(f"Latest version: {value.get('version', 'unknown')}")
                    self._set_news(value.get("news", ""))
                elif kind == "error":
                    self.status.set("Update failed")
                    messagebox.showerror("Maveni Launcher", str(value))
                elif kind == "done":
                    self.status.set(str(value))
        except queue.Empty:
            pass
        self.after(100, self._drain_events)

    def _set_news(self, text: str) -> None:
        self.news.configure(state="normal")
        self.news.delete("1.0", "end")
        self.news.insert("1.0", text or "No new announcements.")
        self.news.configure(state="disabled")

    def check_updates(self) -> None:
        self.events.put(("status", "Checking for updates..."))
        threading.Thread(target=self._check_updates, daemon=True).start()

    def _check_updates(self) -> None:
        try:
            manifest = download_json(self.config_data["manifest_url"])
            self.events.put(("manifest", manifest))
            self.events.put(("done", f"Update manifest loaded: {manifest.get('version', 'unknown')}"))
        except Exception as exc:
            self.events.put(("error", f"Could not load the update manifest:\n{exc}"))

    def update_client(self) -> None:
        self.events.put(("status", "Downloading client updates..."))
        threading.Thread(target=self._update_client, daemon=True).start()

    def _update_client(self) -> None:
        try:
            manifest = self.manifest or download_json(self.config_data["manifest_url"])
            install_dir = Path(self.config_data["install_dir"])
            install_dir.mkdir(parents=True, exist_ok=True)
            base_url = manifest.get("base_url", "").rstrip("/")
            files = manifest.get("files", [])
            for index, item in enumerate(files, 1):
                relative = Path(item["path"])
                destination = (install_dir / relative).resolve()
                if install_dir.resolve() not in destination.parents:
                    raise ValueError(f"Unsafe update path: {relative}")
                if destination.exists() and sha256(destination).lower() == item["sha256"].lower():
                    continue
                url = item.get("url") or f"{base_url}/{item['path'].replace(os.sep, '/')}"
                destination.parent.mkdir(parents=True, exist_ok=True)
                temporary = destination.with_suffix(destination.suffix + ".download")
                urllib.request.urlretrieve(url, temporary)
                if sha256(temporary).lower() != item["sha256"].lower():
                    temporary.unlink(missing_ok=True)
                    raise ValueError(f"Hash verification failed: {relative}")
                temporary.replace(destination)
                self.events.put(("status", f"Updated {index}/{len(files)}: {relative.name}"))
            self.manifest = manifest
            self.events.put(("done", f"Client is up to date: {manifest.get('version', 'unknown')}"))
        except Exception as exc:
            self.events.put(("error", f"Could not update the client:\n{exc}"))

    def launch_game(self) -> None:
        executable = Path(self.config_data["install_dir"]) / self.config_data["game_exe"]
        if not executable.exists():
            messagebox.showwarning("Maveni Launcher", f"Game executable not found:\n{executable}")
            return
        subprocess.Popen([str(executable), *self.config_data.get("game_args", [])], cwd=executable.parent)
        self.status.set("Game launched")

    def settings_window(self) -> None:
        window = tk.Toplevel(self)
        window.title("Maveni Launcher Settings")
        window.configure(bg="#0b0d0e")
        fields = {}
        for row, (label, key) in enumerate((("Manifest URL", "manifest_url"), ("Install folder", "install_dir"), ("Game executable", "game_exe"))):
            tk.Label(window, text=label, fg="#d8c6a2", bg="#0b0d0e").grid(row=row, column=0, sticky="w", padx=18, pady=10)
            entry = tk.Entry(window, width=64, bg="#171b1a", fg="#f2eee5", insertbackground="#f2eee5")
            entry.insert(0, str(self.config_data[key]))
            entry.grid(row=row, column=1, padx=18, pady=10)
            fields[key] = entry

        def save() -> None:
            for key, entry in fields.items():
                self.config_data[key] = entry.get().strip()
            save_config(self.config_data)
            self.status.set("Settings saved")
            window.destroy()

        ttk.Button(window, text="Save", style="Maveni.TButton", command=save).grid(row=3, column=1, sticky="e", padx=18, pady=18)


if __name__ == "__main__":
    Launcher().mainloop()
