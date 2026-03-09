import sys
import os
import datetime

# Ajuste de ruta para importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modules.device_manager_factory import create_device
from src.modules.inventory import get_devices

BACKUP_DIR = 'backups'

def save_to_file(hostname, data):
    # Crear nombre de archivo con fecha: R-SUCURSAL-01_2026-02-02_1830.rsc
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"{hostname}_{now}.rsc"
    filepath = os.path.join(BACKUP_DIR, filename)
    
    # Asegurar que existe la carpeta
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    with open(filepath, 'w') as f:
        f.write(data)
    
    print(f"    [Disk] Guardado en: {filepath}")

def run_backup():
    print("=== SISTEMA DE COPIAS DE SEGURIDAD AUTOMATIZADO ===")
    
    devices = get_devices()
    if not devices:
        return

    for device_info in devices:
        print(f"\n--- Realizando backup de {device_info['hostname']} ---")
        try:
            with create_device(**device_info) as router:
                # Comando para sacar toda la configuración en texto plano
                # 'show-sensitive' es importante para ver algunas claves (aunque Mikrotik v7 oculta las passwords igual)
                full_config = router.send_command("/export show-sensitive")
                
                if full_config:
                    save_to_file(router.hostname, full_config)
                else:
                    print("    [!] Error: Configuración vacía recibida.")
        except ConnectionError as e:
            print(f"    [!] {e}")

if __name__ == "__main__":
    run_backup()