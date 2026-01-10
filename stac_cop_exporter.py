"""
STAC COP Exporter - Core export functionality
"""
import hashlib
import json
import os
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from qgis.core import (
    QgsVectorLayer,
    QgsRasterLayer,
    QgsVectorFileWriter,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsRasterFileWriter,
    QgsRasterPipe,
    QgsRectangle
)
try:
    from osgeo import gdal
    GDAL_AVAILABLE = True
except ImportError:
    GDAL_AVAILABLE = False


class STACCOPExporter:
    """Handles export of QGIS layers to STAC format with COP extension"""

    def __init__(self, output_dir, map_canvas=None):
        """
        Initialize exporter
        
        Args:
            output_dir: Directory where STAC files will be exported
            map_canvas: Optional QgsMapCanvas to use for extent clipping
        """
        self.output_dir = output_dir
        self.map_canvas = map_canvas
        self.exported_items = []
        
        # Create STAC collection directory
        self.stac_dir = os.path.join(output_dir, 'stac_cop_export')
        os.makedirs(self.stac_dir, exist_ok=True)
        
        # Create assets directory
        self.assets_dir = os.path.join(self.stac_dir, 'assets')
        os.makedirs(self.assets_dir, exist_ok=True)
        
        # Clip extent for exports
        self.clip_extent = None
        self.clip_crs = None
    
    def set_clip_extent(self, extent, crs):
        """Set extent for clipping exported layers"""
        self.clip_extent = extent
        self.clip_crs = crs

    def export_layer(self, layer, cop_metadata):
        """
        Export a single QGIS layer to STAC COP format
        
        Args:
            layer: QgsMapLayer to export
            cop_metadata: Dictionary containing COP metadata fields
        """
        layer_name = layer.name()
        # Generate UUID4 for STAC item ID
        layer_id = str(uuid.uuid4())
        # Use sanitized name for file naming
        file_name = self.sanitize_id(layer_name)
        
        # Export layer data
        asset_path = self.export_layer_data(layer, file_name)
        
        # Create STAC Item
        stac_item = self.create_stac_item(layer, layer_id, asset_path, cop_metadata, file_name)
        
        # Store file_name for collection link generation
        stac_item['_file_name'] = file_name
        
        # Save STAC Item JSON using sanitized filename
        item_path = os.path.join(self.stac_dir, f'{file_name}.json')
        
        # Remove internal _file_name before saving
        item_to_save = {k: v for k, v in stac_item.items() if k != '_file_name'}
        with open(item_path, 'w', encoding='utf-8') as f:
            json.dump(item_to_save, f, indent=2)
        
        self.exported_items.append(stac_item)
        return item_path

    def export_layer_data(self, layer, layer_id):
        """
        Export layer data to file
        
        Args:
            layer: QgsMapLayer to export
            layer_id: Sanitized layer identifier
            
        Returns:
            Path to exported asset file
        """
        if isinstance(layer, QgsVectorLayer):
            # Export as GeoJSON
            output_file = os.path.join(self.assets_dir, f'{layer_id}.geojson')
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'GeoJSON'
            options.fileEncoding = 'UTF-8'
            
            # Apply extent filter if set
            if self.clip_extent and self.clip_crs:
                # Transform clip extent to layer CRS
                transform = QgsCoordinateTransform(
                    self.clip_crs,
                    layer.crs(),
                    QgsProject.instance()
                )
                clip_extent_in_layer_crs = transform.transformBoundingBox(self.clip_extent)
                options.filterExtent = clip_extent_in_layer_crs
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer,
                output_file,
                QgsProject.instance().transformContext(),
                options
            )
            
            if error[0] != QgsVectorFileWriter.NoError:
                raise Exception(f"Failed to export vector layer: {error}")
            
            return output_file
            
        elif isinstance(layer, QgsRasterLayer):
            # Export raster - handle both files and web services
            source_path = layer.source()
            
            # Check if this is a web service (XYZ, WMS, WMTS, etc.)
            # Check for common web service parameters and URLs
            is_web_service = any(indicator in source_path.lower() for indicator in [
                'type=xyz', 'type=wms', 'type=wmts', 'servicetype=', 
                'http://', 'https://', 'url=http', 'url=https'
            ]) or (source_path.startswith('crs=') and '&type=' in source_path)
            
            # Also check provider type for web services
            provider_type = layer.providerType().lower()
            if provider_type in ['wms', 'xyz', 'wmts', 'wcs', 'arcgismapserver', 'arcgisfeatureserver']:
                is_web_service = True
            
            if is_web_service:
                # For web services, export metadata as JSON instead of raster data
                output_file = os.path.join(self.assets_dir, f'{layer_id}_service.json')
                
                # Parse service parameters
                service_info = {
                    'type': 'web_service',
                    'source': source_path,
                    'layer_name': layer.name(),
                    'provider': layer.providerType()
                }
                
                # Extract URL if present (handle URL-encoded characters)
                if 'url=' in source_path:
                    url_start = source_path.find('url=') + 4
                    url_end = source_path.find('&', url_start)
                    if url_end == -1:
                        url = source_path[url_start:]
                    else:
                        url = source_path[url_start:url_end]
                    # Decode URL-encoded characters
                    import urllib.parse
                    url = urllib.parse.unquote(url)
                    service_info['url'] = url
                
                # Save service metadata
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(service_info, f, indent=2)
                
                return output_file
            
            # For local files, clean source path (remove any GDAL dataset specifiers)
            if '|' in source_path:
                source_path = source_path.split('|')[0]
            
            # Determine output format and extension
            output_file = os.path.join(self.assets_dir, f'{layer_id}.tif')
            
            # Try using GDAL directly if available for better reliability
            if GDAL_AVAILABLE:
                try:
                    # Open source dataset
                    src_ds = gdal.Open(source_path, gdal.GA_ReadOnly)
                    if src_ds is None:
                        raise Exception(f"Cannot open raster source: {source_path}")
                    
                    # Create output with GeoTIFF driver
                    driver = gdal.GetDriverByName('GTiff')
                    dst_ds = driver.CreateCopy(output_file, src_ds, strict=0, options=['COMPRESS=LZW'])
                    
                    # Close datasets
                    dst_ds = None
                    src_ds = None
                    
                    if not os.path.exists(output_file):
                        raise Exception("GDAL export did not create output file")
                    
                    return output_file
                    
                except Exception as e:
                    # GDAL failed, try fallback
                    pass
            
            # Fallback: try QGIS raster writer
            try:
                file_writer = QgsRasterFileWriter(output_file)
                file_writer.setOutputFormat('GTiff')
                
                pipe = QgsRasterPipe()
                provider = layer.dataProvider()
                
                if not pipe.set(provider.clone()):
                    raise Exception("Cannot set pipe provider")
                
                extent = layer.extent()
                width = layer.width()
                height = layer.height()
                crs = layer.crs()
                
                # Use the correct writeRaster signature
                error = file_writer.writeRaster(
                    pipe,
                    width,
                    height,
                    extent,
                    crs
                )
                
                if error != QgsRasterFileWriter.NoError:
                    error_messages = {
                        1: "CreateDatasourceError - Cannot create output file",
                        2: "WriteError - Error writing to file", 
                        3: "NoDataConflict - No data conflict (possibly web service or virtual raster)",
                        4: "SourceProviderError - Error with source data provider",
                        5: "WriteCanceled - Write operation was canceled"
                    }
                    error_msg = error_messages.get(error, f"Unknown error code {error}")
                    raise Exception(f"QgsRasterFileWriter failed: {error_msg}. Layer: {layer.name()}, Provider: {layer.providerType()}, Source: {source_path[:200]}")
                
                return output_file
                
            except Exception as e:
                # Final fallback: copy original file if it exists and is a file
                if os.path.exists(source_path) and os.path.isfile(source_path):
                    try:
                        shutil.copy2(source_path, output_file)
                        return output_file
                    except Exception as copy_error:
                        raise Exception(f"Failed to export raster - GDAL failed, QGIS writer failed ({str(e)}), and file copy failed ({str(copy_error)})")
                else:
                    raise Exception(f"Failed to export raster - source file not accessible: {source_path}. QGIS error: {str(e)}")
        
        else:
            raise Exception(f"Unsupported layer type: {type(layer)}")

    def create_stac_item(self, layer, layer_id, asset_path, cop_metadata, file_name):
        """
        Create STAC Item with COP extension
        
        Args:
            layer: QgsMapLayer
            layer_id: UUID4 identifier for STAC item
            asset_path: Path to exported asset
            cop_metadata: COP metadata dictionary
            file_name: Sanitized filename for JSON and assets
            
        Returns:
            STAC Item dictionary
        """
        # Get layer extent
        extent = layer.extent()
        crs = layer.crs()
        
        # Transform to WGS84 if needed
        if crs.authid() != 'EPSG:4326':
            transform = QgsCoordinateTransform(
                crs,
                QgsCoordinateReferenceSystem('EPSG:4326'),
                QgsProject.instance()
            )
            extent = transform.transformBoundingBox(extent)
        
        # Check if extent is valid (not NaN or infinite)
        if (not extent.isFinite() or 
            extent.xMinimum() == extent.xMaximum() or 
            extent.yMinimum() == extent.yMaximum()):
            # Use AOI bbox if available, otherwise use location point
            if cop_metadata.get('aoi') and cop_metadata['aoi'].get('bbox'):
                aoi_bbox = cop_metadata['aoi']['bbox']
                bbox = aoi_bbox
                extent = QgsRectangle(aoi_bbox[0], aoi_bbox[1], aoi_bbox[2], aoi_bbox[3])
            elif cop_metadata.get('location_lon') and cop_metadata.get('location_lat'):
                # Create small bbox around the point location
                lon = cop_metadata['location_lon']
                lat = cop_metadata['location_lat']
                offset = 0.001  # ~100m at equator
                bbox = [lon - offset, lat - offset, lon + offset, lat + offset]
                extent = QgsRectangle(bbox[0], bbox[1], bbox[2], bbox[3])
            else:
                # Last resort: use a default small extent
                bbox = [0, 0, 0.001, 0.001]
                extent = QgsRectangle(0, 0, 0.001, 0.001)
        else:
            bbox = [
                extent.xMinimum(),
                extent.yMinimum(),
                extent.xMaximum(),
                extent.yMaximum()
            ]
        
        # Create geometry
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [extent.xMinimum(), extent.yMinimum()],
                [extent.xMaximum(), extent.yMinimum()],
                [extent.xMaximum(), extent.yMaximum()],
                [extent.xMinimum(), extent.yMaximum()],
                [extent.xMinimum(), extent.yMinimum()]
            ]]
        }
        
        # Determine asset type and add format-specific metadata
        if isinstance(layer, QgsVectorLayer):
            asset_type = "feature"
            media_type = "application/geo+json"
            asset_roles = ["data"]
        else:  # Raster layer
            # Check if this is a web service
            if asset_path.lower().endswith('_service.json'):
                asset_type = "metadata"
                media_type = "application/json"
                asset_roles = ["metadata"]
            else:
                asset_type = "imagery"
                # Determine media type from file extension
                if asset_path.lower().endswith('.tif') or asset_path.lower().endswith('.tiff'):
                    media_type = "image/tiff; application=geotiff"
                elif asset_path.lower().endswith('.png'):
                    media_type = "image/png"
                elif asset_path.lower().endswith('.jpg') or asset_path.lower().endswith('.jpeg'):
                    media_type = "image/jpeg"
                else:
                    media_type = "image/tiff"
                asset_roles = ["data", "visual"]
        
        # Build STAC Item
        stac_extensions = [
            "https://stac-extensions.github.io/cop/v1.0.0/schema.json"
        ]
        
        # Add raster extension if it's a raster layer
        if isinstance(layer, QgsRasterLayer):
            stac_extensions.append("https://stac-extensions.github.io/raster/v1.1.0/schema.json")
        
        stac_item = {
            "stac_version": "1.0.0",
            "stac_extensions": stac_extensions,
            "type": "Feature",
            "id": layer_id,
            "bbox": bbox,
            "geometry": geometry,
            "properties": {
                "datetime": datetime.now(timezone.utc).isoformat(),
                "title": layer.name()
            },
            "assets": {
                "data": {
                    "href": os.path.relpath(asset_path, self.stac_dir),
                    "title": f"{layer.name()} Data",
                    "type": media_type,
                    "roles": asset_roles,
                    "cop:asset_type": asset_type
                }
            },
            "links": [
                {
                    "rel": "self",
                    "href": f"./{file_name}.json"
                },
                {
                    "rel": "collection",
                    "href": "./collection.json"
                },
                {
                    "rel": "parent",
                    "href": "./collection.json"
                }
            ]
        }
        
        # Add GNOSIS-specific metadata if present
        if cop_metadata.get('gnosis_source'):
            stac_item['properties']['gnosis:source'] = cop_metadata['gnosis_source']
            stac_item['properties']['gnosis:data_type'] = cop_metadata.get('data_type', 'elevation')
            stac_item['properties']['description'] = f"SRTM elevation data from {cop_metadata['gnosis_source']}"
        
        # Add raster-specific metadata if it's a raster layer
        if isinstance(layer, QgsRasterLayer):
            provider = layer.dataProvider()
            stac_item['properties']['raster:bands'] = []
            
            for band_num in range(1, layer.bandCount() + 1):
                band_info = {
                    "name": layer.bandName(band_num),
                    "data_type": provider.dataType(band_num)
                }
                # Add statistics if available
                stats = provider.bandStatistics(band_num)
                if stats.minimumValue != stats.maximumValue:
                    band_info["statistics"] = {
                        "minimum": stats.minimumValue,
                        "maximum": stats.maximumValue,
                        "mean": stats.mean,
                        "stddev": stats.stdDev
                    }
                stac_item['properties']['raster:bands'].append(band_info)
            
            # Add pixel size
            stac_item['properties']['gsd'] = layer.rasterUnitsPerPixelX()
        
        # Add COP metadata fields to properties
        if cop_metadata.get('mission'):
            stac_item['properties']['cop:mission'] = cop_metadata['mission']
        
        if cop_metadata.get('classification'):
            stac_item['properties']['cop:classification'] = cop_metadata['classification']
        
        if cop_metadata.get('releasability'):
            stac_item['properties']['cop:releasability'] = cop_metadata['releasability']
        
        if cop_metadata.get('dggs_crs'):
            stac_item['properties']['cop:dggs_crs'] = cop_metadata['dggs_crs']
        
        if cop_metadata.get('dggs_zone_id'):
            stac_item['properties']['cop:dggs_zone_id'] = cop_metadata['dggs_zone_id']
        
        if cop_metadata.get('service_provider'):
            stac_item['properties']['cop:service_provider'] = cop_metadata['service_provider']
        
        return stac_item

    def create_collection(self, collection_id, title, description):
        """
        Create STAC Collection for exported items
        
        Args:
            collection_id: Collection identifier
            title: Collection title
            description: Collection description
            
        Returns:
            Path to collection JSON file
        """
        # Calculate overall extent from items
        all_bbox = []
        all_times = []
        
        for item in self.exported_items:
            all_bbox.append(item['bbox'])
            if 'datetime' in item['properties']:
                all_times.append(item['properties']['datetime'])
        
        # Calculate spatial extent
        if all_bbox:
            min_x = min(bbox[0] for bbox in all_bbox)
            min_y = min(bbox[1] for bbox in all_bbox)
            max_x = max(bbox[2] for bbox in all_bbox)
            max_y = max(bbox[3] for bbox in all_bbox)
            spatial_bbox = [min_x, min_y, max_x, max_y]
        else:
            spatial_bbox = [-180, -90, 180, 90]
        
        # Calculate temporal extent
        if all_times:
            temporal_interval = [[min(all_times), max(all_times)]]
        else:
            now = datetime.now(timezone.utc).isoformat()
            temporal_interval = [[now, now]]
        
        collection = {
            "stac_version": "1.0.0",
            "stac_extensions": [
                "https://stac-extensions.github.io/cop/v1.0.0/schema.json"
            ],
            "type": "Collection",
            "id": collection_id,
            "title": title,
            "description": description,
            "license": "proprietary",
            "extent": {
                "spatial": {
                    "bbox": [spatial_bbox]
                },
                "temporal": {
                    "interval": temporal_interval
                }
            },
            "links": [
                {
                    "rel": "self",
                    "href": "./collection.json"
                },
                {
                    "rel": "root",
                    "href": "./collection.json"
                }
            ]
        }
        
        # Add item links
        for item in self.exported_items:
            file_name = item.get('_file_name', item['id'])  # Fallback to ID if no file_name
            collection['links'].append({
                "rel": "item",
                "href": f"./{file_name}.json"
            })
        
        # Save collection
        collection_path = os.path.join(self.stac_dir, 'collection.json')
        with open(collection_path, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2)
        
        return collection_path

    def create_zip_archive(self):
        """
        Create ZIP archive of all exported STAC files and generate SHA256 hash
        
        Returns:
            Tuple of (zip_path, sha256_hash)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'stac_cop_export_{timestamp}.zip'
        zip_path = os.path.join(self.output_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through STAC directory and add all files
            for root, dirs, files in os.walk(self.stac_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.output_dir)
                    zipf.write(file_path, arcname)
        
        # Calculate SHA256 hash of the ZIP file
        sha256_hash = hashlib.sha256()
        with open(zip_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        hash_value = sha256_hash.hexdigest()
        
        # Write hash to a text file
        hash_filename = f'stac_cop_export_{timestamp}.zip.sha256'
        hash_path = os.path.join(self.output_dir, hash_filename)
        with open(hash_path, 'w') as f:
            f.write(f"{hash_value}  {zip_filename}\n")
        
        return zip_path, hash_value

    @staticmethod
    def sanitize_id(name):
        """
        Sanitize layer name to create valid STAC ID
        
        Args:
            name: Original layer name
            
        Returns:
            Sanitized identifier
        """
        # Remove special characters and spaces
        sanitized = ''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
        # Ensure it starts with alphanumeric
        if not sanitized[0].isalnum():
            sanitized = 'item_' + sanitized
        return sanitized.lower()
