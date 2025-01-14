#/disk/networked_disk.py

from disk.disk import Disk
import socket
import json
import threading
from network.messages import DiskMessage

class NetworkedDisk(Disk):
    def __init__(self, disk_id: int, sector_size: int = 32, sector_count: int = 128):
        super().__init__(disk_id, sector_size, sector_count)
        self.stats = DiskStats()
        self.network = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def connect_to_controller(self, host: str, port: int):
        try:
            self.network.connect((host, port))
            self.connected = True
            threading.Thread(target=self._listen_for_messages).start()
        except:
            self.connected = False

    def _listen_for_messages(self):
        while self.connected:
            try:
                data = self.network.recv(1024)
                if not data:
                    break
                message = DiskMessage(**json.loads(data.decode()))
                self._handle_message(message)
            except:
                break
        self.connected = False

    def _handle_message(self, message: DiskMessage):
        start_time = time.time()
        try:
            if message.operation == 'read':
                sector = self.read_sector(message.sector)
                response = DiskMessage('read_response', self.disk_id, 
                                    data=sector.data if sector else None)
            elif message.operation == 'write':
                success = self.write_sector(message.sector, message.data)
                response = DiskMessage('write_response', self.disk_id, data=success)
        except Exception as e:
            response = DiskMessage('error', self.disk_id, data=str(e))

        latency = time.time() - start_time
        self.stats.add_operation(message.operation, len(message.data) if message.data else 0, latency)
        
        if self.connected:
            self.network.send(json.dumps(asdict(response)).encode())
