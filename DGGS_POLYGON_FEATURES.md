# DGGS Polygon Features

## Overview

The Share Common Operating Picture plugin now supports polygon-based DGGS (Discrete Global Grid Systems) representation, allowing you to convert existing polygon features to DGGS zones or create DGGS grids covering specific areas.

## Features

### 1. Select Polygon → DGGS

**Purpose**: Convert existing polygon features from any vector layer into DGGS zones.

**How to Use**:
1. Load polygon layers into your QGIS project
2. Optionally select specific polygon features in a layer
3. Click **"Select Polygon → DGGS"** button in the DGGS section
4. Choose the layer containing polygons you want to convert
5. If no features are selected, you'll be prompted to convert all features
6. The plugin will create a new "DGGS Zones" layer showing:
   - DGGS zone ID for each polygon's centroid
   - Approximate grid cell boundaries (simplified representation)
   - Semi-transparent red fill with labeled zone IDs
   - Area in km²

**Output Layer Fields**:
- `zone_id` - DGGS zone identifier
- `dggs_type` - DGGS coordinate system (rHEALPix, ISEA3H, H3, S2)
- `resolution` - DGGS resolution level (0-20)
- `center_lat` - Centroid latitude
- `center_lon` - Centroid longitude
- `area_km2` - Original polygon area in square kilometers

### 2. Create DGGS Grid

**Purpose**: Generate a regular DGGS grid covering your current map extent or Area of Interest (AOI).

**How to Use**:
1. Set DGGS type and resolution in the DGGS section
2. Zoom to your area of interest or pick a location with AOI
3. Click **"Create DGGS Grid"** button
4. A new "DGGS Grid" layer will be created with:
   - Grid cells covering the extent
   - Each cell labeled with its DGGS zone ID
   - Semi-transparent blue fill
   - Adaptive cell size based on resolution

**Grid Parameters**:
- Cell size automatically adjusts based on DGGS resolution
- Maximum 100 cells to prevent performance issues
- Grid snaps to extent boundaries
- Higher resolution = smaller cells, more precise spatial indexing

**Output Layer Fields**:
- `zone_id` - DGGS zone identifier for cell center
- `dggs_type` - DGGS coordinate system
- `resolution` - DGGS resolution level
- `center_lat` - Cell center latitude
- `center_lon` - Cell center longitude
- `row` - Grid row index
- `col` - Grid column index

### 3. Convert to DGGS (Point-based)

**Purpose**: Convert a single location point to its DGGS zone ID and display center + AOI corners.

**How to Use**:
1. Pick a location or enter coordinates
2. Set DGGS type and resolution
3. Click **"Convert to DGGS"** button
4. Creates a "DGGS Zones" layer with:
   - Center point at picked location
   - 4 corner points marking AOI boundaries
   - Red circles with white-halo labels showing zone IDs

## DGGS Systems Supported

All three methods support these DGGS coordinate systems:

- **rHEALPix**: Hierarchical Equal Area isoLatitude Pixelization
- **ISEA3H**: Icosahedral Snyder Equal Area Aperture 3 Hexagonal
- **H3**: Hexagonal hierarchical geospatial indexing system by Uber
- **S2**: Google's spherical geometry library

## Resolution Levels

- **Range**: 0-20 (higher = more precise, smaller cells)
- **Default**: 12
- **Recommended**:
  - Level 8-10: Regional analysis (large areas)
  - Level 11-13: Local analysis (cities, districts)
  - Level 14-16: Detailed analysis (buildings, parcels)
  - Level 17+: Very fine-grained analysis (sub-meter)

## Use Cases

### Emergency Response
- Convert incident polygons to DGGS zones for spatial indexing
- Create DGGS grids for search area coverage planning
- Standardize location references across agencies

### Military Operations
- Convert operational areas to DGGS zones for coordination
- Generate DGGS grids for mission planning cells
- Enable interoperable location sharing

### Spatial Analysis
- Aggregate data by DGGS zones for consistent spatial bins
- Compare datasets using common DGGS spatial reference
- Perform hierarchical spatial queries at multiple resolutions

## Technical Details

### Coordinate System
- All DGGS layers use **EPSG:4326** (WGS84 lat/lon)
- Input polygons are automatically transformed if needed
- Zone IDs calculated using geometric centroids

### Layer Types
- **Point-based**: Single location with center + AOI corners (5 points)
- **Polygon-based**: Grid cells or simplified representations of input polygons
- **Memory layers**: Not saved to disk unless exported

### Styling
- **Point features**: Red circles with white-halo labels
- **DGGS Zones (from polygons)**: Semi-transparent red fill (#FF6B6B)
- **DGGS Grid**: Semi-transparent blue fill (#6BB3FF)
- All layers include labeled zone IDs for easy identification

### Performance Considerations
- Grid creation limited to 100 cells max to maintain responsiveness
- Large polygons simplified to centroid-based zones
- Cell size adapts automatically based on resolution level

## Workflow Examples

### Example 1: Convert Building Footprints to DGGS
```
1. Load building polygon layer
2. Select buildings of interest
3. Click "Select Polygon → DGGS"
4. Choose building layer
5. Result: Each building assigned a DGGS zone ID
```

### Example 2: Create Search Grid
```
1. Zoom to search area
2. Set resolution to 12 (street-level precision)
3. Click "Create DGGS Grid"
4. Result: Grid covering map extent with labeled cells
```

### Example 3: Convert Operational Area
```
1. Load mission area polygon
2. Set DGGS type to H3 (hexagonal cells)
3. Set resolution to 10
4. Click "Select Polygon → DGGS"
5. Result: Mission area represented as DGGS zone(s)
```

## Integration with COP Export

DGGS zone information is automatically included in STAC exports:
- `cop:dggs_crs` - DGGS coordinate system type
- `cop:dggs_zone_id` - Zone identifier
- Enables spatial discovery and filtering in STAC catalogs

## Limitations

### Current Implementation
- Polygon DGGS zones use simplified grid cells (not true DGGS cell boundaries)
- Zone IDs calculated from centroids only
- Grid generation is extent-based, not feature-aware

### Future Enhancements
- Native DGGS cell geometry generation
- Multi-resolution hierarchical grids
- DGGS-based spatial queries
- Export to native DGGS formats

## Troubleshooting

**No polygon layers found**:
- Ensure vector layers with Polygon geometry are loaded
- Check that layers contain valid geometry

**Grid not visible**:
- Verify resolution level is appropriate for zoom level
- Check layer is enabled in Layers Panel
- Try lower resolution (larger cells)

**Zone IDs not labeled**:
- Enable labels in layer properties if disabled
- Zoom in closer to see small labels
- Adjust label size in layer styling

**Performance issues**:
- Reduce map extent before creating grid
- Use lower resolution (fewer cells)
- Plugin automatically limits to 100 cells

## References

- [DGGS Abstract Specification (OGC)](https://www.ogc.org/standards/dggs)
- [H3 Hexagonal Indexing](https://h3geo.org/)
- [S2 Geometry](https://s2geometry.io/)
- [rHEALPix](https://gimond.github.io/Spatial/discrete-global-grids.html)

## Support

For issues or feature requests related to DGGS polygon features:
1. Check QGIS Python Console for error messages
2. Verify QGIS version compatibility (3.x required)
3. Review DGGS parameters (type, resolution, extent)
4. Consult plugin documentation and examples
