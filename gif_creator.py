"""
GIF-Erstellung - Tab fuer VidTools

Erstellt GIFs aus Videoclips mit FFmpeg-Palette-Optimierung.
Portiert von SimpleGifCreator (customtkinter -> tkinter).
"""

import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk, filedialog

from video_processor import VideoProcessor, SUBPROCESS_FLAGS, FFMPEG_TIMEOUT_SHORT, FFMPEG_TIMEOUT_LONG

# Konstanten
DEFAULT_WIDTH = 480
DEFAULT_FPS = 10

WIDTH_OPTIONS = ["320", "480", "640", "800", "1024"]
FPS_OPTIONS = ["5", "8", "10", "12", "15", "20", "24", "30"]


def _resolve_ffprobe(ffmpeg_path: str) -> str:
    """Leitet ffprobe-Pfad aus dem ffmpeg-Pfad ab, respektiert FFMPEG_PATH.

    Strategie: Wenn FFMPEG_PATH gesetzt ist, ffprobe im selben Verzeichnis suchen.
    Sonst shutil.which, sonst Fallback 'ffprobe'.
    """
    ffmpeg_env = os.getenv("FFMPEG_PATH")
    if ffmpeg_env:
        env_path = Path(ffmpeg_env)
        # FFMPEG_PATH zeigt auf Verzeichnis
        if env_path.is_dir():
            candidate = env_path / "ffprobe"
            if candidate.exists():
                return str(candidate)
            candidate = env_path / "ffprobe.exe"
            if candidate.exists():
                return str(candidate)
        # FFMPEG_PATH zeigt auf ffmpeg-Binary -> ffprobe im selben Ordner
        elif env_path.is_file():
            parent = env_path.parent
            for name in ("ffprobe", "ffprobe.exe"):
                candidate = parent / name
                if candidate.exists():
                    return str(candidate)

    # Aus aufgeloestem ffmpeg-Pfad ableiten
    ffmpeg_dir = Path(ffmpeg_path).parent
    for name in ("ffprobe", "ffprobe.exe"):
        candidate = ffmpeg_dir / name
        if candidate.exists():
            return str(candidate)

    # Fallback: shutil.which
    found = shutil.which('ffprobe')
    return found if found else 'ffprobe'


class GifCreatorTab(ttk.Frame):
    """GIF-Erstellung als Tab fuer VidTools."""

    def __init__(self, parent):
        super().__init__(parent)

        # State
        self.video_path: Optional[Path] = None
        self.video_duration: float = 0.0
        self.video_width: int = 0
        self.video_height: int = 0

        # Resolved binary paths (reuse VideoProcessor's robust lookup)
        processor = VideoProcessor()
        self._ffmpeg = processor.ffmpeg_path
        self._ffprobe = _resolve_ffprobe(self._ffmpeg)

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
            self.status_var.set(f"Analysiere: {self.video_path.name}...")
            # Analyse im Hintergrund-Thread, UI bleibt responsiv
            thread = threading.Thread(target=self._analyze_video_thread,
                                      args=(self.video_path,), daemon=True)
            thread.start()

    def _analyze_video_thread(self, video_path: Path):
        """Analysiert das geladene Video mit FFprobe (Hintergrund-Thread)."""
        try:
            cmd = [
                self._ffprobe, "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration",
                "-of", "csv=p=0",
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True,
                                    timeout=FFMPEG_TIMEOUT_SHORT, **SUBPROCESS_FLAGS)
            parts = result.stdout.strip().split(",")

            width = 0
            height = 0
            duration = None
            if len(parts) >= 3:
                width = int(parts[0])
                height = int(parts[1])
                try:
                    duration = float(parts[2])
                except (ValueError, TypeError):
                    pass  # "N/A" o.ae. — Fallback auf format=duration

            if duration is None:
                # Fallback: nur Dauer ermitteln
                cmd_dur = [
                    self._ffprobe, "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "csv=p=0",
                    str(video_path)
                ]
                result_dur = subprocess.run(cmd_dur, capture_output=True, text=True,
                                            timeout=FFMPEG_TIMEOUT_SHORT, **SUBPROCESS_FLAGS)
                raw = result_dur.stdout.strip()
                if not raw:
                    raise RuntimeError(
                        f"FFprobe lieferte keine Dauer fuer {video_path.name}. "
                        f"Kommando: {' '.join(cmd_dur)}, stderr: {result_dur.stderr[:200]}")
                try:
                    duration = float(raw)
                except ValueError:
                    raise RuntimeError(
                        f"FFprobe-Ausgabe nicht parsebar: '{raw}'. "
                        f"Kommando: {' '.join(cmd_dur)}, stderr: {result_dur.stderr[:200]}")

            # UI-Update im Hauptthread
            self.after(0, self._on_analysis_success, video_path, width, height, duration)

        except subprocess.TimeoutExpired:
            self.after(0, lambda: self.status_var.set(
                f"Fehler: FFprobe-Timeout nach {FFMPEG_TIMEOUT_SHORT}s"))
        except subprocess.CalledProcessError as e:
            error_msg = str(e)
            self.after(0, lambda msg=error_msg: self.status_var.set(
                f"Fehler: FFprobe fehlgeschlagen - {msg}"))
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda msg=error_msg: self.status_var.set(
                f"Fehler beim Analysieren: {msg}"))

    def _on_analysis_success(self, video_path: Path, width: int, height: int, duration: float):
        """UI-Update nach erfolgreicher Analyse (Hauptthread)."""
        # Race-Guard: Wenn inzwischen ein anderes Video gewaehlt wurde, verwerfen
        if self.video_path != video_path:
            return
        self.video_width = width
        self.video_height = height
        self.video_duration = duration

        self.lbl_filename.config(text=video_path.name, foreground="black")
        self.lbl_video_info.config(
            text=f"Aufloesung: {width}x{height} | Dauer: {duration:.1f}s",
            foreground="black"
        )

        # Ende-Zeit auf Video-Dauer setzen (max 10s fuer GIF)
        default_end = min(duration, 10.0)
        self.entry_end.delete(0, "end")
        self.entry_end.insert(0, f"{default_end:.1f}")
        self._update_duration_label()

        self.btn_create.config(state="normal")
        self.status_var.set(f"Video geladen: {video_path.name}")

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

        # Parameter sammeln und validieren
        try:
            start = float(self.entry_start.get())
            end = float(self.entry_end.get())
        except ValueError:
            self.status_var.set("Fehler: Ungueltige Zeit-Werte!")
            return

        if start < 0:
            self.status_var.set("Fehler: Start darf nicht negativ sein!")
            return
        if end < 0:
            self.status_var.set("Fehler: Ende darf nicht negativ sein!")
            return
        if self.video_duration > 0 and end > self.video_duration:
            self.status_var.set("Fehler: Ende liegt ausserhalb der Video-Dauer!")
            return

        duration = end - start
        if duration <= 0:
            self.status_var.set("Fehler: Ende muss nach Start liegen!")
            return

        width = int(self.combo_width.get())
        fps = int(self.combo_fps.get())
        loop = self.var_loop.get()
        video_path = self.video_path

        # Output-Pfad
        output_path = video_path.with_stem(f"{video_path.stem}_gif").with_suffix(".gif")

        # In separatem Thread ausfuehren
        self.btn_create.config(state="disabled")
        self.progress_bar['value'] = 0

        thread = threading.Thread(
            target=self._run_ffmpeg,
            args=(start, duration, width, fps, output_path, loop, video_path),
            daemon=True
        )
        thread.start()

    def _run_ffmpeg(self, start: float, duration: float, width: int, fps: int,
                    output_path: Path, loop: bool, video_path: Path):
        """Fuehrt FFmpeg aus (in separatem Thread). Alle Werte als Parameter, kein tkinter-Zugriff."""
        try:
            self.after(0, lambda: self.status_var.set("Erstelle GIF..."))
            self.after(0, lambda: self.progress_bar.configure(value=20))

            # FFmpeg-Befehl mit Palette fuer beste Qualitaet
            vf_filter = f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"

            cmd = [
                self._ffmpeg, "-y",
                "-ss", str(start),
                "-t", str(duration),
                "-i", str(video_path),
                "-vf", vf_filter,
                "-loop", "0" if loop else "-1",
                str(output_path)
            ]

            self.after(0, lambda: self.progress_bar.configure(value=50))

            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=FFMPEG_TIMEOUT_LONG, **SUBPROCESS_FLAGS)

            self.after(0, lambda: self.progress_bar.configure(value=100))

            if result.returncode == 0 and output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                self.after(0, lambda: self.status_var.set(
                    f"GIF erstellt: {output_path.name} ({size_str})"
                ))
            else:
                error_msg = result.stderr[:200] if result.stderr else "Unbekannter Fehler"
                self.after(0, lambda msg=error_msg: self.status_var.set(
                    f"FFmpeg-Fehler: {msg}"
                ))

        except subprocess.TimeoutExpired:
            self.after(0, lambda: self.status_var.set(
                f"Fehler: FFmpeg-Timeout nach {FFMPEG_TIMEOUT_LONG}s"))
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda msg=error_msg: self.status_var.set(f"Fehler: {msg}"))

        finally:
            self.after(0, lambda: self.btn_create.config(state="normal"))
