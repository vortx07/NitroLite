# 🚀 NitroLite

<p align="center">
  <img src="assets/icon.ico" width="96" height="96" alt="NitroLite Icon">
</p>

<p align="center">
  <b>Ultra-Lightweight Hardware Dashboard & Fan Controller for Acer Nitro & Predator Laptops</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?style=for-the-badge&logo=windows" alt="Windows">
  <img src="https://img.shields.io/badge/RAM%20Usage-~28%20MB-success?style=for-the-badge" alt="RAM Usage">
  <img src="https://img.shields.io/badge/Official%20NitroSense-~600%20MB-critical?style=for-the-badge" alt="Official RAM">
  <img src="https://img.shields.io/badge/RAM%20Reduction-95%25-brightgreen?style=for-the-badge" alt="RAM Reduction">
  <img src="https://img.shields.io/github/v/release/vortx07/NitroLite?style=for-the-badge&color=orange" alt="Release">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
</p>

---

## 💡 Why NitroLite?

Official **Acer NitroSense** runs on Chromium/Electron, spawning multiple helper processes, telemetry modules, and background services that collectively swallow **550 MB to 850 MB of system RAM** just sitting in the background.

**NitroLite** completely replaces the heavy frontend with a native, responsive desktop application using **only ~25–35 MB of RAM**—a **95% memory reduction**—giving that precious memory back to your games and applications.

---

## ⚡ Memory Comparison

```
Official NitroSense (Electron): [████████████████████████████████] ~580 MB
NitroLite (Native):            [█]                               ~28 MB (95% Less RAM!)
```

| Metric | Official NitroSense | NitroLite |
| :--- | :--- | :--- |
| **RAM Consumption** | **~560 MB – 850 MB** (4+ Electron processes) | **~25 MB – 35 MB** (Single process) |
| **Startup Delay** | 5 – 9 seconds | **Instant (< 0.5s)** |
| **Background CPU Usage** | Periodic Chromium re-render spikes | **< 0.1%** (sleeps silently in tray) |
| **Framework** | Heavy Chromium / Node.js / WebViews | Lightweight Native GUI (CustomTkinter) |

---

## ✨ Features

- 📊 **Real-Time Telemetry Dashboard**:
  - **CPU Monitoring**: Live thermals (°C) with dynamic green/yellow/red warning indicators, clock frequency (MHz), fan RPM, and load percentage.
  - **GPU Monitoring**: Dedicated NVIDIA RTX thermals (°C), clock frequency (MHz), fan RPM, and load percentage.
  - **Memory & System**: Live RAM utilization (GB / %) and ambient chassis temperatures.

- ⚡ **Instant Performance Profiles**:
  - 🌿 **Eco**: Energy saving, cooler thermals, ideal for battery longevity.
  - 🤫 **Quiet**: Whisper-quiet fan curves for study, office work, and late-night browsing.
  - ⚖️ **Balanced**: Everyday optimal performance curve.
  - 🚀 **Gaming / Extreme**: Unlocked clock speeds, full GPU wattage, and aggressive cooling response.

- 🎛️ **Full Fan Control**:
  - 🔄 **Auto**: Handled dynamically by official BIOS thermal curves.
  - 🚀 **Max (100%)**: Instant full-blast dual fans for demanding gaming or render workloads.
  - 🎚️ **Custom Sliders**: Independently adjust CPU and GPU fan speeds from 0% to 100%.

- 🎮 **Gaming & Hardware Toggles**:
  - 🪟 **Windows Key Lock**: Disables the Windows key to prevent accidental alt-tabs in intense games.
  - 🖥️ **LCD Overdrive**: Lowers panel response times for competitive FPS motion clarity.
  - 💡 **Backlight 30s Timeout**: Toggles automatic keyboard illumination sleep.

- 📥 **System Tray Companion**:
  - Minimizes cleanly to the Windows taskbar tray when closed.
  - Right-click tray menu for quick mode switching (`Quiet`, `Balanced`, `Gaming`, `Eco`) and fan toggles without needing to open the full dashboard.
  - **Adaptive Polling**: Slows refresh rate to 8–10s when minimized to conserve CPU cycles.

---

## 🔒 Safety & Hardware Protection

NitroLite is **100% hardware safe**:

1. **Official ACPI Driver Bridge**: NitroLite does not write dangerous raw bytes to the Embedded Controller (EC). It speaks directly to the local Windows driver service (`AcerAgentService` on localhost port `46933`) via Acer's authenticated challenge-response protocol.
2. **Motherboard Thermal Failsafes**: Hardware-level BIOS thermal protections remain completely active. Even if NitroLite is closed or suspended, your laptop's firmware automatically takes over if temperatures rise.
3. **Manufacturer Limits**: Fan speeds and operating modes remain strictly within Acer’s factory-certified thresholds.

---

## 🚀 Getting Started

### Option 1: Standalone Executable (Recommended)

No Python or dependencies required!
1. Download or locate `NitroLite.exe`.
2. Double-click **`NitroLite.exe`** to launch.
3. *(Optional)* Run `install_autostart.bat` to have NitroLite start silently in your system tray on Windows boot.

### Option 2: Run from Source

```bash
# Clone the repository
git clone https://github.com/vortx07/NitroLite.git
cd NitroLite

# Install dependencies
pip install customtkinter pystray psutil pillow

# Run the app
python main.py

# Or start directly in system tray
python main.py --tray
```

---

## 🛠️ Building the Standalone `.exe`

To build the executable yourself using PyInstaller:

```bash
python build_exe.py
```
The output binary will be created at `NitroLite.exe`.

---

## 💻 Tested & Supported Models

- **Acer Nitro V 15** (ANV15-51, ANV15-52, ANV15-41, etc.)
- **Acer Nitro 5** (AN515-58, AN517-55, etc.)
- **Acer Nitro 16 / 17** (AN16, AN17 series)
- **Acer Predator Helios & Triton** (with AcerAgentService / PredatorService driver)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
Feel free to contribute, open issues, or submit pull requests!
