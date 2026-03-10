import sys
import os
import csv
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QListWidget, QPushButton, QTextEdit, QLabel, QMessageBox,
    QInputDialog, QLineEdit
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Ajuste de ruta para poder importar los módulos del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.modules.device_manager_factory import create_device
from scripts.backup_network import run_backup

# --- Clase Worker para Hilos (Facts) ---
class ConnectionWorker(QThread):
    log_signal = pyqtSignal(str)      
    finished_signal = pyqtSignal()    

    def __init__(self, device_info, username, password):
        super().__init__()
        self.device_info = device_info
        self.username = username
        self.password = password

    def run(self):
        router = None
        try:
            device_params = {
                "ip": self.device_info["hostname"],
                "hostname": self.device_info["hostname"],
                "device_type": self.device_info["device_type"],
                "username": self.username,
                "password": self.password,
            }

            router = create_device(**device_params)
            if not router:
                self.log_signal.emit("[ERROR] Tipo de dispositivo no soportado o datos incompletos.")
                return

            self.log_signal.emit(f"[*] Estableciendo conexión SSH con {router.hostname}...")
            connected = router.connect()
            if not connected:
                self.log_signal.emit("[ERROR] No se pudo establecer la conexión SSH. Revisa las credenciales.")
                return
            self.log_signal.emit("[OK] Conexión establecida correctamente.")

            commands = []
            if router.device_type == "mikrotik_routeros":
                commands = ["/system identity print", "/system resource print", "/ip address print"]
            elif router.device_type == "cisco_ios":
                commands = ["show version", "show ip interface brief"]

            output_blocks = []
            for cmd in commands:
                result = router.send_command(cmd)
                if result:
                    output_blocks.append(f"$ {cmd}\n{result}\n")

            if output_blocks:
                self.log_signal.emit("\n".join(output_blocks))
            else:
                self.log_signal.emit("[INFO] No se recibieron datos de 'facts'.")

        except Exception as e:
            self.log_signal.emit(f"[ERROR] {e}")
        finally:
            if router:
                router.disconnect()
                self.log_signal.emit(f"[-] Desconectado de {router.hostname}")
            self.finished_signal.emit()

# --- Clase Worker para Hilos (Backup) ---
class BackupWorker(QThread):
    log_signal = pyqtSignal(str)      
    finished_signal = pyqtSignal()    

    def run(self):
        self.log_signal.emit("[*] Iniciando proceso de backup en segundo plano...")
        try:
            run_backup()
            self.log_signal.emit("[+] Copias de seguridad completadas con éxito. Revisa la carpeta 'backups/'.")
        except Exception as e:
            self.log_signal.emit(f"[!] Error al realizar el backup: {e}")
        finally:
            self.finished_signal.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panel de Control de Automatización de Red")
        self.setGeometry(100, 100, 950, 650)
        self.inventory = {}
        
        self._apply_dark_theme() # Aplicamos el tema oscuro profesional
        self._init_ui()
        self._connect_signals()
        self._load_initial_data()

    def _apply_dark_theme(self):
        """Aplica estilos CSS para darle un aspecto Dark Mode profesional."""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding-bottom: 5px;
            }
            QListWidget {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item:selected {
                background-color: #094771;
                color: white;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:disabled {
                background-color: #4d4d4d;
                color: #888888;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ce9178;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                padding: 8px;
            }
            QMenuBar {
                background-color: #333333;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #505050;
            }
            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3e3e42;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
        """)

    def _init_ui(self):
        self.device_list_widget = QListWidget()
        self.connect_button = QPushButton("Conectar y Obtener Facts")
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)

        main_layout = QHBoxLayout()
        left_panel_layout = QVBoxLayout()
        right_panel_layout = QVBoxLayout()

        left_panel_layout.addWidget(QLabel("Dispositivos de Red"))
        left_panel_layout.addWidget(self.device_list_widget)
        left_panel_layout.addWidget(self.connect_button)

        right_panel_layout.addWidget(QLabel("Logs y Terminal"))
        right_panel_layout.addWidget(self.log_text_edit)

        left_widget = QWidget()
        left_widget.setLayout(left_panel_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_panel_layout)

        main_layout.addWidget(left_widget, stretch=1) 
        main_layout.addWidget(right_widget, stretch=2) 

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self._create_menu_bar()

    def _load_inventory(self, filename="inventory/devices.csv"):
        try:
            with open(filename, mode='r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None) # Saltar cabecera
                for i, row in enumerate(reader):
                    if not row or not row[0].strip() or row[0].strip().startswith('#'):
                        continue
                    device_name = row[0]
                    self.inventory[device_name] = {
                        "hostname": row[1],
                        "device_type": row[2]
                    }
            self.log_text_edit.append(f"[*] Inventario cargado correctamente desde '{filename}'.")
        except Exception as e:
            self.log_text_edit.append(f"[!] Ocurrió un error al leer el inventario: {e}")

    def populate_device_list(self):
        self.device_list_widget.clear()
        for device_name in self.inventory.keys():
            self.device_list_widget.addItem(device_name)

    def _connect_signals(self):
        self.connect_button.clicked.connect(self.run_gather_facts)
        self.exit_action.triggered.connect(self.close)
        self.gather_facts_action.triggered.connect(self.run_gather_facts)
        self.backup_action.triggered.connect(self.run_backup_action)
        self.about_action.triggered.connect(self.show_about_dialog)

    def _load_initial_data(self):
        self._load_inventory()
        self.populate_device_list()

    def run_gather_facts(self):
        selected_items = self.device_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecciona un dispositivo de la lista primero.")
            return

        device_name = selected_items[0].text()
        device_info = self.inventory.get(device_name)

        # 1. Validación estricta de Usuario
        username = ""
        while not username.strip():
            username, ok = QInputDialog.getText(self, 'Credenciales', f'Usuario para {device_name}:')
            if not ok:
                self.log_text_edit.append("[-] Operación cancelada por el usuario.")
                return
            if not username.strip():
                QMessageBox.warning(self, "Error", "El campo de usuario no puede estar vacío.")

        # 2. Validación estricta de Contraseña
        password = ""
        while not password:
            password, ok = QInputDialog.getText(self, 'Credenciales', f'Contraseña para {device_name}:', QLineEdit.EchoMode.Password)
            if not ok:
                self.log_text_edit.append("[-] Operación cancelada por el usuario.")
                return
            if not password:
                QMessageBox.warning(self, "Error", "El campo de contraseña no puede estar vacío.")

        self.log_text_edit.append(f"\n--- Procesando {device_name} ---")
        self.connect_button.setEnabled(False)

        self.worker = ConnectionWorker(device_info, username, password)
        self.worker.log_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.start()

    def update_log(self, message):
        self.log_text_edit.append(message)
        self.log_text_edit.verticalScrollBar().setValue(self.log_text_edit.verticalScrollBar().maximum())

    def on_worker_finished(self):
        self.connect_button.setEnabled(True)
        self.log_text_edit.append("[INFO] Proceso finalizado.\n")

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Archivo")
        self.exit_action = QAction("Salir", self)
        file_menu.addAction(self.exit_action)

        actions_menu = menu_bar.addMenu("&Acciones")
        self.gather_facts_action = QAction("Conectar y Obtener Facts", self)
        actions_menu.addAction(self.gather_facts_action)
        self.backup_action = QAction("Realizar Backup", self)
        actions_menu.addAction(self.backup_action)

        help_menu = menu_bar.addMenu("A&yuda")
        self.about_action = QAction("Acerca de...", self)
        help_menu.addAction(self.about_action)

    def run_backup_action(self):
        self.log_text_edit.append("\n--- Ejecutando Copias de Seguridad ---")
        self.backup_action.setEnabled(False)
        self.backup_worker = BackupWorker()
        self.backup_worker.log_signal.connect(self.update_log)
        self.backup_worker.finished_signal.connect(self.on_backup_finished)
        self.backup_worker.start()

    def on_backup_finished(self):
        self.backup_action.setEnabled(True)
        self.log_text_edit.append("[INFO] Proceso de backup finalizado.\n")

    def show_about_dialog(self):
        QMessageBox.about(self, "Acerca de",
            "<b>Panel de Control de Automatización de Red</b><br><br>"
            "Proyecto de Fin de Grado<br>"
            "Autor: Martín Gardachal Rodríguez<br><br>"
            "Una herramienta para automatizar la configuración de redes usando Python, Ansible y PyQt.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# falta por rediseñarla entera