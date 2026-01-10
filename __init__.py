"""
Share Common Operating Picture Plugin
A QGIS plugin for selecting locations with reverse geocoding and DGGS zone conversion.
"""


def classFactory(iface):
    """Load ShareCOP class from file ShareCOP.
    
    Args:
        iface: A QGIS interface instance.
    """
    from .share_cop import ShareCOP
    return ShareCOP(iface)
