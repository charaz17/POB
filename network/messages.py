#/network/messages.py

from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class DiskMessage:
    operation: str  # 'read', 'write', 'status', 'error'
    disk_id: int
    sector: Optional[int] = None
    data: Optional[bytes] = None
    timestamp: float = time.time()