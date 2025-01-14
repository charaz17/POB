#/gui/visualization.py


from PyQt6.QtWidgets import QWidget, QGridLayout
#from PyQt6.QtChart import QChart, QChartView, QLineSeries
import datetime
from controller.raid_controller import RaidController

class DataVisualization(QWidget):
    def __init__(self, controller: RAIDController):
        super().__init__()
        self.controller = controller
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout(self)
        
        # Create charts
        self.throughput_chart = self.create_chart("Throughput Over Time", "Time", "MB/s")
        self.latency_chart = self.create_chart("Latency Over Time", "Time", "ms")
        self.error_chart = self.create_chart("Error Rate", "Time", "Errors/s")
        
        # Create disk usage visualization
        self.disk_usage = QWidget()
        usage_layout = QGridLayout(self.disk_usage)
        self.usage_bars = []
        
        for i, disk in enumerate(self.controller.disks):
            label = QLabel(f"Disk {i} Usage")
            progress = QProgressBar()
            self.usage_bars.append(progress)
            usage_layout.addWidget(label, i, 0)
            usage_layout.addWidget(progress, i, 1)
        
        # Layout everything
        layout.addWidget(self.throughput_chart, 0, 0)
        layout.addWidget(self.latency_chart, 0, 1)
        layout.addWidget(self.error_chart, 1, 0)
        layout.addWidget(self.disk_usage, 1, 1)

    def create_chart(self, title: str, x_label: str, y_label: str) -> QChartView:
        series = QLineSeries()
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        
        axis_x = QValueAxis()
        axis_x.setTitleText(x_label)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText(y_label)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        chart_view = QChartView(chart)
        chart_view.setMinimumSize(300, 200)
        return chart_view

    def update_visualization(self):
        current_time = datetime.datetime.now()
        
        # Update charts
        for disk in self.controller.disks:
            # Throughput
            self.throughput_chart.chart().series()[0].append(
                current_time.timestamp(), disk.stats.get_throughput())
            
            # Latency
            self.latency_chart.chart().series()[0].append(
                current_time.timestamp(), disk.stats.get_average_latency() * 1000)
            
            # Error rate
            self.error_chart.chart().series()[0].append(
                current_time.timestamp(), disk.stats.get_error_rate())
        
        # Update usage bars
        for i, disk in enumerate(self.controller.disks):
            used_sectors = sum(1 for sector in disk.sectors if sector is not None)
            usage_percentage = (used_sectors / disk.sector_count) * 100
            self.usage_bars[i].setValue(int(usage_percentage))

