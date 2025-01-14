import json
import socket
import threading
from dataclasses import dataclass, asdict
from typing import Dict, Optional
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
        """
        Obsługuje komunikację sieciową między kontrolerem RAID a procesami dysków.

        Args:
            host: Adres hosta serwera sieciowego.
            port: Port serwera sieciowego.
        """
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[int, socket.socket] = {}
        self.running = True

    def start_server(self):
        """
        Uruchamia serwer sieciowy do obsługi komunikacji z procesami dysków.
        """
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        threading.Thread(target=self._accept_connections, daemon=True).start()
        print(f"Server started on {self.host}:{self.port}")

    def _accept_connections(self):
        """
        Akceptuje połączenia od klientów (dysków) i rejestruje je.
        """
        while self.running:
            try:
                client, _ = self.socket.accept()
                disk_id = len(self.clients)
                self.clients[disk_id] = client
                threading.Thread(target=self._handle_client, args=(client, disk_id), daemon=True).start()
                print(f"Disk {disk_id} connected.")
            except Exception as e:
                print(f"Error accepting connection: {e}")

    def _handle_client(self, client: socket.socket, disk_id: int):
        """
        Obsługuje komunikację z pojedynczym dyskiem.

        Args:
            client: Obiekt socket reprezentujący połączenie z dyskiem.
            disk_id: Identyfikator dysku.
        """
        while self.running:
            try:
                data = client.recv(1024)
                if not data:
                    break
                message = DiskMessage(**json.loads(data.decode()))
                self.handle_message(message)
            except Exception as e:
                print(f"Error handling client {disk_id}: {e}")
                break
        client.close()
        del self.clients[disk_id]
        print(f"Disk {disk_id} disconnected.")

    def handle_message(self, message: DiskMessage):
        """
        Obsługuje odebrane wiadomości od dysków.

        Args:
            message: Wiadomość odebrana od dysku.
        """
        print(f"Received message: {message}")
        # Tutaj należy zaimplementować logikę obsługi wiadomości

    def send_message(self, disk_id: int, message: DiskMessage) -> bool:
        """
        Wysyła wiadomość do określonego dysku.

        Args:
            disk_id: Identyfikator docelowego dysku.
            message: Obiekt wiadomości do wysłania.

        Returns:
            bool: True, jeśli wiadomość została pomyślnie wysłana, False w przeciwnym razie.
        """
        if disk_id in self.clients:
            try:
                self.clients[disk_id].send(json.dumps(asdict(message)).encode())
                print(f"Message sent to Disk {disk_id}: {message}")
                return True
            except Exception as e:
                print(f"Error sending message to Disk {disk_id}: {e}")
        return False

    def stop(self):
        """
        Zatrzymuje serwer i zamyka wszystkie połączenia.
        """
        self.running = False
        self.socket.close()
        for client in self.clients.values():
            client.close()
        print("Server stopped.")