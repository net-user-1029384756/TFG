import sys
import os
from collections import namedtuple

# Ajuste de ruta para poder importar desde src/ y el directorio raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importaciones de Ansible
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager

# --- AVISO ---
# Esta es una forma avanzada de ejecutar Ansible y puede ser compleja.
# Se utiliza aquí como una solución alternativa a un error de la CLI de Ansible
# en ciertos entornos de Windows ('OSError: [WinError 87]').

def run_ansible_playbook(playbook_path, inventory_source='localhost,', connection='local'):
    """
    Ejecuta un playbook de Ansible utilizando la API de Python.

    Args:
        playbook_path (str): Ruta al archivo del playbook .yml.
        inventory_source (str): Ruta al archivo de inventario o cadena de hosts.
        connection (str): Tipo de conexión Ansible (local, ssh, smart, etc.).
    """
    if not os.path.exists(playbook_path):
        print(f"[!] Error: El archivo del playbook no se encuentra en '{playbook_path}'")
        return

    # El DataLoader se encarga de encontrar y leer los archivos (playbooks, roles, etc.)
    loader = DataLoader()

    # Inventario: por defecto 'localhost,' pero se puede apuntar a un archivo INI/YAML.
    inventory = InventoryManager(loader=loader, sources=inventory_source)

    # El gestor de variables se encarga de las variables, hechos, etc.
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    # Opciones para la ejecución del playbook. Usamos un namedtuple para simular
    # las opciones de la línea de comandos.
    Options = namedtuple('Options', [
        'listtags', 'listtasks', 'listhosts', 'syntax', 'connection',
        'module_path', 'forks', 'remote_user', 'private_key_file',
        'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
        'scp_extra_args', 'become', 'become_method', 'become_user',
        'verbosity', 'check', 'diff'
    ])
    options = Options(
        listtags=False, listtasks=False, listhosts=False, syntax=False,
        connection=connection,
        module_path=None, forks=100, remote_user=None,
        private_key_file=None, ssh_common_args=None, ssh_extra_args=None,
        sftp_extra_args=None, scp_extra_args=None, become=None,
        become_method=None, become_user=None, verbosity=0,
        check=False, diff=False
    )

    # Contraseña, si fuera necesaria. Ansible recomienda usar Vault para esto.
    passwords = {}

    # Crear el PlaybookExecutor y ejecutarlo
    pbex = PlaybookExecutor(
        playbooks=[playbook_path],
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        options=options,
        passwords=passwords
    )

    print(f"[*] Ejecutando el playbook '{playbook_path}' con la API de Python...")
    result = pbex.run()
    print(f"[*] Ejecución finalizada con resultado: {result}")

    # Limpieza
    pbex._tqm.cleanup()


if __name__ == '__main__':
    # Obtenemos la ruta del playbook desde los argumentos de la línea de comandos
    # o usamos el de prueba por defecto.
    if len(sys.argv) > 1:
        playbook_to_run = sys.argv[1]
    else:
        # Apuntamos al playbook de prueba por defecto
        playbook_to_run = os.path.join('playbooks', 'hello_ansible.yml')
        print(f"[i] No se especificó un playbook. Usando por defecto: {playbook_to_run}")

    run_ansible_playbook(playbook_to_run)
