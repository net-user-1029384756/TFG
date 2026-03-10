import sys
import os
import subprocess

# Ajuste de ruta para poder importar desde src/ y el directorio raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modules.logger import log

def run_ansible_playbook(playbook_path, inventory_source='inventory/ansible_hosts', connection='smart'):
    """
    Ejecuta un playbook de Ansible utilizando la CLI nativa mediante subprocess.
    Esta es la forma recomendada y estable en entornos Linux/WSL.

    Args:
        playbook_path (str): Ruta al archivo del playbook .yml.
        inventory_source (str): Ruta al archivo de inventario.
        connection (str): Tipo de conexión Ansible (local, ssh, smart, etc.).
    """
    if not os.path.exists(playbook_path):
        log.error(f"El archivo del playbook no se encuentra en '{playbook_path}'")
        return

    log.info(f"Ejecutando el playbook '{playbook_path}' con Ansible nativo...")

    # Construimos el comando como si lo escribiéramos en la terminal
    cmd = [
        "ansible-playbook",
        "-i", inventory_source,
        "-c", connection,
        playbook_path
    ]

    try:
        # subprocess.run ejecutará el comando y mostrará la salida en color por la consola
        result = subprocess.run(cmd, check=True)
        log.info(f"Ejecución finalizada con éxito (Código: {result.returncode})")
        
    except subprocess.CalledProcessError as e:
        log.error(f"El playbook finalizó con errores (Código de salida: {e.returncode})")
    except FileNotFoundError:
        log.error("No se encuentra 'ansible-playbook'. Verifica que el entorno virtual está activo.")


if __name__ == '__main__':
    # Obtenemos la ruta del playbook desde los argumentos de la línea de comandos
    if len(sys.argv) > 1:
        playbook_to_run = sys.argv[1]
    else:
        playbook_to_run = os.path.join('playbooks', 'hello_ansible.yml')
        print(f"[i] No se especificó un playbook. Usando por defecto: {playbook_to_run}")

    run_ansible_playbook(playbook_to_run)