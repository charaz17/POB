class RAIDController:
    def __init__(self, disks):
        self.disks = disks

    def start_disks(self):
        for disk in self.disks:
            disk.start()

    def stop_disks(self):
        for disk in self.disks:
            disk.stop()
        for disk in self.disks:
            disk.join()
        print("Wszystkie dyski zostały zatrzymane.")

    def exchange_data(self, sender_id, receiver_id, data):
        """Przesyłanie danych między dyskami."""
        sender_disk = self.disks[sender_id]
        receiver_disk = self.disks[receiver_id]
        sender_disk.send_data(receiver_disk.port, data)

    def get_stats(self):
        """Zwraca statystyki każdego dysku."""
        return {i: disk.stats for i, disk in enumerate(self.disks)}
