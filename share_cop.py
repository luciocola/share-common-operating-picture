"""
Share Common Operating Picture Plugin - Main Plugin Class
"""

import os
from qgis.PyQt.QtCore import QTranslator, QCoreApplication, QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject

from .share_cop_dialog import ShareCOPDialog


class ShareCOP:
    """QGIS Plugin Implementation for Share Common Operating Picture."""

    def __init__(self, iface):
        """Constructor.
        
        Args:
            iface: An interface instance that will be passed to this class
                which provides the hook by which you can manipulate the QGIS
                application at run time.
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ShareCOP_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&Share Common Operating Picture')
        self.toolbar = self.iface.addToolBar('ShareCOP')
        self.toolbar.setObjectName('ShareCOP')
        
        # Dialog instance
        self.dlg = None

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        
        Args:
            message: String for translation.
            
        Returns:
            Translated version of message.
        """
        return QCoreApplication.translate('ShareCOP', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.
        
        Args:
            icon_path: Path to the icon for this action
            text: Text that should be shown in menu items for this action
            callback: Function to be called when the action is triggered
            enabled_flag: A flag indicating if the action should be enabled
            add_to_menu: Flag indicating whether the action should also
                be added to the menu
            add_to_toolbar: Flag indicating whether the action should also
                be added to the toolbar
            status_tip: Optional text to show in a popup when mouse pointer
                hovers over the action
            parent: Parent widget for the new action
            whats_this: Optional text to show in the status bar when the
                mouse pointer hovers over the action
                
        Returns:
            The action that was created
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToWebMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr('Share Common Operating Picture'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginWebMenu(
                self.tr('&Share Common Operating Picture'),
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        """Run method that performs all the real work."""
        if self.dlg is None:
            self.dlg = ShareCOPDialog(self.iface)
        
        # Show the dialog
        self.dlg.show()
        result = self.dlg.exec_()
        
        if result:
            # User clicked OK/Accept
            pass
