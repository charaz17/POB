#/disk/disk.py

import threading
from dataclasses import dataclass
from typing import List, Optional
import time

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
        
    def read_sector(self, sector_idx: int) -> Optional[Sector]:
        # implementacja odczytu sektora
        pass
        
    def write_sector(self, sector_idx: int, data: bytearray) -> bool:
        # implementacja zapisu sektora
        pass