from typing import List, Optional, Dict
from multiprocessing import Process, Array, Semaphore
import threading
import logging
import numpy as np

class RAIDController:
    """
    Kontroler macierzy RAID obsługujący różne poziomy RAID (0, 1, 3).
    Zarządza dyskami i operacjami I/O, implementując różne strategie zapisywania danych.
    """

    def __init__(self, raid_type: str, num_disks: int = 4, sector_size: int = 32, num_sectors: int = 128):
        """
        Inicjalizacja kontrolera RAID.

        Args:
            raid_type: Typ RAID ('RAID0', 'RAID1', 'RAID3')
            num_disks: Liczba dysków w macierzy
            sector_size: Rozmiar sektora w bajtach
            num_sectors: Liczba sektorów na każdy dysk
        """
        self.raid_type = raid_type
        self.sector_size = sector_size
        self.num_sectors = num_sectors
        self.num_disks = num_disks

        self.shared_memory = [Array('b', sector_size * num_sectors) for _ in range(num_disks)]
        self.semaphores = [Semaphore(1) for _ in range(num_disks)]
        self.disk_processes: List[Process] = []
        self.initialize_disks()

        # Słownik mapujący typy RAID na odpowiednie metody
        self.write_strategies: Dict[str, callable] = {
            'RAID0': self._write_raid0,
            'RAID1': self._write_raid1,
            'RAID3': self._write_raid3
        }

        self.read_strategies: Dict[str, callable] = {
            'RAID0': self._read_raid0,
            'RAID1': self._read_raid1,
            'RAID3': self._read_raid3
        }

        logging.info(f"Initialized {raid_type} controller with {num_disks} disks")

    def initialize_disks(self):
        """
        Tworzy procesy dla każdego dysku w macierzy.
        """
        for i in range(self.num_disks):
            process = Process(target=self._disk_worker, args=(i,))
            process.start()
            self.disk_processes.append(process)

    def _disk_worker(self, disk_id: int):
        """
        Wątek roboczy dla symulowanego dysku, odpowiedzialny za zarządzanie pamięcią dzieloną.

        Args:
            disk_id: Identyfikator dysku
        """
        while True:
            # Wątek dysku obsługuje tutaj żądania zapisu/odczytu
            pass  # Placeholder - logika komunikacji/działania zostanie dodana później

    def write_data(self, data: bytes, sector_number: int) -> bool:
        """
        Zapisuje dane do macierzy RAID używając odpowiedniej strategii.

        Args:
            data: Dane do zapisania
            sector_number: Numer sektora docelowego

        Returns:
            bool: True jeśli zapis się powiódł, False w przeciwnym razie
        """
        if self.raid_type not in self.write_strategies:
            raise ValueError(f"Unsupported RAID type: {self.raid_type}")

        return self.write_strategies[self.raid_type](data, sector_number)

    def read_data(self, sector_number: int) -> Optional[bytes]:
        """
        Odczytuje dane z macierzy RAID używając odpowiedniej strategii.

        Args:
            sector_number: Numer sektora do odczytu

        Returns:
            Optional[bytes]: Odczytane dane lub None w przypadku błędu
        """
        if self.raid_type not in self.read_strategies:
            raise ValueError(f"Unsupported RAID type: {self.raid_type}")

        return self.read_strategies[self.raid_type](sector_number)

    def _write_raid0(self, data: bytes, sector_number: int) -> bool:
        """
        Implementacja zapisu dla RAID0 (striping).
        Dane są dzielone równo między wszystkie dyski.
        """
        stripe_size = len(data) // self.num_disks
        success = True

        for i in range(self.num_disks):
            start = i * stripe_size
            end = start + stripe_size
            stripe_data = data[start:end]

            # Blokada zapisu
            self.semaphores[i].acquire()
            try:
                start_idx = sector_number * self.sector_size
                self.shared_memory[i][start_idx:start_idx + len(stripe_data)] = stripe_data
            except Exception as e:
                success = False
                logging.error(f"RAID0 write failed on disk {i}: {e}")
            finally:
                self.semaphores[i].release()

        return success

    def _write_raid1(self, data: bytes, sector_number: int) -> bool:
        """
        Implementacja zapisu dla RAID1 (mirroring).
        Dane są powielane na wszystkich dyskach.
        """
        success = True

        for i in range(self.num_disks):
            self.semaphores[i].acquire()
            try:
                start_idx = sector_number * self.sector_size
                self.shared_memory[i][start_idx:start_idx + len(data)] = data
            except Exception as e:
                success = False
                logging.error(f"RAID1 write failed on disk {i}: {e}")
            finally:
                self.semaphores[i].release()

        return success

    def _write_raid3(self, data: bytes, sector_number: int) -> bool:
        """
        Implementacja zapisu dla RAID3 (striping z dedykowaną parzystością).
        """
        stripe_size = len(data) // (self.num_disks - 1)  # Jeden dysk na parzystość
        parity = bytearray(stripe_size)
        success = True

        for i in range(self.num_disks - 1):
            start = i * stripe_size
            end = start + stripe_size
            stripe_data = data[start:end]

            # Obliczanie parzystości
            for j in range(len(stripe_data)):
                parity[j] ^= stripe_data[j]

            self.semaphores[i].acquire()
            try:
                start_idx = sector_number * self.sector_size
                self.shared_memory[i][start_idx:start_idx + len(stripe_data)] = stripe_data
            except Exception as e:
                success = False
                logging.error(f"RAID3 write failed on disk {i}: {e}")
            finally:
                self.semaphores[i].release()

        # Zapis parzystości
        self.semaphores[-1].acquire()
        try:
            start_idx = sector_number * self.sector_size
            self.shared_memory[-1][start_idx:start_idx + len(parity)] = parity
        except Exception as e:
            success = False
            logging.error(f"RAID3 parity write failed: {e}")
        finally:
            self.semaphores[-1].release()

        return success

    def stop_disks(self):
        """
        Zatrzymuje wszystkie procesy dysków.
        """
        for process in self.disk_processes:
            process.terminate()
            process.join()

        logging.info("All disk processes stopped")
