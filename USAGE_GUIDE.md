# Share COP - Quick Usage Guide

## 🚀 Finding Locations - Three Methods

### Method 1: Type Location Name (Easiest!)
1. In the **Location Name** field, type any location:
   - City: `Berlin`, `New York`, `Tokyo`
   - Full address: `Brandenburg Gate, Berlin, Germany`
   - Landmark: `Eiffel Tower`
   - Building: `10 Downing Street, London`
2. Press **Enter** or click **"Find Location"**
3. ✅ **Automatically**:
   - Coordinates filled
   - Address displayed
   - Map zooms to location
   - Ready to continue!

### Method 2: Click on Map
1. Click **"Pick Location from Map"**
2. Click anywhere on the map
3. ✅ **Automatically**:
   - Coordinates filled
   - Reverse geocoded to address
   - Ready to continue!

### Method 3: Enter Coordinates Manually
1. Type longitude (e.g., `13.4050`)
2. Type latitude (e.g., `52.5200`)
3. ✅ **Automatically**:
   - "Zoom to Location" button enables
   - Address looked up
   - Ready to continue!

## 📍 Location Examples

### Cities
```
Berlin
New York, USA
Tokyo, Japan
London, UK
Paris, France
```

### Landmarks
```
Brandenburg Gate
Statue of Liberty
Eiffel Tower
Sydney Opera House
Big Ben
```

### Full Addresses
```
1600 Pennsylvania Avenue, Washington DC
10 Downing Street, London
Place de la Concorde, Paris
```

### Coordinates
```
13.4050, 52.5200 (Berlin)
-74.0060, 40.7128 (New York)
139.6917, 35.6895 (Tokyo)
```

## 🎯 Complete Workflow

### Step 1: Find Your Location (10 seconds)
```
Type "Berlin" → Press Enter → Done!
✅ Coordinates: 13.4050, 52.5200
✅ Address: Berlin, Deutschland
✅ Map: Zoomed to Berlin
```

### Step 2: Zoom to Desired Scale (Optional)
```
Select zoom level:
- 1:1,000 for building detail
- 1:10,000 for neighborhood
- 1:50,000 for city overview

Click "Zoom to Location"
```

### Step 3: Select Layers (5 seconds)
```
Click layers to include, or:
- "Select All" for everything
- "Select None" to deselect
```

### Step 4: Add COP Metadata (15 seconds)
```
Mission: "Emergency Response 2025"
Classification: "public release"
Releasability: "Public"
```

### Step 5: Export (2 clicks)
```
Click "Browse..." → Select folder
Click "Create COP Package"
Done! ✅
```

## 💡 Pro Tips

### Geocoding Tips
- **Be specific**: `"Berlin, Germany"` better than just `"Berlin"`
- **Use English**: Works best with English location names
- **Wait 1 second**: Between searches (Nominatim rate limit)
- **Try variants**: If not found, try different spelling

### Zoom Tips
- **Auto-zoom**: Geocoding automatically zooms to found location
- **Manual zoom**: Use dropdown to change zoom level
- **Re-zoom**: Click "Zoom to Location" anytime

### Layer Tips
- **Pre-load layers**: Add all layers to project first
- **Visible layers**: Only visible layers shown in map extent
- **Multiple selection**: Ctrl+Click (Windows/Linux) or Cmd+Click (Mac)

### Metadata Tips
- **Mission**: Keep it short and descriptive
- **Classification**: Choose appropriate security level
- **Releasability**: Specify who can access the data

## 🔄 Real-World Examples

### Emergency Response
```
1. Type: "Brandenburg Gate, Berlin"
2. Press Enter → Auto-geocoded & zoomed
3. Select layers: "Emergency Units", "Evacuation Routes"
4. Mission: "Berlin Emergency Response"
5. Classification: "internal"
6. Export → COP_Berlin_Emergency_20251211.zip
```

### Environmental Monitoring
```
1. Type: "Amazon Rainforest, Brazil"
2. Press Enter → Auto-geocoded & zoomed
3. Select layers: "Deforestation Areas", "Protected Zones"
4. Mission: "Forest Monitoring 2025"
5. Classification: "public release"
6. Export → COP_Amazon_Monitoring_20251211.zip
```

### Military Operations
```
1. Click map at operational area
2. Auto-geocoded to address
3. Select layers: "Unit Positions", "Supply Routes"
4. Mission: "Operation Shield"
5. Classification: "classified"
6. Export → COP_Operation_Shield_20251211.zip
```

## ⚙️ Keyboard Shortcuts

- **Enter** (in Location Name): Geocode location
- **Enter** (in coordinates): Validate and enable zoom
- **Tab**: Navigate between fields
- **Ctrl+A**: Select all in text field

## ⚠️ Troubleshooting

### "Could not find location"
**Problem**: Geocoding failed
**Solutions**:
- Check spelling
- Be more specific: Add country/city
- Try English name
- Use coordinates instead

### "Geocoding failed"
**Problem**: No internet or API error
**Solutions**:
- Check internet connection
- Wait 1-2 seconds and retry
- Use "Pick Location from Map" instead

### "Zoom doesn't work"
**Problem**: Invalid coordinates
**Solutions**:
- Check longitude: -180 to 180
- Check latitude: -90 to 90
- Use geocoding to auto-fill

### "No layers to select"
**Problem**: No layers in project
**Solutions**:
- Load layers in QGIS first
- Add at least one layer to project
- Refresh plugin (close and reopen)

## 📊 What You Get

After clicking "Create COP Package":

```
Output/
└── COP_Berlin_Emergency_20251211_143022.zip
    ├── collection.json          (STAC Collection)
    ├── units.json                (STAC Item)
    ├── routes.json               (STAC Item)
    └── assets/
        ├── units.geojson         (Layer data)
        └── routes.geojson        (Layer data)

COP_Berlin_Emergency_20251211_143022.zip.sig (Signature)
```

## 🎓 Learning Path

### Beginner (First Time)
1. Type a city name → Press Enter
2. Select one layer
3. Fill metadata
4. Export

### Intermediate
1. Type full address → Auto-zoom
2. Adjust zoom level
3. Select multiple layers
4. Export with signature

### Advanced
1. Click map for precise location
2. Fine-tune coordinates manually
3. Select layers strategically
4. Use appropriate classification
5. Verify package with signature

## 🆘 Quick Help

**Need coordinates fast?**
→ Type location name, press Enter

**Need to see specific area?**
→ Type location, choose zoom level, zoom

**Need multiple layers?**
→ Use "Select All" or Ctrl+Click

**Need secure package?**
→ Check "Sign package" before export

**Need to verify package?**
→ Check `.sig` file with signature info

---

**Questions?** Check ENHANCED_FEATURES.md for detailed documentation
**Issues?** Check QGIS Python Console for error messages
**Support?** Email luciocol@gmail.com
