<p align="center">
  <picture>
    <img src="docs/assetorganizer banner.webp" alt="Asset Organizer" width="720">
  </picture>
</p>

<p align="center">
  <strong>Batch-process Adobe files into a searchable, archived asset library.</strong>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-Windows-blue?logo=windows&logoColor=white" alt="Windows"></a>
  <a href="#"><img src="https://img.shields.io/badge/Adobe-Photoshop-blueviolet?logo=adobephotoshop&logoColor=white" alt="Photoshop"></a>
  <a href="#"><img src="https://img.shields.io/badge/Adobe-Illustrator-orange?logo=adobeillustrator&logoColor=white" alt="Illustrator"></a>
  <a href="#"><img src="https://img.shields.io/badge/release-v1.2.0-brightgreen" alt="Release 1.2.0"></a>
  <a href="https://github.com/mh3nj/evoury"><img src="https://img.shields.io/badge/Evoury-DAM-ff69b4" alt="Evoury DAM"></a>
</p>

---

Asset Organizer processes PSD, AI, and EPS files one at a time. For each file it exports a preview, asks for a descriptive name, creates an AVIF thumbnail, and packages everything into a verified RAR archive.

The goal is simple: replace generic filenames like `Logo_Final.ai` with searchable names like `green white black letter logo minimal corporate shadow.ai`. Once files are named this way, any filesystem search tool (Windows Search, Everything, grep) finds them immediately — no database, no tags, no proprietary catalog.

Asset Organizer is the ingestion pipeline for [Evoury](https://github.com/mh3nj/evoury), a full-featured digital asset management platform. Evoury provides the catalog and grid interface; Asset Organizer prepares the assets for it.

---

## Pipeline

Each asset goes through these stages in order:

| # | Stage | Description |
|---|-------|-------------|
| 1 | Open | Opens the file in Adobe. Closes any previous document first. |
| 2 | Export PNG | Renders a full-resolution PNG preview via Adobe ExtendScript. |
| 3 | Convert AVIF | Converts the PNG to AVIF. Produces a full preview and a 400×400 thumbnail. |
| 4 | Name prompt | Shows the preview and waits for you to type a name. |
| 5 | Hide layers | Hides all visible layers for a clean archive copy. |
| 6 | Save | Saves the document in Adobe. |
| 7 | Close tab | Closes the document tab. Saves changes, no dialog. |
| 8 | Rename | Renames the source file, AVIF, and thumbnail to the chosen name. |
| 9 | Archive | Creates a best-compression RAR with the source and AVIF inside. |
| 10 | Verify | Tests RAR integrity. |
| 11 | Cleanup | Removes the loose source file. The AVIF stays for indexing. |

The queue is single-threaded. One file is processed completely before the next starts. Only one Adobe document is ever open at a time.

---

## Features

- **One-by-one processing.** Never opens more than one Adobe document at once. Previous document is always closed before the next opens.
- **Regenerate preview.** Edit the document in Adobe while the naming prompt is showing, then click "Regen Preview." The document is saved, re-exported, and the preview updates without breaking the pipeline.
- **Resume failed.** If the app crashes, "Resume Failed" re-queues any incomplete jobs from the last session. Source files of incomplete jobs are always at their original path — they only get renamed after full success.
- **Session persistence.** Progress saves to `data/session.json` after every job. On restart, the app can recover where it left off.
- **Disk space guard.** Won't start if free space drops below the configured minimum. Pauses and waits, or stops if you cancel the queue.
- **Error recovery.** Adobe errors (scratch disk full, out of memory, not responding) trigger an automatic restart and retry.
- **Name history.** Arrow keys cycle through previously used names.
- **Dark/light theme.** Toggle via the Theme button.
- **AVIF with thumbnails.** Every asset gets a full-size AVIF preview and a small `.thumb.avif` for grid views.
- **Verified RAR archives.** Best compression, solid archive, tested after creation.

---

## Screenshots

<table>
  <tr>
    <td><img src="docs/screenshots/dark main window.webp" loading="lazy"></td>
    <td><img src="docs/screenshots/light main window.png.webp" loading="lazy"></td>
  </tr>
</table>

---

## Demo

[assetOrganizer.demo.webm](https://github.com/user-attachments/assets/8b1f5923-c615-49a4-8fd1-27f8e6403c7a)


---

## Requirements

### Runtime

| Component | Notes |
|-----------|-------|
| **Windows 10+** | COM interop is Windows-only |
| **Adobe Photoshop CS6+** or **Illustrator CS6+** | Used for opening, exporting, and layer operations |
| **WinRAR** (`Rar.exe`) | Required for archive creation |

### Development (running from source)

| Dependency | Version |
|-----------|---------|
| Python | 3.11+ |
| `pywin32` | latest |
| `Pillow` | 10.0+ |
| `pillow-avif-plugin` | latest |

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Installation

Asset Organizer runs on Windows only (it depends on Adobe COM interop). The setup scripts and manual steps below all assume a Windows environment.

### First run: configuration

Every setup path below needs one manual step the first time:

```bash
copy config.example.py config.py
```

`config.example.py` is a template — the app never imports it. It reads `config.py`, so without that copy the app won't start.

You usually don't need to edit anything afterwards: Adobe and WinRAR paths are **auto-detected** from `C:\Program Files`. Only touch `config.py` if you want to force a specific Adobe version or override defaults. `config.py` is gitignored; only ever push `config.example.py`.

### Prebuilt executable (recommended)

Download the latest `AssetOrganizer.exe` from the [Releases page](https://github.com/mh3nj/assetOrganizer/releases/tag/organizer). Extract the archive and run the executable. No Python or dependencies required — everything is bundled.

### Run from source with setup script

The repository includes two scripts that create a virtual environment, install dependencies, and launch the app:

**Windows:**
```batch
setup.bat
```

**Linux / macOS** (for development or testing — Adobe COM is Windows-only, so the pipeline itself will not work):
```bash
chmod +x setup.sh
./setup.sh
```

Each script checks for Python 3.11+, creates a `.venv` if one does not exist, installs `requirements.txt`, and runs `main.py`.

### Run from source manually

```bash
# Clone the repository
git clone https://github.com/YOUR_USER/AssetOrganizer.git
cd AssetOrganizer

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create config.py from the template (one-time; paths auto-detect)
copy config.example.py config.py

# Launch the application
python main.py
```

### Build a standalone executable

```bash
pip install pyinstaller
python -m PyInstaller AssetOrganizer.spec --noconfirm
```

The executable will be at `dist/AssetOrganizer/AssetOrganizer.exe`. It includes all dependencies and the `scripts/` folder containing Adobe ExtendScript files.

> **Always build from the `.spec` file.** Running `pyinstaller main.py` regenerates the spec with no data files and silently drops the `scripts/` folder, which makes every job fail with "Missing JSX".

---

## Usage

1. Launch the application.
2. Click **Select Folder** and choose a folder containing PSD, AI, or EPS files. Subdirectories are scanned recursively.
3. Click **Start Queue**.
4. For each asset:
   - A preview appears.
   - Type a descriptive name and press Enter or click **Confirm**.
   - Optionally, edit the document in Adobe and click **Regen Preview** before confirming.
5. The app creates a `.rar` archive next to the source file and removes the loose source.

### Controls

| Control | Action |
|---------|--------|
| **Select Folder** | Scan a folder recursively for Adobe source files |
| **Resume Failed** | Re-queue incomplete jobs from the last session |
| **Start Queue** | Begin sequential processing |
| **Pause / Resume** | Pause or resume between jobs |
| **Regen Preview** | Re-export the preview from the currently open document (during naming only) |
| **Confirm** | Accept the typed name and continue |
| **Theme** | Toggle dark and light themes |

### Regenerating a preview

1. Wait for the naming prompt.
2. Switch to Adobe Photoshop or Illustrator.
3. Make your edits.
4. Switch back to Asset Organizer.
5. Click **Regen Preview**.
6. The preview updates. Type the name and continue.

The pipeline stays at the naming step the entire time. Nothing breaks.

### Resuming after a crash

1. Launch Asset Organizer.
2. Click **Resume Failed**.
3. Incomplete jobs from the last session are restored.
4. Click **Start Queue** to process them.

Only jobs that never reached "done" are recovered. Jobs whose source file was already deleted are skipped.

---

## Configuration

First-time setup: `copy config.example.py config.py` (the app only reads `config.py` — `config.example.py` is just a template you can push to GitHub).

All Adobe/WinRAR paths auto-detect from `C:\Program Files`, so most people never touch this file. Edit `config.py` if you need to override the defaults:

| Setting | Default | Description |
|---------|---------|-------------|
| `PREVIEW_WIDTH` | 2000 | Max preview width in pixels |
| `PREVIEW_HEIGHT` | 2000 | Max preview height in pixels |
| `THUMB_WIDTH` | 400 | Thumbnail width in pixels |
| `THUMB_HEIGHT` | 400 | Thumbnail height in pixels |
| `AVIF_QUALITY` | 90 | AVIF encode quality (0–100) |
| `AVIF_SPEED` | 6 | AVIF encoding speed (0=slowest/best, 10=fastest) |
| `THUMB_QUALITY` | 70 | Thumbnail AVIF quality |
| `MINIMUM_FREE_SPACE_GB` | 1 | Disk space safety threshold |
| `ADOBE_STARTUP_WAIT` | 20 | Seconds to wait for Adobe to launch |
| `ADOBE_RECOVERY_WAIT` | 20 | Seconds to wait after restarting Adobe |
| `DOCUMENT_TIMEOUT` | 60 | Seconds to wait for a document to finish opening |
| `MAX_RETRIES` | 2 | Number of automatic retries on recoverable errors |

---

## Supported formats

| Format | Open | Export | Hide Layers | Save | Close |
|--------|------|--------|-------------|------|-------|
| `.psd` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `.ai` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `.eps` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `.indd` | — | — | — | — | — |

---

## Evoury integration

[Evoury](https://github.com/mh3nj/evoury) is a full-featured digital asset management (DAM) platform. It provides an asset grid, catalog browsing, and search across your organized library.

Asset Organizer is the ingestion pipeline for Evoury. Together they form a complete workflow:

```
Source files (PSD/AI/EPS)
       │
       ▼
Asset Organizer ────→ Organized archives (RAR + AVIF)
(ingestion pipeline)        │
                            ▼
                       Evoury DAM
                   (catalog and management)
```

You can use Asset Organizer without Evoury. It produces standard files that work with any file manager or search tool.

---

## Architecture

```
main.py                  Entry point — wires all components
├── config.py            Global configuration (local-only, gitignored)
├── config.example.py    Sanitized config template (push to GitHub)
├── logger.py            File, console, and UI logging
├── requirements_check.py   Environment verification
│
├── scanner.py           Recursive folder scanning
├── queue.py             Sequential job queue (single-threaded)
├── processor.py         Main pipeline orchestrator
├── job.py               Job model and status enum
│
├── photoshop.py         Photoshop COM controller
├── illustrator.py       Illustrator COM controller
├── jsx_bridge.py        Loads and executes ExtendScript (.jsx)
├── naming.py            Thread-safe name prompt
├── preview.py           PNG to AVIF conversion
├── filename.py          Name normalization and deduplication
│
├── archive.py           RAR creation via Rar.exe
├── storage.py           Disk space monitoring
├── cleanup.py           Post-archive source deletion
├── session.py           Session persistence (data/session.json)
├── adobe_recovery.py    Error classification and recovery
│
├── ui.py                Tkinter GUI
│
└── scripts/             Adobe ExtendScript files
    ├── photoshop_export.jsx
    └── illustrator_export.jsx
```

### Threading

| Thread | Responsibility |
|--------|---------------|
| **UI thread** | Tkinter main loop. Polls for name requests and progress every 500ms. |
| **Worker thread** | Runs the queue. Opens Adobe documents, calls COM, blocks on name input. |

Communication uses `threading.Event`. The UI sets the event when a name is submitted or a regeneration is requested. The worker wakes, reads the state, and continues.

### Adobe COM lifecycle

- The Adobe application starts once when the queue begins.
- Before each file, all existing documents are closed.
- One document opens, gets processed, then closes.
- On a recoverable error, the Adobe application restarts.
- When the queue finishes, the application shuts down.

---

## FAQ

**Can I use this without Evoury?**  
Yes. Asset Organizer produces organized RAR and AVIF files that work with any file manager or search tool.

**Does it modify the original files?**  
The source file is renamed and archived into a RAR. After the archive is verified, the loose original is deleted. Keep backups of anything irreplaceable.

**Can I rename assets after they are archived?**  
Not through Asset Organizer. You would need to extract the RAR, rename manually, and re-archive.

**Why does EPS sometimes show a save dialog?**  
Illustrator may prompt for EPS export options. See [Known Limitations](issues.md#eps-save-dialog-illustrator) for the workaround.

**Can I process 1000 files at once?**  
One at a time, sequentially. The queue is single-threaded by design because Adobe COM is single-threaded.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built as organizer for <a href="https://github.com/mh3nj/evoury">Evoury</a></sub>
</p>
