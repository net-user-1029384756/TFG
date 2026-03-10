import argparse
import os


INVENTORY_PATH = os.path.join("inventory", "ansible_hosts")


def ensure_group(lines, group_name):
    """
    Asegura que el grupo existe en el inventario.
    Si no existe, lo añade al final.
    """
    header = f"[{group_name}]"
    if any(line.strip() == header for line in lines):
        return lines
    lines.append("\n")
    lines.append(f"{header}\n")
    return lines


def register_host(hostname, ip, group, ansible_user=None, ansible_ssh_private_key_file=None):
    """
    Registra o actualiza un host en el inventario de Ansible.
    """
    if not os.path.exists(INVENTORY_PATH):
        raise FileNotFoundError(f"No se encuentra el inventario de Ansible en: {INVENTORY_PATH}")

    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    lines = ensure_group(lines, group)

    header = f"[{group}]"
    new_lines = []
    in_target_group = False
    host_line = f"{hostname} ansible_host={ip}"
    if ansible_user:
        host_line += f" ansible_user={ansible_user}"
    if ansible_ssh_private_key_file:
        host_line += f" ansible_ssh_private_key_file={ansible_ssh_private_key_file}"
    host_line += "\n"

    replaced = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_target_group = stripped == header
            new_lines.append(line)
            continue

        if in_target_group and stripped.startswith(hostname):
            # Reemplazar línea existente para este host
            new_lines.append(host_line)
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        # Añadir al final del grupo
        new_lines.append(host_line)

    with open(INVENTORY_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"[Inventario] Host '{hostname}' registrado en grupo '{group}' con IP {ip}.")


def main():
    parser = argparse.ArgumentParser(description="Registrar/actualizar una VM en inventory/ansible_hosts.")
    parser.add_argument("--hostname", required=True, help="Nombre lógico del host en Ansible.")
    parser.add_argument("--ip", required=True, help="Dirección IP del host.")
    parser.add_argument("--group", required=True, help="Nombre del grupo de Ansible.")
    parser.add_argument("--user", help="Usuario SSH para Ansible (ansible_user).")
    parser.add_argument("--keyfile", help="Ruta a la clave privada SSH (ansible_ssh_private_key_file).")
    args = parser.parse_args()

    register_host(
        hostname=args.hostname,
        ip=args.ip,
        group=args.group,
        ansible_user=args.user,
        ansible_ssh_private_key_file=args.keyfile,
    )


if __name__ == "__main__":
    main()

