from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from gui.disk_panel import DiskPanel
import threading
import time

class RAIDSimulatorGUI(QMainWindow):
    def __init__(self, controller):
        """
        Inicjalizuje główne okno aplikacji symulującej działanie macierzy RAID.

        Args:
            controller: Obiekt kontrolera RAID odpowiedzialny za zarządzanie dyskami.
        """
        super().__init__()
        self.controller = controller
        self.setWindowTitle("RAID Simulator")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        """
        Inicjalizuje elementy interfejsu użytkownika, w tym zakładki dla panelu statusu dysków
        oraz wizualizacji statystyk RAID.
        """
        # Główna zakładka
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Dodanie zakładek GUI
        self.disk_panel = DiskPanel(self.controller)
        self.visualization_panel = VisualizationPanel(self.controller)

        self.tabs.addTab(self.disk_panel, "Disk Status")
        self.tabs.addTab(self.visualization_panel, "Visualization")

class VisualizationPanel(QWidget):
    def __init__(self, controller):
        """
        Panel wizualizacji statystyk RAID, w tym przepustowości i błędów w czasie rzeczywistym.

        Args:
            controller: Obiekt kontrolera RAID odpowiedzialny za dostarczanie danych statystycznych.
        """
        super().__init__()
        self.controller = controller
        self.init_ui()
        self.update_thread = threading.Thread(target=self.update_visualization, daemon=True)
        self.update_thread.start()

    def init_ui(self):
        """
        Tworzy elementy graficzne panelu, w tym etykiety do wyświetlania statystyk oraz wykresy
        przepustowości za pomocą biblioteki matplotlib.
        """
        layout = QVBoxLayout(self)
        self.throughput_label = QLabel("Throughput: 0 MB/s")
        self.error_rate_label = QLabel("Error Rate: 0 errors/s")
        
        # Wykresy za pomocą matplotlib
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Disk Throughput Over Time")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Throughput (MB/s)")
        self.throughput_data = []
        self.time_data = []

        # Przycisk odświeżania
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.update_visualization)

        layout.addWidget(self.throughput_label)
        layout.addWidget(self.error_rate_label)
        layout.addWidget(self.canvas)
        layout.addWidget(self.refresh_button)

    def update_visualization(self):
        """
        Aktualizuje dane statystyczne RAID w czasie rzeczywistym, w tym przepustowość i wskaźnik błędów,
        oraz odświeża wykresy wizualizacji.
        """
        while True:
            try:
                # Aktualizacja statystyk RAID
                throughput = sum(disk.stats.get_throughput() for disk in self.controller.shared_memory) / len(self.controller.shared_memory)
                error_rate = sum(disk.stats.get_error_rate() for disk in self.controller.shared_memory) / len(self.controller.shared_memory)

                # Aktualizacja tekstów
                self.throughput_label.setText(f"Throughput: {throughput:.2f} MB/s")
                self.error_rate_label.setText(f"Error Rate: {error_rate:.2f} errors/s")

                # Dodanie nowych danych do wykresu
                self.time_data.append(len(self.time_data))
                self.throughput_data.append(throughput)

                # Rysowanie wykresu
                self.ax.clear()
                self.ax.plot(self.time_data, self.throughput_data, label="Throughput")
                self.ax.legend()
                self.canvas.draw()

                time.sleep(1)  # Odświeżanie co 1 sekundę
            except Exception as e:
                print(f"Visualization update error: {e}")
                break