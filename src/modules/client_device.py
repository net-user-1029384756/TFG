import paramiko
import winrm
from abc import ABC, abstractmethod

class ClientDevice(ABC):
    """Clase base abstracta para equipos cliente (Windows, Linux)."""
    def __init__(self, ip, username, password, device_type, hostname=None):
        self.ip = ip
        self.username = username
        self.password = password
        self.device_type = device_type
        self.hostname = hostname if hostname else "Unknown"
        self.session = None

    def __enter__(self):
        if self.connect():
            return self
        raise ConnectionError(f"No se pudo conectar a {self.hostname} ({self.ip})")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    @abstractmethod
    def connect(self):
        """Establece la conexión con el cliente."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        """Cierra la conexión con el cliente."""
        raise NotImplementedError

    @abstractmethod
    def execute_command(self, command):
        """Ejecuta un comando en el cliente."""
        raise NotImplementedError


class LinuxClient(ClientDevice):
    """Clase para gestionar clientes Linux vía SSH con Paramiko."""
    def connect(self):
        print(f"[*] Conectando a cliente Linux {self.hostname} ({self.ip}) con Paramiko...")
        try:
            self.session = paramiko.SSHClient()
            self.session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.session.connect(
                self.ip,
                username=self.username,
                password=self.password,
                timeout=5
            )
            print(f"[+] Conectado exitosamente a {self.hostname}")
            return True
        except paramiko.AuthenticationException:
            print(f"[!] Error de autenticación en {self.ip}.")
            return False
        except Exception as e:
            print(f"[!] Error de conexión en {self.ip}: {e}")
            return False

    def disconnect(self):
        if self.session:
            self.session.close()
            print(f"[-] Desconectado de {self.hostname} ({self.ip})")

    def execute_command(self, command):
        if not self.session:
            print("[!] No hay conexión activa.")
            return None
        
        print(f"    > Ejecutando en {self.hostname}: {command}")
        try:
            stdin, stdout, stderr = self.session.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            if error:
                print(f"[!] Error en comando: {error}")
            return output
        except Exception as e:
            print(f"[!] Error al ejecutar comando en {self.hostname}: {e}")
            return None


class WindowsClient(ClientDevice):
    """Clase para gestionar clientes Windows vía WinRM."""
    def connect(self):
        print(f"[*] Conectando a cliente Windows {self.hostname} ({self.ip}) con PyWinRM...")
        try:
            self.session = winrm.Protocol(
                endpoint=f"http://{self.ip}:5985/wsman",
                transport_type='ntlm',
                username=self.username,
                password=self.password,
                server_cert_validation='ignore'
            )
            self.session.open_shell()
            print(f"[+] Conectado exitosamente a {self.hostname}")
            return True
        except Exception as e:
            print(f"[!] Error de conexión en {self.ip}: {e}")
            return False

    def disconnect(self):
        if self.session:
            self.session.close_shell()
            print(f"[-] Desconectado de {self.hostname} ({self.ip})")

    def execute_command(self, command):
        if not self.session:
            print("[!] No hay conexión activa.")
            return None
            
        print(f"    > Ejecutando en {self.hostname}: {command}")
        try:
            # Por simplicidad, se usa un solo comando. PowerShell es más potente.
            # Se recomienda usar 'powershell -Command "{command}"' para comandos complejos.
            r = self.session.run_cmd(command)
            output = r.std_out.decode('cp850', errors='ignore') # cp850 para consolas Windows en español
            error = r.std_err.decode('cp850', errors='ignore')
            if r.status_code != 0:
                print(f"[!] Error en comando (código {r.status_code}): {error}")
            return output
        except Exception as e:
            print(f"[!] Error al ejecutar comando en {self.hostname}: {e}")
            return None
