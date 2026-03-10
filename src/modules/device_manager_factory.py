"""
Módulo Factory para la creación de objetos de dispositivo (de red y clientes).
Este patrón de diseño permite desacoplar la creación de objetos de su uso,
facilitando la adición de nuevos tipos de dispositivos sin modificar el código que los utiliza.
"""

# Importación de las clases de dispositivos de sus respectivos módulos
from .network_device import MikrotikDevice, CiscoIosDevice
from .client_device import LinuxClient, WindowsClient

# Mapeo centralizado de 'device_type' a la clase constructora correspondiente.
# Esta es la única sección que necesita ser modificada para añadir soporte a un nuevo hardware.
DEVICE_MAP = {
    # Dispositivos de Red
    'mikrotik_routeros': MikrotikDevice,
    'cisco_ios': CiscoIosDevice,
    
    # Equipos Cliente
    'linux': LinuxClient,
    'windows': WindowsClient,
}

def create_device(**device_info):
    """
    Crea una instancia de un objeto de dispositivo basado en su 'device_type'.

    Args:
        device_info (dict): Un diccionario que contiene toda la información necesaria
                            para inicializar el dispositivo (IP, credenciales, etc.).
                            Debe incluir la clave 'device_type'.

    Returns:
        Una instancia de una subclase de BaseDevice o ClientDevice si el tipo es soportado.
        Devuelve None si el 'device_type' no se encuentra en DEVICE_MAP o no se especifica.
    """
    device_type = device_info.get('device_type')
    
    if not device_type:
        hostname = device_info.get('hostname', 'N/A')
        print(f"[!] Error: 'device_type' no especificado para el dispositivo '{hostname}'.")
        return None

    # Busca la clase correspondiente en el mapa
    device_class = DEVICE_MAP.get(device_type)

    if not device_class:
        print(f"[!] Error: El tipo de dispositivo '{device_type}' no es soportado por el factory.")
        return None

    # Crea y devuelve una instancia de la clase encontrada, pasando toda la información
    print(f"[*] Factory: Creando instancia para el tipo '{device_type}'...")
    return device_class(**device_info)

# --- Ejemplo de uso (se puede ejecutar este fichero para probar) ---
if __name__ == '__main__':
    print("--- Probando el Device Manager Factory ---")
    
    # 1. Información de un dispositivo Mikrotik
    mikrotik_data = {
        'ip': '192.168.1.1',
        'username': 'admin',
        'password': 'password',
        'device_type': 'mikrotik_routeros',
        'hostname': 'Router-Mikrotik'
    }
    
    # 2. Información de un cliente Linux
    linux_data = {
        'ip': '192.168.1.100',
        'username': 'user',
        'password': 'password',
        'device_type': 'linux',
        'hostname': 'Servidor-Web'
    }

    # 3. Información de un tipo no soportado
    unsupported_data = {
        'ip': '10.0.0.1',
        'username': 'admin',
        'password': 'password',
        'device_type': 'juniper_junos',
        'hostname': 'FW-Juniper'
    }

    # Creación de los dispositivos
    mikrotik_dev = create_device(**mikrotik_data)
    linux_client = create_device(**linux_data)
    unsupported_dev = create_device(**unsupported_data)

    print("\n--- Resultados ---")
    print(f"Dispositivo Mikrotik creado: {mikrotik_dev}")
    print(f"Cliente Linux creado: {linux_client}")
    print(f"Dispositivo no soportado: {unsupported_dev}")

    if mikrotik_dev:
        print(f"Tipo de objeto para Mikrotik: {type(mikrotik_dev)}")
    
    if linux_client:
        print(f"Tipo de objeto para Linux: {type(linux_client)}")

