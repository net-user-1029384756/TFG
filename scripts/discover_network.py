import sys
import os

# Añadir ruta para poder importar desde src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modules.scanner import NetworkScanner

def run_discovery():
    """
    Gestiona el proceso de descubrimiento de red interactuando con el usuario.
    """
    print("=== MÓDULO DE DESCUBRIMIENTO DE RED (Nmap) ===")
    
    # Pedir al usuario el rango de red
    default_range = "192.168.56.0/24"
    network_range = input(f" > Introduce el rango de red a escanear (ej. {default_range}): ")
    if not network_range:
        network_range = default_range
        print(f"   [i] Usando rango por defecto: {network_range}")

    # Preguntar si se desea detección de SO
    os_detect_choice = input(" > ¿Intentar detección de Sistema Operativo? (s/N): ").lower()
    use_os_detection = os_detect_choice == 's'
    if use_os_detection:
        print("   [!] AVISO: La detección de SO requiere privilegios de administrador y puede ser lenta.")

    # Crear el scanner y lanzar el descubrimiento
    scanner = NetworkScanner()
    devices = scanner.discover_devices(network_range, with_os_detection=use_os_detection)

    if not devices:
        print("[i] No se encontraron dispositivos o el escaneo falló.")
        return

    # Imprimir los resultados en una tabla bonita
    print("--- RESULTADOS DEL ESCANEO ---")
    # Imprimir cabecera
    header = f"{'IP':<18}{'HOSTNAME':<25}{'ESTADO':<10}"
    if use_os_detection:
        header += f"{'SISTEMA OPERATIVO':<30}{'PRECISIÓN':<10}"
    print(header)
    print("=" * 90)

    for device in devices:
        line = f"{device.get('ip', 'N/A'):<18}{device.get('hostname', 'N/A'):<25}{device.get('status', 'N/A'):<10}"
        if use_os_detection:
            os_name = device.get('os', 'Desconocido')
            os_accuracy = f"{device.get('os_accuracy', 'N/A')}%"
            line += f"{os_name:<30}{os_accuracy:<10}"
        print(line)

if __name__ == '__main__':
    run_discovery()
