# Installing ReportLab for PDF Generation

The Share Common Operating Picture plugin can generate PDF reports of chatbot results. This requires the `reportlab` library.

## Installation

### macOS (QGIS-LTR)

Open Terminal and run:

```bash
/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3 -m pip install reportlab
```

### Linux

```bash
python3 -m pip install --user reportlab
# OR if using QGIS Python directly:
/usr/bin/python3 -m pip install --user reportlab
```

### Windows

Open OSGeo4W Shell (or QGIS Python Console) and run:

```bash
python -m pip install reportlab
```

## Verification

To verify ReportLab is installed:

1. Open QGIS Python Console (Plugins → Python Console)
2. Type: `import reportlab; print(reportlab.Version)`
3. You should see a version number (e.g., "3.6.12")

## Without ReportLab

If ReportLab is not installed:
- The plugin will still work normally
- Chatbot results will be displayed in the dialog
- Results will be included in the STAC collection metadata
- **PDF generation will be skipped** with a warning message

## Features with ReportLab

When ReportLab is installed, the plugin will:
- ✅ Generate a formatted PDF report of chatbot results
- ✅ Save PDF in the `assets/` folder
- ✅ Reference PDF in STAC collection as an asset
- ✅ Include PDF in the exported ZIP package

The PDF includes:
- Mission query text
- Timestamp
- All chatbot responses and suggestions
- Related missions and references
- URLs and classifications
- Professional formatting with headings and sections
