import unittest
import sys
import os
from unittest.mock import patch, mock_open

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.modules.inventory import get_devices
from scripts.deploy_ospf import get_ospf_config

class TestLogic(unittest.TestCase):
    """Pruebas para la lógica de inventario y generación de comandos OSPF."""

    @patch('builtins.open', new_callable=mock_open, read_data="name,hostname,type\nrouter1,192.168.1.1,mikrotik_routeros\n")
    @patch('csv.DictReader')
    def test_get_devices(self, mock_csv, mock_file):
        """Verifica que el inventario CSV se parsea correctamente."""
        # Simulamos la lectura del CSV
        mock_csv.return_value = [{'name': 'router1', 'hostname': '192.168.1.1', 'type': 'mikrotik_routeros'}]
        devices = get_devices('dummy_path.csv')
        
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['device_type'], 'mikrotik_routeros')
        self.assertNotIn('type', devices[0]) # Asegura que la clave 'type' se cambió a 'device_type'
        print("[PASS] test_get_devices")

    def test_get_ospf_config_sucursal(self):
        """Verifica que se generen los comandos OSPF correctos para una sucursal."""
        comandos = get_ospf_config("R-SUCURSAL-01")
        self.assertTrue(any("router-id=1.1.1.1" in cmd for cmd in comandos))
        self.assertTrue(any("192.168.10.0/24" in cmd for cmd in comandos))
        print("[PASS] test_get_ospf_config_sucursal")

if __name__ == '__main__':
    unittest.main(verbosity=2)