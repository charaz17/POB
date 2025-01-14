from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QProgressBar
from PyQt6.QtCore import Qt

class DiskPanel(QWidget):
    def __init__(self, controller):
        """
        Panel GUI odpowiedzialny za monitorowanie stanu dysków oraz interakcję z użytkownikiem,
        w tym wprowadzanie błędów i ich naprawę.

        Args:
            controller: Obiekt kontrolera RAID odpowiedzialny za zarządzanie dyskami.
        """
        super().__init__()
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        """
        Inicjalizuje elementy graficzne panelu, takie jak pasek postępu dla każdego dysku,
        przyciski do wprowadzania błędów i naprawiania dysków.
        """
        layout = QVBoxLayout(self)
        self.disk_widgets = []

        for disk_id in range(len(self.controller.shared_memory)):
            disk_layout = QHBoxLayout()
            
            # Etykieta identyfikatora dysku
            label = QLabel(f"Disk {disk_id}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Pasek postępu użycia dysku
            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setValue(0)  # Wartość początkowa

            # Przycisk wstrzykiwania błędów
            inject_error_button = QPushButton("Inject Error")
            inject_error_button.clicked.connect(lambda _, d=disk_id: self.inject_error(d))

            # Przycisk naprawy dysku
            repair_button = QPushButton("Repair Disk")
            repair_button.clicked.connect(lambda _, d=disk_id: self.repair_disk(d))

            # Dodanie elementów do layoutu
            disk_layout.addWidget(label)
            disk_layout.addWidget(progress_bar)
            disk_layout.addWidget(inject_error_button)
            disk_layout.addWidget(repair_button)

            layout.addLayout(disk_layout)
            self.disk_widgets.append((progress_bar, inject_error_button, repair_button))

        self.setLayout(layout)

    def update_status(self):
        """
        Aktualizuje stan dysków na podstawie danych z kontrolera RAID, w tym postęp użycia sektorów
        oraz status awarii.
        """
        for disk_id, (progress_bar, inject_error_button, repair_button) in enumerate(self.disk_widgets):
            disk_stats = self.controller.get_disk_status()[disk_id]
            
            # Aktualizacja paska postępu
            used_sectors = disk_stats['stats']['total_bytes_written'] / (
                self.controller.sector_size * self.controller.num_sectors
            ) * 100
            progress_bar.setValue(int(used_sectors))

            # Aktualizacja przycisków w zależności od statusu dysku
            if disk_stats['is_failed']:
                inject_error_button.setEnabled(False)
                repair_button.setEnabled(True)
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
            else:
                inject_error_button.setEnabled(True)
                repair_button.setEnabled(False)
                progress_bar.setStyleSheet("")

    def inject_error(self, disk_id):
        """
        Wstrzykuje błąd do wybranego dysku.

        Args:
            disk_id: ID dysku, do którego ma zostać wprowadzony błąd.
        """
        self.controller.inject_disk_error(disk_id, "disk_failure")
        self.update_status()

    def repair_disk(self, disk_id):
        """
        Naprawia wybrany dysk.

        Args:
            disk_id: ID dysku, który ma zostać naprawiony.
        """
        self.controller.repair_disk(disk_id)
        self.update_status()
