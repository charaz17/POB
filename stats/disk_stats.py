#/stats/disk_stats.py

import time
from typing import List, Tuple

class DiskStats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.reads = 0
        self.writes = 0
        self.errors = 0
        self.latency_history = []
        self.error_history = []
        self.throughput_history = []
        self.current_load = 0
        self.total_bytes_read = 0
        self.total_bytes_written = 0
        self.start_time = time.time()

    def add_operation(self, op_type: str, size: int, latency: float):
        if op_type == 'read':
            self.reads += 1
            self.total_bytes_read += size
        elif op_type == 'write':
            self.writes += 1
            self.total_bytes_written += size

        self.latency_history.append(latency)
        self.update_throughput()

    def add_error(self, error_type: str, timestamp: float):
        self.errors += 1
        self.error_history.append((error_type, timestamp))

    def update_throughput(self):
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            current_throughput = (self.total_bytes_read + self.total_bytes_written) / elapsed
            self.throughput_history.append(current_throughput)

    def get_average_latency(self) -> float:
        return sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0

    def get_error_rate(self) -> float:
        total_ops = self.reads + self.writes
        return self.errors / total_ops if total_ops > 0 else 0

    def get_throughput(self) -> float:
        return self.throughput_history[-1] if self.throughput_history else 0
