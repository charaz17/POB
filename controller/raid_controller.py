import logging
from typing import List, Optional, Dict
import threading
from threading import Semaphore, Lock
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

        # Zamiast multiprocessing.Array używamy po prostu listy bajtów lub bytearray.
        # Każdy "dysk" jest reprezentowany przez tablicę znaków (bajtów).
        self.shared_memory: List[bytearray] = [
            bytearray(sector_size * num_sectors) for _ in range(num_disks)
        ]

        # Każdy dysk ma własną semaforę do ochrony zapisu.
        self.semaphores: List[Semaphore] = [Semaphore(value=1) for _ in range(num_disks)]

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

    # -----------------------
    # Metody zapisu
    # -----------------------

    def _write_raid0(self, data: bytes, sector_number: int) -> bool:
        """
        Implementacja zapisu dla RAID0 (striping).
        Dane są dzielone równo między wszystkie dyski.
        """
        success = True
        stripe_size = len(data) // self.num_disks if self.num_disks > 0 else len(data)

        for i in range(self.num_disks):
            start = i * stripe_size
            end = start + stripe_size
            stripe_data = data[start:end]

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
        Ostatni dysk w tablicy to dysk parzystości.
        """
        success = True
        if self.num_disks < 2:
            logging.error("RAID3 requires at least 2 disks.")
            return False

        data_disks = self.num_disks - 1
        stripe_size = len(data) // data_disks if data_disks > 0 else len(data)

        # Bufor na parzystość
        parity = bytearray(stripe_size)

        # Zapis + obliczanie parzystości
        for i in range(data_disks):
            start = i * stripe_size
            end = start + stripe_size
            stripe_data = data[start:end]

            # XOR do parzystości
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

        # Zapis dysku parzystości (ostatni dysk)
        parity_disk = self.num_disks - 1
        self.semaphores[parity_disk].acquire()
        try:
            start_idx = sector_number * self.sector_size
            self.shared_memory[parity_disk][start_idx:start_idx + len(parity)] = parity
        except Exception as e:
            success = False
            logging.error(f"RAID3 parity write failed: {e}")
        finally:
            self.semaphores[parity_disk].release()

        return success

    # -----------------------
    # Metody odczytu
    # -----------------------

    def _read_raid0(self, sector_number: int) -> Optional[bytes]:
        """
        Implementacja odczytu dla RAID0.
        Odczytuje dane z wszystkich dysków i je scala.
        """
        success = True
        result = bytearray()

        for i in range(self.num_disks):
            self.semaphores[i].acquire()
            try:
                start_idx = sector_number * self.sector_size
                part = self.shared_memory[i][start_idx:start_idx + self.sector_size]
                result.extend(part)
            except Exception as e:
                success = False
                logging.error(f"RAID0 read failed on disk {i}: {e}")
            finally:
                self.semaphores[i].release()

        return bytes(result) if success else None

    def _read_raid1(self, sector_number: int) -> Optional[bytes]:
        """
        Implementacja odczytu dla RAID1.
        Dane są odczytywane z pierwszego dostępnego (nieuszkodzonego) dysku.
        """
        for i in range(self.num_disks):
            self.semaphores[i].acquire()
            try:
                start_idx = sector_number * self.sector_size
                data = bytes(self.shared_memory[i][start_idx:start_idx + self.sector_size])
                return data
            except Exception as e:
                logging.warning(f"RAID1 read failed on disk {i}: {e}")
            finally:
                self.semaphores[i].release()

        logging.error("RAID1 read failed: no functional disks")
        return None

    def _read_raid3(self, sector_number: int) -> Optional[bytes]:
        """
        Implementacja odczytu dla RAID3.
        Odczyt danych z dysków, regeneracja w razie potrzeby.
        Ostatni dysk jest dyskiem parzystości.
        """
        if self.num_disks < 2:
            logging.error("RAID3 requires at least 2 disks.")
            return None

        data_disks = self.num_disks - 1
        stripe_size = self.sector_size

        parity = bytearray(stripe_size)
        result = bytearray()
        failed_disk_idx = -1

        # Najpierw wczytujemy dane z dysków „danych”
        for i in range(data_disks):
            self.semaphores[i].acquire()
            try:
                start_idx = sector_number * stripe_size
                stripe_data = self.shared_memory[i][start_idx:start_idx + stripe_size]
                result.extend(stripe_data)
                # XOR w locie do parzystości
                for j in range(stripe_size):
                    parity[j] ^= stripe_data[j]
            except Exception as e:
                failed_disk_idx = i
                logging.warning(f"RAID3 read: disk {i} failed during read: {e}")
                # Zapisz informację, który dysk padł i spróbujemy zrekonstruować
            finally:
                self.semaphores[i].release()

        # Jeśli któryś dysk danych jest uszkodzony, odczytujemy parzystość i rekonstruujemy
        if failed_disk_idx != -1:
            parity_disk = self.num_disks - 1
            self.semaphores[parity_disk].acquire()
            try:
                start_idx = sector_number * stripe_size
                parity_data = self.shared_memory[parity_disk][start_idx:start_idx + stripe_size]
                # Miejsce w result, gdzie powinna być partia z failed_disk_idx
                offset = failed_disk_idx * stripe_size
                # Nadpisz surowe dane w result danymi z parzystości
                for j in range(stripe_size):
                    # Startowo przypisz bajt z parzystości
                    result[offset + j] = parity_data[j]
                    # XOR z innymi dyskami (oprócz uszkodzonego), żeby odtworzyć oryginał
                    for k in range(data_disks):
                        if k != failed_disk_idx:
                            idx_k = k * stripe_size + j
                            result[offset + j] ^= result[idx_k]
            except Exception as e:
                logging.error(f"RAID3 read failed during parity reconstruction: {e}")
                return None
            finally:
                self.semaphores[parity_disk].release()

        return bytes(result)

    # Metody "pomocnicze" do obsługi w razie potrzeby
    def stop_disks(self):
        """
        Aktualnie nie tworzymy żadnych procesów, więc nic nie zatrzymujemy.
        Zostawiamy metodę w razie przyszłej rozbudowy.
        """
        logging.info("All disk processes would stop here if they existed.")
