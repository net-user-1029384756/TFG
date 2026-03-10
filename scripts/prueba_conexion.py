from netmiko import ConnectHandler

# 1. Definimos el dispositivo (Tu router Mikrotik)
mikrotik_router = {
    'device_type': 'mikrotik_routeros',
    'host':   '192.168.56.10',
    'username': 'admin',
    'password': 'admin',
    'port': 22,
}

print("[-] Conectando al router R-SUCURSAL-01...")

try:
    # 2. Establecer conexión SSH
    net_connect = ConnectHandler(**mikrotik_router)
    print("[+] ¡Conexión SSH exitosa!")

    # 3. Enviar un comando simple
    output = net_connect.send_command("/system identity print")
    
    print("\n--- RESPUESTA DEL ROUTER ---")
    print(output)
    print("----------------------------")
    
    # 4. Cerrar
    net_connect.disconnect()

except Exception as e:
    print(f"[!] Error fatal: {e}")