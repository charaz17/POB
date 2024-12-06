import threading
import socket

class Disk(threading.Thread):
    def __init__(self, port, disk_id):
        super().__init__()
        self.port = port
        self.disk_id = disk_id
        self.active = True
        self.data = [""] * 128  # 128 sektorów danych
        self.stats = {"reads": 0, "writes": 0, "errors": 0, "sent": 0, "received": 0}

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', self.port))
            s.settimeout(1)  # Timeout, aby nie blokować zamykania
            s.listen()
            print(f"Dysk {self.disk_id} oczekuje na połączenie na porcie {self.port}")
            while self.active:
                try:
                    conn, _ = s.accept()
                    with conn:
                        while self.active:
                            data = conn.recv(1024)
                            if not data or not self.active:
                                break
                            command, *params = data.decode().split(":")
                            if command == "write":
                                self.write_data(params[0])
                            elif command == "read":
                                self.read_data()
                            elif command == "inject_fault":
                                self.inject_fault(params[0])
                            elif command == "receive":
                                self.receive_data(params[0], params[1])
                except socket.timeout:
                    continue

    def receive_data(self, sender_id, data):
        """Obsługa odbioru danych od innego dysku."""
        if self.stats["errors"] > 0:  # Jeśli występuje błąd, nie zapisujemy
            print(f"Dysk {self.disk_id}: Odrzucono dane z Dysku {sender_id} z powodu błędu")
            return
        self.stats["received"] += 1
        self.write_data(data)
        print(f"Dysk {self.disk_id} otrzymał dane od Dysku {sender_id}: '{data}'")

    def write_data(self, data):
        self.stats["writes"] += 1
        self.data[0] = data
        print(f"Dysk {self.disk_id} zapisuje dane: {data}")

    def send_data(self, target_disk_port, data):
        """Wysyła dane do innego dysku."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', target_disk_port))
                s.sendall(f"receive:{self.disk_id}:{data}".encode())
                self.stats["sent"] += 1
                print(f"Dysk {self.disk_id} wysyła dane: '{data}' do Dysku na porcie {target_disk_port}")
        except Exception as e:
            print(f"Błąd podczas wysyłania danych z Dysku {self.disk_id} do portu {target_disk_port}: {e}")

    def stop(self):
        print(f"Zatrzymywanie dysku {self.disk_id}")
        self.active = False
