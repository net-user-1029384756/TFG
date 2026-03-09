from abc import ABC, abstractmethod
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException

class BaseDevice(ABC):
    """Clase base abstracta para todos los dispositivos (de red y clientes)."""
    def __init__(self, ip, username, password, device_type, hostname=None):
        self.ip = ip
        self.username = username
        self.password = password
        self.device_type = device_type
        self.hostname = hostname if hostname else "Unknown"
        self.connection = None

    def __enter__(self):
        if self.connect():
            return self
        raise ConnectionError(f"No se pudo establecer la conexión con {self.hostname} ({self.ip})")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    @abstractmethod
    def connect(self):
        """Establece la conexión con el dispositivo."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        """Cierra la conexión con el dispositivo."""
        raise NotImplementedError

    @abstractmethod
    def send_command(self, command):
        """Envía un comando y devuelve la salida."""
        raise NotImplementedError


class NetmikoDevice(BaseDevice):
    """Clase base para dispositivos de red gestionados con Netmiko."""
    def connect(self):
        print(f"[*] Conectando a {self.hostname} ({self.ip}) con Netmiko...")
        try:
            # Netmiko utiliza 'host' en lugar de 'ip'
            device_params = {
                'device_type': self.device_type,
                'host': self.ip,
                'username': self.username,
                'password': self.password,
                'port': 22,  # Puerto estándar SSH, se puede sobreescribir
            }
            self.connection = ConnectHandler(**device_params)
            
            if self.hostname == "Unknown":
                self.hostname = self.connection.find_prompt()

            print(f"[+] Conectado exitosamente a: {self.hostname}")
            return True
        except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
            print(f"[!] Error de conexión en {self.ip}: {e}")
            self.connection = None
            return False
        except Exception as e:
            print(f"[!] Error inesperado durante la conexión a {self.ip}: {e}")
            self.connection = None
            return False

    def disconnect(self):
        if self.connection:
            self.connection.disconnect()
            print(f"[-] Desconectado de {self.hostname} ({self.ip})")
            self.connection = None

    def send_command(self, command):
        if not self.connection:
            print("[!] No hay conexión activa.")
            return None
        
        print(f"    > Ejecutando en {self.hostname}: {command}")
        try:
            output = self.connection.send_command(command)
            return output
        except Exception as e:
            print(f"[!] Error al ejecutar comando en {self.hostname}: {e}")
            return None

    def send_config(self, config_commands):
        if not self.connection:
            print("[!] No hay conexión activa.")
            return None
        
        print(f"    > Aplicando configuración en {self.hostname} ({len(config_commands)} comandos)...")
        try:
            output = self.connection.send_config_set(config_commands)
            return output
        except Exception as e:
            print(f"[!] Error aplicando configuración en {self.hostname}: {e}")
            return None


class MikrotikDevice(NetmikoDevice):
    """Clase específica para dispositivos Mikrotik RouterOS."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # No se necesita lógica adicional por ahora, hereda todo de NetmikoDevice.
        # Se mantiene por si en el futuro se necesita una función específica de Mikrotik.
        pass


class CiscoIosDevice(NetmikoDevice):
    """Clase específica para dispositivos Cisco IOS."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Lógica específica de Cisco si fuera necesaria
        pass

    def send_config(self, config_commands):
        """
        Método sobreescrito para usar el modo de configuración de Cisco.
        """
        if not self.connection:
            print("[!] No hay conexión activa.")
            return None
        
        print(f"    > Entrando en modo de configuración en {self.hostname}...")
        try:
            # En Cisco es común entrar en modo de configuración primero
            self.connection.enable()
            output = self.connection.send_config_set(config_commands)
            self.connection.exit_config_mode()
            print(f"    > Configuración aplicada en {self.hostname}.")
            return output
        except Exception as e:
            print(f"[!] Error aplicando configuración en {self.hostname}: {e}")
            return None
