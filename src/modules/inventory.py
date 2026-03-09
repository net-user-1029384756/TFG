"""
Módulo para gestionar el inventario de dispositivos de red.
"""
import csv

def get_devices(inventory_file='inventory/devices.csv'):
    """
    Lee el archivo de inventario CSV y devuelve una lista de dispositivos.

    Args:
        inventory_file (str): Ruta al archivo CSV del inventario.

    Returns:
        list: Una lista de diccionarios, donde cada diccionario representa un dispositivo.
    """
    try:
        with open(inventory_file, mode='r') as f:
            reader = csv.DictReader(f)
            devices = []
            for row in reader:
                row['device_type'] = row.pop('type')
                devices.append(row)
            return devices
    except FileNotFoundError:
        print(f"[!] Error: El archivo de inventario '{inventory_file}' no fue encontrado.")
        return []
    except Exception as e:
        print(f"[!] Error inesperado al leer el inventario: {e}")
        return []
