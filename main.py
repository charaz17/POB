from PyQt5 import QtWidgets
from disks.disk import Disk
from controllers.raid_controller import RAIDController
from gui.raid_interface import RAIDInterface
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    disks = [Disk(5000 + i, i) for i in range(4)]
    raid_controller = RAIDController(disks)
    raid_controller.start_disks()
    
    window = RAIDInterface(raid_controller)
    window.show()
    
    sys.exit(app.exec_())
