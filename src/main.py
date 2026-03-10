import sys
import os

# Ajuste de ruta para importar módulos del directorio raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.backup_network import run_backup
from scripts.deploy_lan import run_deploy_lan
from scripts.deploy_ospf import run_deploy_ospf
from scripts.discover_network import run_discovery
from scripts.deploy_dhcp import run_deploy_dhcp
from scripts.run_playbook import run_ansible_playbook

from src.modules.logger import log

def show_menu():
    """Muestra el menú de opciones al usuario."""
    print("\n" + "=" * 60)
    print(" AUTOMATIZACIÓN DE RED: MENÚ PRINCIPAL")
    print("=" * 60)
    print("1. Realizar copia de seguridad de todos los routers")
    print("2. Desplegar configuración LAN básica")
    print("3. Desplegar configuración OSPF")
    print("4. Descubrir dispositivos en la red")
    print("5. Desplegar servidor DHCP mediante Ansible")
    print("6. Configurar clientes Linux (Ansible)")   
    print("7. Configurar clientes Windows (Ansible)") 
    print("0. Salir")
    print("=" * 60)


def main():
    """Bucle principal que gestiona la interacción con el usuario."""
    while True:
        show_menu()
        choice = input(" > Selecciona una opción: ")

        if choice == '1':
            run_backup()
        elif choice == '2':
            run_deploy_lan()
        elif choice == '3':
            run_deploy_ospf()
        elif choice == '4':
            run_discovery()
        elif choice == '5':
            run_deploy_dhcp()
        elif choice == '6':
            log.info("\n[*] Desplegando configuración base en clientes Linux...")
            run_ansible_playbook(os.path.join('playbooks', 'setup_linux_client.yml'), inventory_source=os.path.join('inventory', 'ansible_hosts'))
        elif choice == '7':
            log.info("\n[*] Desplegando configuración base en clientes Windows...")
            run_ansible_playbook(os.path.join('playbooks', 'setup_windows_client.yml'), inventory_source=os.path.join('inventory', 'ansible_hosts'))
        elif choice == '0':
            print("\n[i] Saliendo del programa. ¡Hasta pronto!")
            sys.exit()
        else:
            print("\n[!] Opción no válida. Por favor, inténtalo de nuevo.")

        input("\n--- Pulsa Enter para continuar ---")


if __name__ == "__main__":
    main()
