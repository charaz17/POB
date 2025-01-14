#/main.py

import sys
from PyQt6.QtWidgets import QApplication
from network.protocol import NetworkProtocol
from controller.raid_controller import RAIDController
from gui.raid_interface import RAIDSimulatorGUI

def main():
    network = NetworkProtocol()
    network.start_server()
    
    controller = RAIDController('RAID0')
    
    app = QApplication(sys.argv)
    window = RAIDSimulatorGUI(controller)
    window.show()
    
    try:
        sys.exit(app.exec())
    finally:
        network.stop()
        controller.stop_disks()

if __name__ == '__main__':
    main()