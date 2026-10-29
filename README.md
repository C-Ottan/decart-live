# DECART LIVE PRO — REAL-TIME AI VIDEO CLIENT ⚡

Standalone Desktop Application and Python SDK for real-time video transformation using Reactor's **Vidu S2-Editing** model (`reactor/vidu-s2-editing`).

Stream live video from your webcam over WebRTC, apply real-time AI transformations (style transfer, virtual try-on, character replacement, background swap), and hot-swap target references live mid-stream. Direct connection via API key — zero server infrastructure required.

---

## 🛠️ Setup on a New PC

### Prerequisites
- **OS**: Windows 10 / 11 (64-bit)
- **Python**: 3.10 - 3.13 (with `Add Python to PATH` checked during installation)
- **Webcam**: Built-in or USB webcam
- **API Key**: A valid Reactor / Decart API key (`rk_...`)

---

### Quick Start (Clone & Run)

Open **PowerShell** or **Command Prompt** and run:

```powershell
# 1. Clone repository
git clone https://github.com/C-Ottan/decart-live.git
cd decart-live

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
pip install -e .

# 5. Run Desktop Application
python app.py
```

Or double-click `run.bat` after installing requirements.

---

## 🎯 Usage

1. **Enter API Key**: Paste your Reactor API key (`rk_...`) into the top API Key field. It saves locally to your user profile (`~/.decart_live_pro/config.json`).
2. **Select Model & Mode**:
   - `Realtime Video PRO`: Full-scene style transfer.
   - `Live Avatar PRO`: Virtual try-on and character replacement.
   - `Interactive World PRO`: Background replacement while keeping you intact.
3. **Choose Reference Image**: Select a character image, garment, or style reference (or use the included sample).
4. **Start Live**: Click **START LIVE**. The widescreen 952x544 output window appears and transforms your camera feed in real time at up to 30 FPS.
5. **Hot-Swapping**: You can select new reference images or change modes while the stream is active without reconnecting.
6. **Stop**: Click **STOP LIVE** or press `Q` inside the output window.

---

## 📦 Building Standalone Executable (.exe)

To compile a single portable `.exe` that runs without installing Python:

```powershell
python build_exe.py
```

The resulting `DecartLivePro.exe` is placed into `dist/` and copied to your Desktop.
