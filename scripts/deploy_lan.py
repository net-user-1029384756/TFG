import sys
import os

# Truco para importar módulos desde la carpeta superior
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modules.device_manager_factory import create_device
from src.modules.inventory import get_devices

def get_lan_config(hostname):
    """Define la configuración según el nombre del router"""
    commands = []
    
    # Comandos comunes para Mikrotik (Crear interfaz Bridge Loopback)
    # Nota: Usamos /interface/bridge/add con un nombre específico para evitar duplicados si se lanza 2 veces
    # SUGERENCIA DE IDEMPOTENCIA: En un script real, antes de añadir, comprobaríamos si ya existe.
    # Por ejemplo, con un comando find: "/interface/bridge/print [find name=LAN_BRIDGE]"
    # y solo si no devuelve nada, ejecutaríamos el 'add'.
    commands.append("/interface/bridge/add name=LAN_BRIDGE comment=Creado_por_Python")
    
    if "SUCURSAL" in hostname:
        # Configuración para la SUCURSAL (Red 10.0)
        commands.append("/ip/address/add address=192.168.10.1/24 interface=LAN_BRIDGE network=192.168.10.0")
        print(f"    [i] Configuración cargada: PERFIL SUCURSAL (192.168.10.1)")
        
    elif "CORE" in hostname:
        # Configuración para el CORE (Red 20.0)
        commands.append("/ip/address/add address=192.168.20.1/24 interface=LAN_BRIDGE network=192.168.20.0")
        print(f"    [i] Configuración cargada: PERFIL CORE (192.168.20.1)")
        
    return commands

def run_deploy_lan():
    print("=== DESPLIEGUE AUTOMATIZADO DE LANs ===")
    
    devices = get_devices()
    if not devices:
        return

    for device_info in devices:
        print(f"\n--- Configurando {device_info['hostname']} ---")
        try:
            with create_device(**device_info) as router:
                # 1. Obtener los comandos para este router
                config_list = get_lan_config(router.hostname)
                
                # 2. Aplicar configuración
                output = router.send_config(config_list)
                
                print("    [v] Resultado del router:")
                print(output)
                
                # 3. Verificación rápida
                check = router.send_command("/ip address print where interface=LAN_BRIDGE")
                print("\n    [?] Verificación:")
                print(check)
        except ConnectionError as e:
            print(f"    [!] {e}")

if __name__ == "__main__":
    run_deploy_lan()