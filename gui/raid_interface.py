from PyQt5 import QtWidgets
import socket

class RAIDInterface(QtWidgets.QMainWindow):
    def __init__(self, raid_controller):
        super().__init__()
        self.setWindowTitle("Symulacja RAID")
        self.setGeometry(100, 100, 500, 400)
        self.raid_controller = raid_controller
        self.setupUI()

    def setupUI(self):
        self.label = QtWidgets.QLabel("Monitor RAID", self)
        self.label.setGeometry(50, 20, 300, 30)
        self.disk_status_labels = []

        for i in range(4):
            label = QtWidgets.QLabel(f"Dysk {i} - OK", self)
            label.setGeometry(50, 60 + i * 40, 300, 30)
            self.disk_status_labels.append(label)

        self.button_exchange = QtWidgets.QPushButton("Prześlij dane między dyskami", self)
        self.button_exchange.setGeometry(50, 290, 200, 50)
        self.button_exchange.clicked.connect(self.exchange_data)

        self.button_show_stats = QtWidgets.QPushButton("Pokaż Statystyki", self)
        self.button_show_stats.setGeometry(260, 290, 200, 50)
        self.button_show_stats.clicked.connect(self.show_stats)

    def update_status_labels(self):
        """Aktualizuje statusy dysków w GUI."""
        for i, disk in enumerate(self.raid_controller.disks):
            status = (
                f"Dysk {i} - Writes: {disk.stats['writes']}, "
                f"Reads: {disk.stats['reads']}, "
                f"Sent: {disk.stats['sent']}, "
                f"Received: {disk.stats['received']}"
            )
            self.disk_status_labels[i].setText(status)

    def exchange_data(self):
        """Symulacja przesyłania danych między dwoma dyskami."""
        sender_id = 0
        receiver_id = 1
        data = "Przykładowe dane"
        self.raid_controller.exchange_data(sender_id, receiver_id, data)
        self.update_status_labels()

    def show_stats(self):
        """Wyświetlanie statystyk RAID."""
        stats = self.raid_controller.get_stats()
        stats_text = "\n".join([f"Dysk {i}: {stat}" for i, stat in stats.items()])
        QtWidgets.QMessageBox.information(self, "Statystyki RAID", stats_text)
