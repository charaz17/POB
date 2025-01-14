import sys
import logging
from PyQt6.QtWidgets import QApplication
from network.protocol import NetworkProtocol
from controller.raid_controller import RAIDController
from gui.raid_interface import RAIDSimulatorGUI

def initialize_components():
    """
    Inicjalizuje wszystkie komponenty aplikacji, takie jak protokół sieciowy i kontroler RAID.
    """
    logging.info("Starting Network Protocol...")
    network = NetworkProtocol()
    network.start_server()

    logging.info("Initializing RAID Controller...")
    # Uproszczona wersja: RAID0, 4 dyski
    controller = RAIDController('RAID0', num_disks=4)
    return network, controller

def shutdown_components(network, controller):
    """
    Zamyka wszystkie komponenty aplikacji w bezpieczny sposób.
    """
    logging.info("Shutting down components...")
    try:
        if network:
            network.stop()
        if controller:
            controller.stop_disks()
    except Exception as shutdown_error:
        logging.error(f"Error during shutdown: {shutdown_error}")
    logging.info("Application closed.")

def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    network, controller = None, None

    try:
        network, controller = initialize_components()

        logging.info("Launching GUI...")
        app = QApplication(sys.argv)
        window = RAIDSimulatorGUI(controller)
        window.show()

        logging.info("Starting Application Loop...")
        sys.exit(app.exec())

    except Exception as e:
        logging.error(f"An error occurred: {e}")

    finally:
        shutdown_components(network, controller)

if __name__ == '__main__':
    main()
