import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Añadir el directorio raíz del proyecto a la ruta de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar las clases que vamos a probar
from src.modules.network_device import MikrotikDevice, CiscoIosDevice
from src.modules.client_device import LinuxClient, WindowsClient

class TestDeviceImplementations(unittest.TestCase):
    """
    Pruebas para las implementaciones de dispositivos.
    Se utiliza 'patch' de unittest.mock para simular las librerías de conexión
    y evitar conexiones de red reales durante las pruebas.
    """

    def setUp(self):
        """Datos de prueba comunes."""
        self.device_info = {
            'ip': '127.0.0.1',
            'username': 'test',
            'password': 'password',
            'hostname': 'test-device'
        }

    @patch('src.modules.network_device.ConnectHandler')
    def test_mikrotik_connect(self, mock_connect_handler):
        """Verifica que MikrotikDevice llama a ConnectHandler con los datos correctos."""
        device_info = self.device_info.copy()
        device_info['device_type'] = 'mikrotik_routeros'
        
        # El mock simula la conexión exitosa
        mock_instance = MagicMock()
        mock_instance.find_prompt.return_value = "Mikrotik-Test>"
        mock_connect_handler.return_value = mock_instance

        with MikrotikDevice(**device_info) as device:
            # Comprobar que se llamó a ConnectHandler con los argumentos esperados
            mock_connect_handler.assert_called_once_with(
                device_type='mikrotik_routeros',
                host='127.0.0.1',
                username='test',
                password='password',
                port=22
            )
            # Comprobar que el objeto de conexión se asignó
            self.assertIsNotNone(device.connection)
        
        # Comprobar que se llamó a la desconexión al salir del 'with'
        mock_instance.disconnect.assert_called_once()
        print(f"\n[PASS] test_mikrotik_connect")

    @patch('src.modules.client_device.paramiko')
    def test_linux_client_connect(self, mock_paramiko):
        """Verifica que LinuxClient utiliza Paramiko para conectar."""
        device_info = self.device_info.copy()
        device_info['device_type'] = 'linux'
        
        mock_ssh_client = MagicMock()
        mock_paramiko.SSHClient.return_value = mock_ssh_client

        with LinuxClient(**device_info) as client:
            # Comprobar que se intentó crear un cliente SSH
            mock_paramiko.SSHClient.assert_called_once()
            # Comprobar que se llamó al método connect del cliente SSH
            mock_ssh_client.connect.assert_called_once_with(
                '127.0.0.1',
                username='test',
                password='password',
                timeout=5
            )
            self.assertIsNotNone(client.session)
        
        mock_ssh_client.close.assert_called_once()
        print(f"\n[PASS] test_linux_client_connect")

    @patch('src.modules.client_device.winrm.Protocol')
    def test_windows_client_connect(self, mock_protocol):
        """Verifica que WindowsClient utiliza pywinrm para conectar."""
        device_info = self.device_info.copy()
        device_info['device_type'] = 'windows'

        mock_session = MagicMock()
        mock_protocol.return_value = mock_session
        
        with WindowsClient(**device_info) as client:
            # Comprobar que se inicializó el protocolo WinRM
            mock_protocol.assert_called_once_with(
                endpoint='http://127.0.0.1:5985/wsman',
                transport_type='ntlm',
                username='test',
                password='password',
                server_cert_validation='ignore'
            )
            # Comprobar que se abrió la shell
            mock_session.open_shell.assert_called_once()
            self.assertIsNotNone(client.session)
            
        mock_session.close_shell.assert_called_once()
        print(f"\n[PASS] test_windows_client_connect")


if __name__ == '__main__':
    unittest.main(verbosity=2)
