# Share Common Operating Picture - Installation Guide

## Quick Installation

### 1. Prerequisites

- QGIS 3.x installed
- Python 3.x (included with QGIS)
- Internet connection (for geocoding)

### 2. Install dggal Library

**Before** installing the plugin, install the required `dggal` library.

#### Method A: QGIS Python Console (Recommended)

1. Open QGIS
2. Go to: **Plugins → Python Console**
3. Run these commands:

```python
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "dggal"])
```

4. You should see "Successfully installed dggal" in the console
5. Restart QGIS

#### Method B: System Terminal

Find your QGIS Python executable and install dggal:

**macOS:**
```bash
/Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install dggal
```

**Linux:**
```bash
# Usually in your PATH as python3
python3 -m pip install dggal
```

**Windows:**
```cmd
# Find QGIS Python (usually in C:\Program Files\QGIS 3.x\apps\Python39\)
"C:\Program Files\QGIS 3.x\apps\Python39\python.exe" -m pip install dggal
```

### 3. Install the Plugin

#### Option A: Manual Installation

1. Download or copy the `share_common_operating_picture` folder
2. Place it in your QGIS plugins directory:

   **macOS:**
   ```
   ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
   ```

   **Linux:**
   ```
   ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
   ```

   **Windows:**
   ```
   %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
   ```

3. Restart QGIS

#### Option B: Using pb_tool (Developers)

If you have `pb_tool` installed:

```bash
cd share_common_operating_picture
pb_tool deploy
```

This will compile UI files and copy everything to the plugins directory.

### 4. Enable the Plugin

1. Open QGIS
2. Go to: **Plugins → Manage and Install Plugins**
3. Click the **"Installed"** tab
4. Find **"Share Common Operating Picture"** in the list
5. Check the checkbox to enable it
6. You should see a new icon in the toolbar

## Verify Installation

### Test dggal

Open QGIS Python Console and run:

```python
import dggal
print("dggal version:", dggal.__version__)
```

If this works, dggal is installed correctly.

### Test the Plugin

1. Click the plugin icon in the toolbar
2. The "Share Common Operating Picture" dialog should open
3. Try clicking "Pick Location from Map"
4. Click anywhere on the map
5. Coordinates should appear in the dialog

## Troubleshooting

### "No module named 'dggal'"

**Problem:** dggal library is not installed in QGIS's Python environment.

**Solution:** Follow step 2 above carefully. Make sure to use QGIS's Python, not your system Python.

**Verify which Python QGIS uses:**
```python
# In QGIS Python Console
import sys
print(sys.executable)
```

Then install dggal using that exact Python executable.

### "Plugin not found" or "Failed to load"

**Problem:** Plugin files are in the wrong location or corrupted.

**Solution:**
1. Check the plugin directory path is correct for your OS
2. Ensure the folder is named exactly: `share_common_operating_picture`
3. Verify all required files are present:
   - `__init__.py`
   - `share_cop.py`
   - `share_cop_dialog.py`
   - `location_picker.py`
   - `metadata.txt`
   - `ui/share_cop_dialog.ui`

### Plugin Icon Not Appearing

**Problem:** Plugin enabled but no toolbar icon.

**Solution:**
1. Go to: **View → Toolbars**
2. Ensure "ShareCOP" toolbar is checked
3. Or access via: **Plugins → Share Common Operating Picture**

### Geocoding Fails

**Problem:** "Geocoding failed" error when clicking "Reverse Geocode Location".

**Solution:**
1. Check your internet connection
2. OpenStreetMap Nominatim is free but rate-limited
3. Wait 1 second between requests
4. For production use, consider using your own Nominatim instance

### Location Picker Not Working

**Problem:** Clicking map doesn't select location.

**Solution:**
1. Make sure you clicked "Pick Location from Map" button first
2. Cursor should change to a crosshair
3. Click on the map canvas (not outside QGIS)
4. If it still doesn't work, check QGIS Python Console for errors

### DGGS Conversion Fails

**Problem:** "DGGS conversion failed" error.

**Possible causes:**
1. dggal not installed correctly - reinstall following step 2
2. Invalid coordinates - check longitude (-180 to 180) and latitude (-90 to 90)
3. Unsupported resolution for selected DGGS system

**Solution:**
- Verify dggal installation: `import dggal` in Python Console
- Check coordinate values are within valid ranges
- Try different DGGS system or resolution level

## Dependencies

The plugin requires:

- **QGIS 3.x** (tested on 3.28+)
- **PyQt5** (included with QGIS)
- **dggal** (must be installed separately)

Optional but used:
- Internet connection for reverse geocoding (OpenStreetMap Nominatim)

## Uninstallation

1. In QGIS: **Plugins → Manage and Install Plugins → Installed**
2. Find "Share Common Operating Picture"
3. Click "Uninstall plugin"

Or manually delete:
```bash
# macOS/Linux
rm -rf ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/share_common_operating_picture

# Windows
rd /s /q %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\share_common_operating_picture
```

## Getting Help

If you encounter issues:

1. **Check QGIS Python Console** for detailed error messages
2. **Verify all dependencies** are installed
3. **Check the README.md** for usage instructions
4. **Email support:** luciocol@gmail.com

## Advanced: Developer Installation

For development with live reloading:

1. Clone/symlink the plugin directory into QGIS plugins folder
2. Install Plugin Reloader plugin from QGIS plugin repository
3. Use Plugin Reloader to reload after code changes
4. No need to restart QGIS for each change

## System Requirements

- **OS:** Windows 10+, macOS 10.14+, Linux (Ubuntu 20.04+)
- **QGIS:** 3.0 or higher (3.28+ recommended)
- **Python:** 3.7+ (included with QGIS)
- **RAM:** 4GB minimum (8GB recommended)
- **Internet:** Required for reverse geocoding

---

**Version:** 1.0.0  
**Last Updated:** December 2025
