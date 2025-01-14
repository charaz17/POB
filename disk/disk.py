import threading
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Sector:
    index: int
    data: bytearray
    checksum: int

class Disk(threading.Thread):
    def __init__(self, disk_id: int, sector_size: int = 32, sector_count: int = 128):
        super().__init__()
        self.disk_id = disk_id
        self.sector_size = sector_size
        self.sector_count = sector_count
        self.sectors: List[Optional[Sector]] = [None] * sector_count
        self.is_failed = False
        self._stop_event = threading.Event()
        
    def run(self):
        """
        Jeśli potrzebujesz, możesz tutaj zaimplementować logikę wątku dysku.
        Obecnie pusto.
        """
        while not self._stop_event.is_set():
            # Tu jakaś logika np. obsługa I/O
            pass
        
    def stop(self):
        """
        Bezpieczne zatrzymanie wątku.
        """
        self._stop_event.set()

    def read_sector(self, sector_idx: int) -> Optional[Sector]:
        # Implementacja odczytu sektora (przykład)
        if 0 <= sector_idx < self.sector_count:
            return self.sectors[sector_idx]
        return None
        
    def write_sector(self, sector_idx: int, data: bytearray) -> bool:
        # Implementacja zapisu sektora (przykład)
        if 0 <= sector_idx < self.sector_count:
            self.sectors[sector_idx] = Sector(index=sector_idx, data=data, checksum=0)
            return True
        return False
