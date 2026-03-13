# VidTools

Video Processing Toolbox — eine GUI-Anwendung fuer Video-Skalierung, Untertitel-Uebersetzung, Transkription, Text-Extraktion und GIF-Erstellung.

> **Herkunft:** Dieses Projekt basiert auf [VidScalerSubtitleAdder](https://github.com/ddumdi11/VidScalerSubtitleAdder) und konsolidiert zusaetzlich [SimpleGifCreator](https://github.com/ddumdi11/SimpleGifCreator) sowie die Uebersetzungs-Engine [smart-srt-translator](https://pypi.org/project/smart-srt-translator/) (als pip-Dependency).

## Funktionen

- **Smart-Skalierung**: Dropdown-Menue mit optimierten Skalierungswerten (automatisch gerade Pixelwerte)
- **Untertitel-Einbettung**: Brennt .srt-Untertitel in einen schwarzen Balken unterhalb des Videos ein
- **Audio-Transkription**: Erstellt automatisch SRT-Dateien aus Video-Audio mit OpenAI Whisper
- **Mehrsprachige Uebersetzung**: Untertitel uebersetzen mit drei Methoden:
  - **OpenAI Translation** (beste Qualitaet): KI-Uebersetzung via smart-srt-translator
  - **Google Translate** (schnell): Kostenlose, schnelle Uebersetzung
  - **Whisper Translation** (lokal): Lokale Uebersetzung, nur nach Englisch
- **Dual Subtitles**: Original-Untertitel oben, Uebersetzung unten – perfekt fuer Sprachlerner
- **Smart Split**: Videos automatisch in konfigurierbare Segmente aufteilen (mit Ueberlappung)
- **Text-Exzerpt**: Konvertiert SRT-Dateien zu gut lesbaren Text-/Markdown-Dokumenten mit KI-Veredelung
- **GIF-Erstellung**: Videos zu optimierten GIFs konvertieren mit Palette-Optimierung

## Voraussetzungen

- **Python 3.10+** (tkinter ist bereits enthalten)
- **FFmpeg** muss installiert und im PATH verfuegbar sein
  - Download: <https://ffmpeg.org/download.html>
  - Alternativ via Chocolatey: `choco install ffmpeg`

## Installation

1. Repository klonen:

   ```bash
   git clone https://github.com/ddumdi11/VidTools.git
   cd VidTools
   ```

2. Virtuelle Umgebung einrichten und aktivieren:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Dependencies installieren:

   ```bash
   pip install -r requirements.txt
   ```

4. Anwendung starten:

   ```bash
   python vidscaler.py
   ```

Oder einfach per Doppelklick: `start.bat`

## Verwendung

Die Anwendung besteht aus zwei Tabs: **Video-Verarbeitung** und **GIF-Erstellung**.

### Tab 1: Video-Verarbeitung

1. **Video auswaehlen** und **"Video analysieren"** klicken – aktuelle Aufloesung wird angezeigt
2. Gewuenschte **Skalierung** aus dem Dropdown-Menue waehlen
3. Optional: **"Audio transkribieren"** klicken, um SRT-Untertitel aus dem Audio zu erstellen
4. Optional: **Uebersetzung** konfigurieren (Quell-/Zielsprache und Methode waehlen)

### Aktions-Buttons

| Button | Beschreibung | Ausgabe-Suffix |
| --- | --- | --- |
| **Video skalieren** | Nur Skalierung, keine Untertitel | `_scaled` |
| **Mit Original-Untertiteln** | Original-SRT im schwarzen Balken unter dem Video | `_subtitled` |
| **Mit Uebersetzung** | Nur uebersetzte Untertitel im schwarzen Balken | `_translated` |
| **Mit Original + Uebersetzung** | Original oben, Uebersetzung unten (Dual Mode) | `_dual_subtitled` |

### Tab 2: GIF-Erstellung

1. **Video laden** – Datei auswaehlen; die Analyse startet automatisch
2. **Einstellungen** waehlen: Breite, FPS, Endlos-Loop
3. **Trimmen**: Start- und Endzeit in Sekunden angeben
4. **GIF erstellen** klicken – Palette-optimiertes GIF wird erstellt

### Weitere Features

- **Smart Split**: Checkbox aktivieren, Teillaenge (1–60 Min) und Ueberlappung (0–30 Sek) einstellen. Das Video wird nach der Verarbeitung automatisch aufgeteilt.
- **Text-Exzerpt**: SRT zu lesbarem Text/Markdown konvertieren – optional mit SpaCy (Satzgrenzen) und OpenAI (KI-Veredelung).

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.
