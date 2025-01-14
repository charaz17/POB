#/gui/raid_interface.py

from PyQt6.QtWidgets import QMainWindow, QTabWidget
from gui.disk_panel import DiskPanel
from gui.visualization import DataVisualization

class RAIDSimulatorGUI(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.init_ui()