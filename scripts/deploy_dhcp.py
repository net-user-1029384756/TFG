import sys
import os

# Añadir el directorio raíz del proyecto al sys.path para poder importar scripts.*
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.run_playbook import run_ansible_playbook


def run_deploy_dhcp():
    """
    Lanza el playbook de Ansible que despliega un servidor DHCP
    en los hosts definidos en 'inventory/ansible_hosts' (grupo [dhcp_servers]).
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    playbook_path = os.path.join(project_root, 'playbooks', 'deploy_dhcp.yml')
    inventory_path = os.path.join(project_root, 'inventory', 'ansible_hosts')

    print("=== DESPLIEGUE DE SERVIDOR DHCP MEDIANTE ANSIBLE ===")
    print(f"[*] Playbook : {playbook_path}")
    print(f"[*] Inventario: {inventory_path}")

    # Usamos conexión 'smart' para que Ansible decida (ssh por defecto)
    run_ansible_playbook(playbook_path, inventory_source=inventory_path, connection='smart')


if __name__ == '__main__':
    run_deploy_dhcp()

