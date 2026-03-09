import sys
import os
import csv
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QListWidget, QPushButton, QTextEdit, QLabel, QMessageBox,
    QInputDialog, QLineEdit
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Ajuste de ruta para poder importar los módulos del proyecto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)
from src.modules.device_manager_factory import create_device


# --- Clase Worker para conexiones SSH ---
class ConnectionWorker(QThread):
    """Hilo que gestiona la conexión SSH en segundo plano."""
    log_signal = pyqtSignal(str)      # Señal para enviar texto al log
    finished_signal = pyqtSignal()    # Señal para indicar que ha terminado

    def __init__(self, device_info, username, password):
        super().__init__()
        self.device_info = device_info
        self.username = username
        self.password = password

    def run(self):
        """Código que se ejecuta en el hilo secundario."""
        router = None
        try:
            # Construir la información necesaria para el factory
            device_params = {
                "ip": self.device_info["hostname"],  # En el CSV este campo contiene la IP/host
                "hostname": self.device_info["hostname"],
                "device_type": self.device_info["device_type"],
                "username": self.username,
                "password": self.password,
            }

            router = create_device(**device_params)
            if not router:
                self.log_signal.emit("[ERROR] Tipo de dispositivo no soportado o datos incompletos.")
                return

            # 1. Conectar
            self.log_signal.emit(f"[*] Estableciendo conexión SSH con {router.hostname}...")
            connected = router.connect()
            if not connected:
                self.log_signal.emit("[ERROR] No se pudo establecer la conexión SSH.")
                return
            self.log_signal.emit("[OK] Conexión establecida correctamente.")

            # 2. Obtener información básica ("facts") según el tipo de dispositivo
            commands = []
            if router.device_type == "mikrotik_routeros":
                commands = [
                    "/system identity print",
                    "/system resource print",
                    "/ip address print",
                ]
            elif router.device_type == "cisco_ios":
                commands = [
                    "show version",
                    "show ip interface brief",
                ]

            output_blocks = []
            for cmd in commands:
                result = router.send_command(cmd)
                if result:
                    output_blocks.append(f"$ {cmd}\n{result}\n")

            if output_blocks:
                self.log_signal.emit("\n".join(output_blocks))
            else:
                self.log_signal.emit("[INFO] No se recibieron datos de 'facts' del dispositivo.")

        except Exception as e:
            self.log_signal.emit(f"[ERROR] {e}")
        finally:
            # 3. Desconectar siempre
            if router:
                router.disconnect()
                self.log_signal.emit(f"[-] Desconectado de {router.hostname}")
            self.finished_signal.emit()


class AnsiblePlaybookWorker(QThread):
    """
    Hilo que ejecuta un comando de sistema (por ejemplo, un script de Ansible)
    y envía la salida estándar al log de la interfaz.
    """

    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, command, cwd):
        super().__init__()
        self.command = command
        self.cwd = cwd

    def run(self):
        try:
            self.log_signal.emit(f"[INFO] Ejecutando: {' '.join(self.command)}")
            process = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            for line in process.stdout:
                self.log_signal.emit(line.rstrip())

            process.wait()
            self.log_signal.emit(f"[INFO] Proceso finalizado con código {process.returncode}.")
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Fallo ejecutando el comando: {e}")
        finally:
            self.finished_signal.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Panel de Control de Automatización de Red")
        self.setGeometry(100, 100, 900, 600)

        self.inventory = {}

        self._init_ui()
        self._connect_signals()
        self._load_initial_data()

    def _init_ui(self):
        """Crea y organiza todos los widgets de la interfaz de usuario."""
        # --- Creación de Widgets ---
        self.device_list_widget = QListWidget()
        self.connect_button = QPushButton("Conectar y Obtener Facts")
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setStyleSheet("background-color: #2b2b2b; color: #f0f0f0; font-family: 'Courier New';")

        # --- Creación de Layouts ---
        main_layout = QHBoxLayout()
        left_panel_layout = QVBoxLayout()
        right_panel_layout = QVBoxLayout()

        # --- Panel Izquierdo (Inventario) ---
        left_panel_layout.addWidget(QLabel("Inventario de Dispositivos"))
        left_panel_layout.addWidget(self.device_list_widget)
        left_panel_layout.addWidget(self.connect_button)

        # --- Panel Derecho (Logs) ---
        right_panel_layout.addWidget(QLabel("Logs y Resultados"))
        right_panel_layout.addWidget(self.log_text_edit)

        # --- Ensamblaje Final ---
        left_widget = QWidget()
        left_widget.setLayout(left_panel_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_panel_layout)

        main_layout.addWidget(left_widget, stretch=1) # 1/3 del espacio
        main_layout.addWidget(right_widget, stretch=2) # 2/3 del espacio

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self._create_menu_bar()

    def _load_inventory(self, filename="inventory/devices.csv"):
        """Carga el inventario de dispositivos desde un archivo CSV."""
        try:
            with open(filename, mode='r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                for i, row in enumerate(reader):
                    # Saltar filas vacías o comentarios
                    if not row or not row[0].strip() or row[0].strip().startswith('#'):
                        continue
                    
                    # Asumimos el formato posicional: name, hostname, device_type
                    device_name = row[0]
                    self.inventory[device_name] = {
                        "hostname": row[1],
                        "device_type": row[2]
                    }
            self.log_text_edit.append(f"[INFO] Inventario cargado correctamente desde '{filename}'.")
        except FileNotFoundError:
            self.log_text_edit.append(f"[ERROR] ¡Archivo de inventario '{filename}' no encontrado!")
        except IndexError:
            self.log_text_edit.append(f"[ERROR] Error de formato en el CSV en la línea {i + 1}.")
            self.log_text_edit.append("[INFO] Cada fila debe tener al menos 3 columnas: name,hostname,device_type")
        except Exception as e:
            self.log_text_edit.append(f"[ERROR] Ocurrió un error al leer el inventario: {e}")

    def populate_device_list(self):
        """Carga los dispositivos del inventario en el widget de la lista."""
        self.device_list_widget.clear()
        for device_name in self.inventory.keys():
            self.device_list_widget.addItem(device_name)

    def _connect_signals(self):
        """Conecta las señales de los widgets (clics, etc.) a sus slots (métodos)."""
        self.connect_button.clicked.connect(self.run_gather_facts)
        self.exit_action.triggered.connect(self.close)
        self.gather_facts_action.triggered.connect(self.run_gather_facts)
        self.backup_action.triggered.connect(self.run_backup_placeholder)
        self.deploy_dhcp_action.triggered.connect(self.run_deploy_dhcp_playbook)
        self.about_action.triggered.connect(self.show_about_dialog)

    def _load_initial_data(self):
        """Carga los datos iniciales, como el inventario."""
        self._load_inventory()
        self.populate_device_list()

    def run_gather_facts(self):
        """Pide credenciales, se conecta al dispositivo y ejecuta la obtención de facts."""
        selected_items = self.device_list_widget.selectedItems()
        if not selected_items:
            self.log_text_edit.append("[ERROR] ¡Ningún dispositivo seleccionado! Por favor, selecciona un dispositivo de la lista.")
            return

        device_name = selected_items[0].text()
        device_info = self.inventory.get(device_name)

        # 1. Pedir credenciales al usuario
        username, ok1 = QInputDialog.getText(self, 'Credenciales', 'Usuario:')
        if not (ok1 and username):
            self.log_text_edit.append("[INFO] Operación cancelada por el usuario.")
            return
        
        password, ok2 = QInputDialog.getText(self, 'Credenciales', 'Contraseña:', QLineEdit.EchoMode.Password)
        if not ok2: # Permitir contraseñas vacías, pero no cancelar
            self.log_text_edit.append("[INFO] Operación cancelada por el usuario.")
            return
        
        self.log_text_edit.append(f"--- Procesando {device_name} ---")
        self.log_text_edit.append(f"[*] Conectando a {device_info['hostname']} ({device_info['device_type']})...")
        
        # Deshabilitar botón para evitar doble clic
        self.connect_button.setEnabled(False)

        # 2. Iniciar el Hilo (Worker)
        self.worker = ConnectionWorker(device_info, username, password)
        self.worker.log_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def update_log(self, message):
        """Recibe mensajes del hilo y los pone en el log."""
        self.log_text_edit.append(message)
        self.log_text_edit.verticalScrollBar().setValue(self.log_text_edit.verticalScrollBar().maximum())

    def on_worker_finished(self):
        """Se ejecuta cuando el hilo termina."""
        self.connect_button.setEnabled(True)
        self.log_text_edit.append("[INFO] Proceso finalizado.\n")

    def _create_menu_bar(self):
        """Crea y configura la barra de menú de la aplicación."""
        menu_bar = self.menuBar()

        # --- Menú Archivo ---
        file_menu = menu_bar.addMenu("&Archivo")
        self.exit_action = QAction("Salir", self)
        file_menu.addAction(self.exit_action)

        # --- Menú Acciones ---
        actions_menu = menu_bar.addMenu("&Acciones")
        self.gather_facts_action = QAction("Conectar y Obtener Facts", self)
        actions_menu.addAction(self.gather_facts_action)
        self.backup_action = QAction("Realizar Backup", self)
        actions_menu.addAction(self.backup_action)
        self.deploy_dhcp_action = QAction("Desplegar DHCP (Ansible)", self)
        actions_menu.addAction(self.deploy_dhcp_action)

        # --- Menú Ayuda ---
        help_menu = menu_bar.addMenu("A&yuda")
        self.about_action = QAction("Acerca de...", self)
        help_menu.addAction(self.about_action)

    def run_backup_placeholder(self):
        self.log_text_edit.append("\n[INFO] La función para realizar backups se conectará aquí.")

    def run_deploy_dhcp_playbook(self):
        """
        Lanza el script Python que ejecuta el playbook de Ansible para desplegar DHCP.
        """
        script_path = os.path.join(PROJECT_ROOT, "scripts", "deploy_dhcp.py")
        if not os.path.exists(script_path):
            self.log_text_edit.append(f"[ERROR] No se encuentra el script: {script_path}")
            return

        self.log_text_edit.append("\n=== DESPLIEGUE DHCP DESDE LA GUI ===")

        # Deshabilitar la acción para evitar lanzarlo varias veces a la vez
        self.deploy_dhcp_action.setEnabled(False)

        self.ansible_worker = AnsiblePlaybookWorker(
            command=[sys.executable, script_path],
            cwd=PROJECT_ROOT,
        )
        self.ansible_worker.log_signal.connect(self.update_log)

        def on_finished():
            self.deploy_dhcp_action.setEnabled(True)
            self.log_text_edit.append("[INFO] Despliegue DHCP terminado.\n")

        self.ansible_worker.finished_signal.connect(on_finished)
        self.ansible_worker.start()

    def show_about_dialog(self):
        QMessageBox.about(self, "Acerca de",
            "<b>Panel de Control de Automatización de Red</b><br><br>"
            "Proyecto de Fin de Grado<br>"
            "Autor: Martín Gardachal Rodríguez<br><br>"
            "Una herramienta para automatizar la configuración de redes usando Python, Ansible y PyQt.")

if __name__ == "__main__":
    # Necesitas instalar PyQt6: pip install PyQt6
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
