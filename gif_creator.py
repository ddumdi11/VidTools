"""
GIF-Erstellung - Tab fuer VidTools

Erstellt GIFs aus Videoclips mit FFmpeg-Palette-Optimierung.
Portiert von SimpleGifCreator (customtkinter -> tkinter).
"""

import os
import subprocess
import threading
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk, filedialog

# Konstanten
DEFAULT_WIDTH = 480
DEFAULT_FPS = 10
SUPPORTED_FORMATS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".gif")

WIDTH_OPTIONS = ["320", "480", "640", "800", "1024"]
FPS_OPTIONS = ["5", "8", "10", "12", "15", "20", "24", "30"]


class GifCreatorTab(ttk.Frame):
    """GIF-Erstellung als Tab fuer VidTools."""

    def __init__(self, parent):
        super().__init__(parent)

        # State
        self.video_path: Optional[Path] = None
        self.video_duration: float = 0.0
        self.video_width: int = 0
        self.video_height: int = 0

        self._create_widgets()

    def _create_widgets(self):
        """Erstellt alle GUI-Elemente."""

        # === Datei-Auswahl ===
        ttk.Label(self, text="Video fuer GIF auswaehlen:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=(10, 5), padx=10
        )

        file_frame = ttk.Frame(self)
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=(0, 10))

        self.lbl_filename = ttk.Label(file_frame, text="Keine Datei ausgewaehlt", foreground="gray")
        self.lbl_filename.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))

        ttk.Button(file_frame, text="Video laden", command=self._load_video).grid(
            row=0, column=1
        )

        file_frame.columnconfigure(0, weight=1)

        # === Video-Info ===
        self.lbl_video_info = ttk.Label(self, text="", foreground="gray")
        self.lbl_video_info.grid(row=2, column=0, sticky=tk.W, padx=10, pady=(0, 10))

        # === GIF-Einstellungen ===
        ttk.Label(self, text="GIF-Einstellungen:", font=("Arial", 12, "bold")).grid(
            row=3, column=0, sticky=tk.W, padx=10, pady=(0, 5)
        )

        settings_frame = ttk.Frame(self)
        settings_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=10, pady=(0, 10))

        # Breite
        ttk.Label(settings_frame, text="Breite (px):").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.StringVar(value=str(DEFAULT_WIDTH))
        self.combo_width = ttk.Combobox(settings_frame, textvariable=self.width_var,
                                        values=WIDTH_OPTIONS, width=10, state="readonly")
        self.combo_width.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))

        # FPS
        ttk.Label(settings_frame, text="FPS:").grid(row=0, column=2, sticky=tk.W)
        self.fps_var = tk.StringVar(value=str(DEFAULT_FPS))
        self.combo_fps = ttk.Combobox(settings_frame, textvariable=self.fps_var,
                                      values=FPS_OPTIONS, width=10, state="readonly")
        self.combo_fps.grid(row=0, column=3, sticky=tk.W, padx=(5, 20))

        # Loop
        self.var_loop = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Endlos-Loop", variable=self.var_loop).grid(
            row=0, column=4, sticky=tk.W
        )

        # === Trimmen ===
        ttk.Label(self, text="Trimmen:", font=("Arial", 12, "bold")).grid(
            row=5, column=0, sticky=tk.W, padx=10, pady=(0, 5)
        )

        trim_frame = ttk.Frame(self)
        trim_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), padx=10, pady=(0, 10))

        ttk.Label(trim_frame, text="Start (s):").grid(row=0, column=0, sticky=tk.W)
        self.entry_start = ttk.Entry(trim_frame, width=10)
        self.entry_start.insert(0, "0.0")
        self.entry_start.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))

        ttk.Label(trim_frame, text="Ende (s):").grid(row=0, column=2, sticky=tk.W)
        self.entry_end = ttk.Entry(trim_frame, width=10)
        self.entry_end.insert(0, "5.0")
        self.entry_end.grid(row=0, column=3, sticky=tk.W, padx=(5, 20))

        self.lbl_duration = ttk.Label(trim_frame, text="Dauer: 5.0s")
        self.lbl_duration.grid(row=0, column=4, sticky=tk.W)

        # Bind entry changes to update duration
        self.entry_start.bind('<FocusOut>', lambda e: self._update_duration_label())
        self.entry_end.bind('<FocusOut>', lambda e: self._update_duration_label())

        # === Aktions-Buttons ===
        button_frame = ttk.Frame(self)
        button_frame.grid(row=7, column=0, pady=(20, 10), padx=10)

        self.btn_create = ttk.Button(button_frame, text="GIF erstellen",
                                     command=self._create_gif, state="disabled")
        self.btn_create.grid(row=0, column=0, padx=(0, 10))

        # === Status ===
        self.status_var = tk.StringVar(value="Bereit - Lade ein Video um zu starten")
        self.lbl_status = ttk.Label(self, textvariable=self.status_var)
        self.lbl_status.grid(row=8, column=0, sticky=(tk.W, tk.E), padx=10, pady=(10, 0))

        self.progress_bar = ttk.Progressbar(self, mode='determinate')
        self.progress_bar.grid(row=9, column=0, sticky=(tk.W, tk.E), padx=10, pady=(5, 10))

        # Grid-Konfiguration
        self.columnconfigure(0, weight=1)

    def _load_video(self):
        """Oeffnet Dateidialog und laedt Video."""
        filetypes = [
            ("Video-Dateien", "*.mp4 *.mov *.avi *.mkv *.webm"),
            ("Alle Dateien", "*.*")
        ]

        path = filedialog.askopenfilename(
            title="Video auswaehlen",
            filetypes=filetypes
        )

        if path:
            self.video_path = Path(path)
            self._analyze_video()

    def _analyze_video(self):
        """Analysiert das geladene Video mit FFprobe."""
        if not self.video_path:
            return

        self.status_var.set(f"Analysiere: {self.video_path.name}...")
        self.update()

        try:
            # FFprobe fuer Metadaten
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration",
                "-of", "csv=p=0",
                str(self.video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            parts = result.stdout.strip().split(",")

            if len(parts) >= 3:
                self.video_width = int(parts[0])
                self.video_height = int(parts[1])
                self.video_duration = float(parts[2])
            else:
                # Fallback: nur Dauer ermitteln
                cmd_dur = [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "csv=p=0",
                    str(self.video_path)
                ]
                result_dur = subprocess.run(cmd_dur, capture_output=True, text=True,
                                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                self.video_duration = float(result_dur.stdout.strip())
                self.video_width = 0
                self.video_height = 0

            # UI aktualisieren
            self.lbl_filename.config(text=self.video_path.name, foreground="black")
            self.lbl_video_info.config(
                text=f"Aufloesung: {self.video_width}x{self.video_height} | "
                     f"Dauer: {self.video_duration:.1f}s",
                foreground="black"
            )

            # Ende-Zeit auf Video-Dauer setzen (max 10s fuer GIF)
            default_end = min(self.video_duration, 10.0)
            self.entry_end.delete(0, "end")
            self.entry_end.insert(0, f"{default_end:.1f}")
            self._update_duration_label()

            # Button aktivieren
            self.btn_create.config(state="normal")
            self.status_var.set(f"Video geladen: {self.video_path.name}")

        except subprocess.CalledProcessError as e:
            self.status_var.set(f"Fehler: FFprobe fehlgeschlagen - {e}")
        except Exception as e:
            self.status_var.set(f"Fehler beim Analysieren: {e}")

    def _update_duration_label(self):
        """Aktualisiert die Dauer-Anzeige."""
        try:
            start = float(self.entry_start.get())
            end = float(self.entry_end.get())
            duration = max(0, end - start)
            self.lbl_duration.config(text=f"Dauer: {duration:.1f}s")
        except ValueError:
            pass

    def _create_gif(self):
        """Erstellt das GIF mit FFmpeg."""
        if not self.video_path:
            return

        # Parameter sammeln
        try:
            start = float(self.entry_start.get())
            end = float(self.entry_end.get())
            duration = end - start

            if duration <= 0:
                self.status_var.set("Fehler: Ende muss nach Start liegen!")
                return

        except ValueError:
            self.status_var.set("Fehler: Ungueltige Zeit-Werte!")
            return

        width = int(self.combo_width.get())
        fps = int(self.combo_fps.get())

        # Output-Pfad
        output_path = self.video_path.with_stem(f"{self.video_path.stem}_gif").with_suffix(".gif")

        # In separatem Thread ausfuehren
        self.btn_create.config(state="disabled")
        self.progress_bar['value'] = 0

        thread = threading.Thread(
            target=self._run_ffmpeg,
            args=(start, duration, width, fps, output_path),
            daemon=True
        )
        thread.start()

    def _run_ffmpeg(self, start: float, duration: float, width: int, fps: int, output_path: Path):
        """Fuehrt FFmpeg aus (in separatem Thread)."""
        try:
            self.after(0, lambda: self.status_var.set("Erstelle GIF..."))
            self.after(0, lambda: self.progress_bar.configure(value=20))

            # FFmpeg-Befehl mit Palette fuer beste Qualitaet
            vf_filter = f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start),
                "-t", str(duration),
                "-i", str(self.video_path),
                "-vf", vf_filter,
                "-loop", "0" if self.var_loop.get() else "-1",
                str(output_path)
            ]

            self.after(0, lambda: self.progress_bar.configure(value=50))

            result = subprocess.run(cmd, capture_output=True, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

            self.after(0, lambda: self.progress_bar.configure(value=100))

            if result.returncode == 0 and output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                self.after(0, lambda: self.status_var.set(
                    f"GIF erstellt: {output_path.name} ({size_str})"
                ))
            else:
                error_msg = result.stderr[:200] if result.stderr else "Unbekannter Fehler"
                self.after(0, lambda: self.status_var.set(
                    f"FFmpeg-Fehler: {error_msg}"
                ))

        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Fehler: {e}"))

        finally:
            self.after(0, lambda: self.btn_create.config(state="normal"))
