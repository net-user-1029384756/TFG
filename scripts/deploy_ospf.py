import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modules.device_manager_factory import create_device
from src.modules.inventory import get_devices

def get_ospf_config(hostname):
    commands = []
    
    # Definimos variables según el router
    if "SUCURSAL" in hostname:
        router_id = "1.1.1.1"
        my_lan_network = "192.168.10.0/24"
    elif "CORE" in hostname:
        router_id = "2.2.2.2"
        my_lan_network = "192.168.20.0/24"
    else:
        return []

    # --- COMANDOS MIKROTIK v7 OSPF ---
    
    # 1. Crear la Instancia OSPF (El proceso principal)
    commands.append(f"/routing/ospf/instance/add name=ospf-instance-1 version=2 router-id={router_id}")
    
    # 2. Crear el Área Backbone (Área 0)
    commands.append("/routing/ospf/area/add name=backbone-area instance=ospf-instance-1 area-id=0.0.0.0")
    
    # 3. Anunciar redes (Interface Templates en v7)
    # Anunciamos la WAN (común a todos)
    commands.append("/routing/ospf/interface-template/add area=backbone-area networks=10.0.0.0/30")
    
    # Anunciamos nuestra LAN interna específica
    commands.append(f"/routing/ospf/interface-template/add area=backbone-area networks={my_lan_network}")
    
    return commands

def run_deploy_ospf():
    print("=== DESPLIEGUE DE ENRUTAMIENTO OSPF (v7) ===")
    
    devices = get_devices()
    if not devices:
        return

    for device_info in devices:
        print(f"\n--- Configurando OSPF en {device_info['hostname']} ---")
        try:
            with create_device(**device_info) as router:
                config = get_ospf_config(router.hostname)
                output = router.send_config(config)
                print("    [v] Comandos enviados.")
                
                # Verificación rápida de vecinos OSPF
                import time
                time.sleep(2) # Damos un respiro para que negocien
                neighbor = router.send_command("/routing/ospf/neighbor/print")
                print("\n    [?] Estado de Vecinos OSPF:")
                print(neighbor)
        except ConnectionError as e:
            print(f"    [!] {e}")

if __name__ == "__main__":
    run_deploy_ospf()