import nmap
import sys

class NetworkScanner:
    """
    Encapsula la funcionalidad de escaneo de red utilizando python-nmap.
    """
    def __init__(self):
        """Inicializa el PortScanner de nmap."""
        try:
            self.nm = nmap.PortScanner()
        except nmap.PortScannerError:
            print("[!] Error: Nmap no se encuentra en el sistema. Asegúrate de que está instalado y en el PATH.")
            sys.exit(1)

    def discover_devices(self, network_range='192.168.1.0/24', with_os_detection=False):
        """
        Descubre dispositivos en un rango de red y opcionalmente detecta su SO.

        Args:
            network_range (str): El rango de red a escanear (ej. '192.168.1.0/24').
            with_os_detection (bool): Si es True, intenta la detección de SO (requiere privilegios de admin/root).

        Returns:
            list: Una lista de diccionarios, cada uno representando un dispositivo.
        """
        print(f"\n[*] Escaneando la red {network_range}...")
        
        arguments = '-sn -T4' # Escaneo de ping rápido por defecto
        if with_os_detection:
            print("[i] Se intentará la detección de SO (puede requerir sudo/admin y tardar más)...")
            # -O para detección de SO
            # -T4 para un escaneo más agresivo/rápido
            arguments = '-O -T4'

        try:
            self.nm.scan(hosts=network_range, arguments=arguments)
        except nmap.PortScannerError as e:
            print(f"[!] Error durante el escaneo: {e}")
            print("[!] La detección de SO (-O) a menudo requiere privilegios de administrador.")
            print("[!] Intenta ejecutar el script como administrador/root o deshabilita la detección de SO.")
            return []
            
        discovered_devices = []
        for host in self.nm.all_hosts():
            device_info = {
                'ip': host,
                'status': self.nm[host].state(),
                'hostname': self.nm[host].hostname() if self.nm[host].hostname() else 'N/A'
            }
            
            if with_os_detection and 'osmatch' in self.nm[host] and self.nm[host]['osmatch']:
                # Nmap devuelve una lista de posibles SO, tomamos el más probable
                os_match = self.nm[host]['osmatch'][0]
                device_info['os'] = os_match['name']
                device_info['os_accuracy'] = os_match['accuracy']
            
            discovered_devices.append(device_info)
        
        print(f"[+] Escaneo completado. Se encontraron {len(discovered_devices)} dispositivos activos.")
        return discovered_devices

# --- Ejemplo de uso ---
if __name__ == '__main__':
    scanner = NetworkScanner()
    
    # Escaneo simple sin detección de SO
    devices_ping = scanner.discover_devices('192.168.56.0/24')
    if devices_ping:
        print("\n--- Resultados (Ping Scan) ---")
        for device in devices_ping:
            print(f"  - IP: {device['ip']}, Hostname: {device['hostname']}, Estado: {device['status']}")
            
    # Escaneo con detección de SO (requiere privilegios)
    # Nota: Este escaneo puede fallar si no se ejecuta como administrador.
    devices_os = scanner.discover_devices('192.168.56.0/24', with_os_detection=True)
    if devices_os:
        print("\n--- Resultados (OS Detection Scan) ---")
        for device in devices_os:
            os_info = f", SO: {device.get('os', 'Desconocido')} (Precisión: {device.get('os_accuracy', 'N/A')}%)" if 'os' in device else ""
            print(f"  - IP: {device['ip']}, Hostname: {device['hostname']}{os_info}")
