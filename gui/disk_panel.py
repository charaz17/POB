#/gui/disk_panel.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from controller.raid_controller import RAIDController

class DiskPanel(QWidget):
    def __init__(self, controller: RAIDController):
        super().__init__()
        self.controller = controller
        self.init_ui()