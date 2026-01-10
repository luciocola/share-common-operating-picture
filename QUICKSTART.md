# Share Common Operating Picture - Quick Start

## 1-Minute Setup

### Install dggal (Required!)

Open QGIS Python Console and run:
```python
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "dggal"])
```

Restart QGIS after installation.

### Enable Plugin

1. **Plugins → Manage and Install Plugins → Installed**
2. Check **"Share Common Operating Picture"**
3. Look for the icon in the toolbar

## Quick Usage

### Pick a Location

1. Click the plugin icon
2. Click **"Pick Location from Map"**
3. Click anywhere on the map
4. Coordinates appear automatically

### Get Address

Click **"Reverse Geocode Location"** to get the address

### Convert to DGGS

1. Select DGGS type (rHEALPix, ISEA3H, H3, S2)
2. Set resolution (0-20, default: 12)
3. Click **"Convert to DGGS Zone ID"**
4. See results in the bottom panel

## Example Workflow

```
1. Open plugin
2. Pick location: Berlin, Germany
3. Reverse geocode → "Berlin, 10178, Deutschland"
4. Select: rHEALPix, Resolution: 12
5. Convert → Zone ID: N3314...
6. Copy JSON output from Results panel
```

## Common Issues

**"dggal not found"**: Install dggal first (see above)

**Geocoding fails**: Check internet connection, wait 1 second between requests

**Pick location not working**: Click the button first, then click the map

## DGGS Systems

- **rHEALPix**: Good for global data, equal area cells
- **ISEA3H**: Hexagonal cells, good for analysis
- **H3**: Uber's system, optimized for transportation
- **S2**: Google's system, efficient for spatial indexing

## Output Format

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [lon, lat]
  },
  "properties": {
    "dggs_crs": "rHEALPix",
    "dggs_zone_id": "N3314...",
    "resolution": 12,
    "address": "Full address"
  }
}
```

## Next Steps

- Read full documentation in README.md
- Check INSTALLATION.md for troubleshooting
- Experiment with different DGGS systems and resolutions

---

**Need Help?** luciocol@gmail.com
