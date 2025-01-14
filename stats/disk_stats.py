import time
from typing import List, Tuple

class DiskStats:
    def __init__(self):
        """
        Inicjalizuje obiekt statystyk dla dysku, przechowujący dane dotyczące operacji I/O,
        błędów, opóźnień oraz przepustowości.
        """
        self.reset()

    def reset(self):
        """
        Resetuje wszystkie statystyki dysku do wartości początkowych.
        """
        self.reads = 0
        self.writes = 0
        self.errors = 0
        self.latency_history: List[float] = []
        self.error_history: List[Tuple[str, float]] = []
        self.throughput_history: List[float] = []
        self.current_load = 0
        self.total_bytes_read = 0
        self.total_bytes_written = 0
        self.start_time = time.time()

    def add_operation(self, op_type: str, size: int, latency: float):
        """
        Rejestruje operację dysku, aktualizując statystyki odczytów, zapisów i opóźnień.

        Args:
            op_type: Typ operacji ('read' lub 'write').
            size: Rozmiar danych operacji w bajtach.
            latency: Opóźnienie operacji w sekundach.
        """
        if op_type == 'read':
            self.reads += 1
            self.total_bytes_read += size
        elif op_type == 'write':
            self.writes += 1
            self.total_bytes_written += size

        self.latency_history.append(latency)
        self.update_throughput()

    def add_error(self, error_type: str, timestamp: float):
        """
        Rejestruje błąd operacji na dysku.

        Args:
            error_type: Typ błędu (np. 'disk_failure').
            timestamp: Czas wystąpienia błędu.
        """
        self.errors += 1
        self.error_history.append((error_type, timestamp))

    def update_throughput(self):
        """
        Aktualizuje przepustowość na podstawie całkowitej ilości danych odczytanych i zapisanych
        od początku działania dysku.
        """
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            current_throughput = (self.total_bytes_read + self.total_bytes_written) / elapsed / (1024 * 1024)
            self.throughput_history.append(current_throughput)

    def get_average_latency(self) -> float:
        """
        Oblicza średnie opóźnienie dla operacji dysku.

        Returns:
            Średnie opóźnienie w sekundach.
        """
        return sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0.0

    def get_error_rate(self) -> float:
        """
        Oblicza wskaźnik błędów w stosunku do wszystkich operacji.

        Returns:
            Wskaźnik błędów jako wartość dziesiętna (np. 0.01 dla 1%).
        """
        total_ops = self.reads + self.writes
        return self.errors / total_ops if total_ops > 0 else 0.0

    def get_throughput(self) -> float:
        """
        Pobiera ostatnio zarejestrowaną przepustowość.

        Returns:
            Przepustowość w MB/s.
        """
        return self.throughput_history[-1] if self.throughput_history else 0.0

    def get_stats(self) -> dict:
        """
        Zwraca słownik ze szczegółowymi statystykami dysku.

        Returns:
            Słownik zawierający kluczowe dane statystyczne dysku.
        """
        return {
            'reads': self.reads,
            'writes': self.writes,
            'errors': self.errors,
            'average_latency': self.get_average_latency(),
            'error_rate': self.get_error_rate(),
            'throughput': self.get_throughput(),
            'total_bytes_read': self.total_bytes_read,
            'total_bytes_written': self.total_bytes_written
        }