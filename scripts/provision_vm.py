import argparse
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.run_playbook import run_ansible_playbook
from src.modules.vbox_manager import load_vm_config, create_vm, start_vm
from scripts.register_vm_in_inventory import register_host


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INVENTORY_PATH = os.path.join(PROJECT_ROOT, "inventory", "ansible_hosts")


ROLE_PLAYBOOK_MAP = {
    "dhcp_server": "playbooks/deploy_dhcp.yml",
    # Estos playbooks se pueden crear/extender más adelante
    "linux_client": "playbooks/setup_linux_client.yml",
    "windows_client": "playbooks/setup_windows_client.yml",
}


def provision_vm_from_yaml(yaml_path: str):
    """
    Crea una VM en VirtualBox a partir de un YAML, la arranca y la
    registra en el inventario de Ansible. Después lanza el playbook
    correspondiente según el rol.
    """
    config = load_vm_config(yaml_path)

    name = config.get("name")
    role = config.get("role")
    ip = config.get("ip")
    ansible_group = config.get("ansible_group")

    if not name or not role or not ip or not ansible_group:
        raise ValueError("El YAML debe incluir 'name', 'role', 'ip' y 'ansible_group'.")

    print(f"=== PROVISIONING VM DESDE YAML: {yaml_path} ===")
    print(f"[*] Nombre: {name} | Rol: {role} | IP: {ip} | Grupo Ansible: {ansible_group}")

    # 1. Crear la VM en VirtualBox
    create_vm(config)

    # 2. Arrancar la VM
    start_vm(name, headless=True)

    # 3. Registrar la VM en el inventario de Ansible
    register_host(
        hostname=name,
        ip=ip,
        group=ansible_group,
    )

    # 4. Lanzar el playbook correspondiente al rol (si está definido)
    playbook_rel = ROLE_PLAYBOOK_MAP.get(role)
    if not playbook_rel:
        print(f"[INFO] No hay playbook definido para el rol '{role}'. Saltando paso de Ansible.")
        return

    playbook_path = os.path.join(PROJECT_ROOT, playbook_rel)

    print(f"[*] Ejecutando playbook para el rol '{role}': {playbook_path}")
    run_ansible_playbook(playbook_path, inventory_source=INVENTORY_PATH, connection="smart")


def main():
    parser = argparse.ArgumentParser(description="Crear y provisionar una VM a partir de un archivo YAML.")
    parser.add_argument("yaml_path", help="Ruta al archivo YAML de configuración de la VM.")
    args = parser.parse_args()

    provision_vm_from_yaml(args.yaml_path)


if __name__ == "__main__":
    main()


