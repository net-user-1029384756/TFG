import unittest
import sys
import os

# Añadir el directorio raíz del proyecto a la ruta de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modules.device_manager_factory import create_device
from src.modules.network_device import MikrotikDevice, CiscoIosDevice
from src.modules.client_device import LinuxClient, WindowsClient

class TestDeviceManagerFactory(unittest.TestCase):
    """Pruebas para el factory de creación de dispositivos."""

    def setUp(self):
        """Información de prueba común para los dispositivos."""
        self.device_data = {
            'ip': '127.0.0.1',
            'username': 'testuser',
            'password': 'testpassword'
        }

    def test_create_mikrotik_device(self):
        """Verifica que se cree correctamente un objeto MikrotikDevice."""
        device_info = self.device_data.copy()
        device_info['device_type'] = 'mikrotik_routeros'
        device = create_device(**device_info)
        self.assertIsInstance(device, MikrotikDevice, "El factory debería crear un objeto MikrotikDevice.")
        print(f"\n[PASS] test_create_mikrotik_device")

    def test_create_cisco_device(self):
        """Verifica que se cree correctamente un objeto CiscoIosDevice."""
        device_info = self.device_data.copy()
        device_info['device_type'] = 'cisco_ios'
        device = create_device(**device_info)
        self.assertIsInstance(device, CiscoIosDevice, "El factory debería crear un objeto CiscoIosDevice.")
        print(f"[PASS] test_create_cisco_device")

    def test_create_linux_client(self):
        """Verifica que se cree correctamente un objeto LinuxClient."""
        device_info = self.device_data.copy()
        device_info['device_type'] = 'linux'
        device = create_device(**device_info)
        self.assertIsInstance(device, LinuxClient, "El factory debería crear un objeto LinuxClient.")
        print(f"[PASS] test_create_linux_client")

    def test_create_windows_client(self):
        """Verifica que se cree correctamente un objeto WindowsClient."""
        device_info = self.device_data.copy()
        device_info['device_type'] = 'windows'
        device = create_device(**device_info)
        self.assertIsInstance(device, WindowsClient, "El factory debería crear un objeto WindowsClient.")
        print(f"[PASS] test_create_windows_client")

    def test_unsupported_device_type(self):
        """Verifica que el factory devuelva None para un tipo no soportado."""
        device_info = self.device_data.copy()
        device_info['device_type'] = 'unsupported_type'
        device = create_device(**device_info)
        self.assertIsNone(device, "El factory debería devolver None para tipos no soportados.")
        print(f"[PASS] test_unsupported_device_type")

    def test_no_device_type(self):
        """Verifica que el factory devuelva None si no se especifica 'device_type'."""
        device_info = self.device_data.copy()
        # No añadimos 'device_type'
        device = create_device(**device_info)
        self.assertIsNone(device, "El factory debería devolver None si no hay 'device_type'.")
        print(f"[PASS] test_no_device_type")

if __name__ == '__main__':
    # Esto permite ejecutar las pruebas directamente desde el terminal
    unittest.main(verbosity=2)
