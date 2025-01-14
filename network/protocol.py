#/network/protocol.py


import json
import socket
import threading
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import time

@dataclass
class DiskMessage:
    operation: str  # 'read', 'write', 'status', 'error'
    disk_id: int
    sector: Optional[int] = None
    data: Optional[bytes] = None
    timestamp: float = time.time()

class NetworkProtocol:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[int, socket.socket] = {}
        self.running = True

    def start_server(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        threading.Thread(target=self._accept_connections).start()

    def _accept_connections(self):
        while self.running:
            try:
                client, addr = self.socket.accept()
                disk_id = len(self.clients)
                self.clients[disk_id] = client
                threading.Thread(target=self._handle_client, args=(client, disk_id)).start()
            except:
                break

    def _handle_client(self, client: socket.socket, disk_id: int):
        while self.running:
            try:
                data = client.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode())
                self.handle_message(DiskMessage(**message))
            except:
                break
        client.close()
        del self.clients[disk_id]

    def send_message(self, disk_id: int, message: DiskMessage):
        if disk_id in self.clients:
            try:
                self.clients[disk_id].send(json.dumps(asdict(message)).encode())
                return True
            except:
                return False
        return False

    def stop(self):
        self.running = False
        self.socket.close()
        for client in self.clients.values():
            client.close()
