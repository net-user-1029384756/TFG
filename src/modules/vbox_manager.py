import os
import subprocess
from typing import Dict, Any

import yaml


VBOXMANAGE_CMD = "VBoxManage"


def load_vm_config(path: str) -> Dict[str, Any]:
    """
    Carga un archivo YAML de definición de VM y devuelve un diccionario.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encuentra el archivo de configuración de VM: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data


def _run_command(args):
    """
    Ejecuta un comando de sistema y muestra la salida por pantalla.
    Lanza CalledProcessError si el comando falla.
    """
    cmd = [VBOXMANAGE_CMD] + args
    print(f"[VBox] Ejecutando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)


def create_vm(config: Dict[str, Any]) -> None:
    """
    Crea y registra una VM en VirtualBox a partir de un diccionario de configuración.

    El diccionario debe contener, al menos:
        - name
        - vbox_ostype
        - resources.cpus
        - resources.memory_mb
        - resources.disk_gb
        - storage.base_folder
        - network.adapter1.type
        - network.adapter1.name
    """
    name = config.get("name")
    vbox_ostype = config.get("vbox_ostype")

    if not name or not vbox_ostype:
        raise ValueError("La configuración de la VM debe incluir 'name' y 'vbox_ostype'.")

    resources = config.get("resources", {})
    cpus = int(resources.get("cpus", 1))
    memory_mb = int(resources.get("memory_mb", 1024))
    disk_gb = int(resources.get("disk_gb", 10))

    storage = config.get("storage", {})
    base_folder = storage.get("base_folder")
    if not base_folder:
        raise ValueError("La configuración de la VM debe incluir 'storage.base_folder' con la ruta al SSD.")

    # Asegurarnos de que la carpeta base existe
    os.makedirs(base_folder, exist_ok=True)

    disk_path = os.path.join(base_folder, f"{name}.vdi")

    network = config.get("network", {})
    adapter1 = network.get("adapter1", {})
    adapter1_type = adapter1.get("type", "hostonly")
    adapter1_name = adapter1.get("name")

    print(f"=== Creación de VM en VirtualBox: {name} ({vbox_ostype}) ===")

    # 1. Crear la VM y registrarla
    _run_command(["createvm", "--name", name, "--ostype", vbox_ostype, "--register"])

    # 2. Configurar recursos básicos
    _run_command([
        "modifyvm", name,
        "--cpus", str(cpus),
        "--memory", str(memory_mb),
        "--vram", "16",
    ])

    # 3. Configurar red del adaptador 1
    if adapter1_type == "hostonly":
        if not adapter1_name:
            raise ValueError("Para 'hostonly' es necesario especificar 'network.adapter1.name' (por ejemplo, vboxnet0).")
        _run_command([
            "modifyvm", name,
            "--nic1", "hostonly",
            "--hostonlyadapter1", adapter1_name,
        ])
    elif adapter1_type == "bridged":
        if not adapter1_name:
            raise ValueError("Para 'bridged' es necesario especificar 'network.adapter1.name' (nombre de interfaz bridge).")
        _run_command([
            "modifyvm", name,
            "--nic1", "bridged",
            "--bridgeadapter1", adapter1_name,
        ])
    else:
        # Por defecto, dejamos NAT
        _run_command([
            "modifyvm", name,
            "--nic1", "nat",
        ])

    # 4. Crear disco duro y adjuntarlo a un controlador SATA
    print(f"[VBox] Creando disco virtual en {disk_path} ({disk_gb} GB)...")
    _run_command([
        "createmedium", "disk",
        "--filename", disk_path,
        "--size", str(disk_gb * 1024),  # VBox espera MB
    ])

    controller_name = "SATA Controller"
    _run_command([
        "storagectl", name,
        "--name", controller_name,
        "--add", "sata",
        "--controller", "IntelAhci",
    ])

    _run_command([
        "storageattach", name,
        "--storagectl", controller_name,
        "--port", "0",
        "--device", "0",
        "--type", "hdd",
        "--medium", disk_path,
    ])

    print(f"[VBox] VM '{name}' creada y registrada correctamente.")


def start_vm(name: str, headless: bool = True) -> None:
    """
    Arranca una VM ya creada.
    """
    args = ["startvm", name]
    if headless:
        args += ["--type", "headless"]
    _run_command(args)

