import sys
import os
import csv
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QStackedWidget, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QInputDialog, QLineEdit, QTextEdit, QCheckBox,
    QGridLayout, QComboBox, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.modules.device_manager_factory import create_device
from src.modules.scanner import NetworkScanner
from scripts.deploy_lan import run_deploy_lan
from scripts.deploy_ospf import run_deploy_ospf
from scripts.deploy_dhcp import run_deploy_dhcp
from scripts.run_playbook import run_ansible_playbook

# ==========================================
# WORKERS (HILOS EN SEGUNDO PLANO)
# ==========================================
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
            if not router.connect():
                self.log_signal.emit("[ERROR] No se pudo conectar. Revisa IP y credenciales.")
                return
            self.log_signal.emit("[OK] Conexión establecida correctamente.")

            commands = []
            if router.device_type == "mikrotik_routeros":
                commands = ["/system identity print", "/system resource print", "/ip address print"]
            elif router.device_type == "cisco_ios":
                commands = ["show version", "show ip interface brief"]
            elif router.device_type == "linux":
                commands = ["uname -a", "ip a", "free -m"]
            elif router.device_type == "windows":
                commands = ["systeminfo | findstr /B /C:\"OS Name\" /C:\"OS Version\"", "ipconfig"]

            output_blocks = []
            if hasattr(router, 'send_command'):
                for cmd in commands:
                    res = router.send_command(cmd)
                    if res: output_blocks.append(f"$ {cmd}\n{res}\n")
            elif hasattr(router, 'execute_command'):
                for cmd in commands:
                    res = router.execute_command(cmd)
                    if res: output_blocks.append(f"$ {cmd}\n{res}\n")

            if output_blocks:
                self.log_signal.emit("\n".join(output_blocks))
            else:
                self.log_signal.emit("[INFO] No se recibieron datos de 'facts'.")

        except Exception as e:
            self.log_signal.emit(f"[ERROR] Ocurrió una excepción: {e}")
        finally:
            if router:
                router.disconnect()
                self.log_signal.emit(f"[-] Desconectado de {router.hostname}")
            self.finished_signal.emit()

class ScannerWorker(QThread):
    """Hilo para ejecutar Nmap en segundo plano sin congelar la GUI."""
    log_signal = pyqtSignal(str)
    result_signal = pyqtSignal(list)
    finished_signal = pyqtSignal()

    def __init__(self, network_range, os_detection):
        super().__init__()
        self.network_range = network_range
        self.os_detection = os_detection

    def run(self):
        self.log_signal.emit(f"[*] Iniciando escaneo Nmap en la red {self.network_range}...")
        if self.os_detection:
            self.log_signal.emit("[i] Detección de SO activada (puede tardar unos minutos).")
        
        try:
            scanner = NetworkScanner()
            devices = scanner.discover_devices(self.network_range, with_os_detection=self.os_detection)
            self.result_signal.emit(devices)
            self.log_signal.emit(f"[+] Escaneo completado. {len(devices)} dispositivos encontrados.")
        except Exception as e:
            self.log_signal.emit(f"[!] Error fatal en Nmap: {e}")
            self.result_signal.emit([])
        finally:
            self.finished_signal.emit()

class ActionWorker(QThread):
    """Hilo genérico para ejecutar scripts de Ansible o Netmiko en segundo plano."""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, target_function, *args):
        super().__init__()
        self.target_function = target_function
        self.args = args

    def run(self):
        self.log_signal.emit("[*] Lanzando orquestador en segundo plano...")
        self.log_signal.emit("[i] (Revisa tu terminal original de Ubuntu para ver los colores y el progreso detallado en tiempo real)")
        try:
            # Ejecutamos la función que nos hayan pasado (run_deploy_lan, run_ansible, etc)
            self.target_function(*self.args)
            self.log_signal.emit("\n[+] Tarea de despliegue finalizada correctamente.")
        except Exception as e:
            self.log_signal.emit(f"\n[!] Error crítico durante el despliegue: {e}")
        finally:
            self.finished_signal.emit()

# ==========================================
# VENTANA PRINCIPAL
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panel de Control de Automatización de Red")
        self.setGeometry(100, 100, 1150, 750)
        self.inventory_file = "inventory/devices.csv"
        
        self.current_theme = "light" 
        self._load_theme(self.current_theme)
        
        self._init_ui()
        self._load_inventory_table()

    def _load_theme(self, theme_name):
        theme_path = os.path.join(os.path.dirname(__file__), 'styles', f'{theme_name}.qss')
        try:
            with open(theme_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            pass

    def _toggle_theme(self):
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.btn_theme_toggle.setText("Modo Oscuro")
        else:
            self.current_theme = "dark"
            self.btn_theme_toggle.setText("Modo Claro")
        self._load_theme(self.current_theme)

    def _init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("sidebar")
        self.sidebar_widget.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(5)

        self.btn_dashboard = self._create_nav_button("Dashboard")
        self.btn_inventory = self._create_nav_button("Inventario de Red")
        self.btn_discovery = self._create_nav_button("Descubrimiento (Nmap)")
        self.btn_actions = self._create_nav_button("Despliegues y Ansible")
        self.btn_logs = self._create_nav_button("Consola Global")

        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_inventory)
        sidebar_layout.addWidget(self.btn_discovery)
        sidebar_layout.addWidget(self.btn_actions)
        sidebar_layout.addWidget(self.btn_logs)
        sidebar_layout.addStretch()

        self.btn_theme_toggle = QPushButton("Modo Oscuro")
        self.btn_theme_toggle.setObjectName("btn_theme_toggle")
        self.btn_theme_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme_toggle.clicked.connect(self._toggle_theme)
        sidebar_layout.addWidget(self.btn_theme_toggle)

        # --- Área Central (Páginas) ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setContentsMargins(20, 20, 20, 20)

        self.page_dashboard = self._create_placeholder_page("Dashboard", "Resumen de infraestructura en construcción...")
        self.page_inventory = self._build_inventory_page()
        self.page_discovery = self._build_discovery_page()
        self.page_actions = self._build_actions_page()
        self.page_logs = self._build_logs_page()
        
        self.stacked_widget.addWidget(self.page_dashboard)
        self.stacked_widget.addWidget(self.page_inventory)
        self.stacked_widget.addWidget(self.page_discovery)
        self.stacked_widget.addWidget(self.page_actions)
        self.stacked_widget.addWidget(self.page_logs)

        main_layout.addWidget(self.sidebar_widget)
        main_layout.addWidget(self.stacked_widget)

        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Conexiones
        self.btn_dashboard.clicked.connect(lambda: self._switch_page(0, self.btn_dashboard))
        self.btn_inventory.clicked.connect(lambda: self._switch_page(1, self.btn_inventory))
        self.btn_discovery.clicked.connect(lambda: self._switch_page(2, self.btn_discovery))
        self.btn_actions.clicked.connect(lambda: self._switch_page(3, self.btn_actions))
        self.btn_logs.clicked.connect(lambda: self._switch_page(4, self.btn_logs))

        self._switch_page(0, self.btn_discovery) # Empezamos en Descubrimiento para que lo pruebes

    def _create_nav_button(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _switch_page(self, index, active_button):
        self.stacked_widget.setCurrentIndex(index)
        for btn in [self.btn_dashboard, self.btn_inventory, self.btn_discovery, self.btn_actions, self.btn_logs]:
            btn.setChecked(False)
        active_button.setChecked(True)

    def _create_placeholder_page(self, title_text, description_text):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel(title_text)
        title.setProperty("class", "page-title")
        desc = QLabel(description_text)
        desc.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()
        return page

    # ==========================================
    # LÓGICA DE INVENTARIO (FASE 2)
    # ==========================================
    def _build_inventory_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        title = QLabel("Gestión de Inventario")
        title.setProperty("class", "page-title")
        layout.addWidget(title)
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(3)
        self.inventory_table.setHorizontalHeaderLabels(["Nombre Lógico", "IP / Hostname", "Tipo de Sistema"])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.inventory_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.inventory_table)
        
        btn_layout = QHBoxLayout()
        self.btn_add_device = QPushButton("Añadir Dispositivo")
        self.btn_del_device = QPushButton("Eliminar Seleccionado")
        self.btn_get_facts = QPushButton("Conectar y Obtener Facts")
        
        self.btn_add_device.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del_device.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_get_facts.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_get_facts.setStyleSheet("background-color: #28a745; color: white; padding: 10px; border-radius: 4px; font-weight: bold;") 
        
        btn_layout.addWidget(self.btn_add_device)
        btn_layout.addWidget(self.btn_del_device)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_get_facts)
        
        layout.addLayout(btn_layout)
        
        self.btn_add_device.clicked.connect(self._add_device_gui)
        self.btn_del_device.clicked.connect(self._delete_device_gui)
        self.btn_get_facts.clicked.connect(self.run_gather_facts)
        
        return page

    def _load_inventory_table(self):
        self.inventory_table.setRowCount(0)
        try:
            with open(self.inventory_file, mode='r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)
                for row in reader:
                    if not row or not row[0].strip() or row[0].strip().startswith('#'): continue
                    row_position = self.inventory_table.rowCount()
                    self.inventory_table.insertRow(row_position)
                    self.inventory_table.setItem(row_position, 0, QTableWidgetItem(row[0]))
                    self.inventory_table.setItem(row_position, 1, QTableWidgetItem(row[1]))
                    self.inventory_table.setItem(row_position, 2, QTableWidgetItem(row[2]))
        except Exception as e:
            self.update_log(f"[!] Error leyendo inventario: {e}")

    def _save_inventory_to_csv(self):
        try:
            with open(self.inventory_file, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["name", "hostname", "type"])
                for row in range(self.inventory_table.rowCount()):
                    name = self.inventory_table.item(row, 0).text()
                    ip = self.inventory_table.item(row, 1).text()
                    tipo = self.inventory_table.item(row, 2).text()
                    writer.writerow([name, ip, tipo])
        except Exception as e:
            self.update_log(f"[!] Error guardando el CSV: {e}")

    def _add_device_gui(self):
        name, ok = QInputDialog.getText(self, "Añadir Dispositivo", "Nombre lógico:")
        if not ok or not name.strip(): return
        
        ip, ok = QInputDialog.getText(self, "Añadir Dispositivo", "IP o Hostname:")
        if not ok or not ip.strip(): return
        
        tipos = ["mikrotik_routeros", "cisco_ios", "linux", "windows"]
        tipo, ok = QInputDialog.getItem(self, "Añadir Dispositivo", "Tipo de Sistema:", tipos, 0, False)
        if not ok or not tipo: return
        
        row_position = self.inventory_table.rowCount()
        self.inventory_table.insertRow(row_position)
        self.inventory_table.setItem(row_position, 0, QTableWidgetItem(name.strip()))
        self.inventory_table.setItem(row_position, 1, QTableWidgetItem(ip.strip()))
        self.inventory_table.setItem(row_position, 2, QTableWidgetItem(tipo))
        
        self._save_inventory_to_csv()

    def _delete_device_gui(self):
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Selecciona una fila entera para eliminar.")
            return
        row = selected_rows[0].row()
        device_name = self.inventory_table.item(row, 0).text()
        reply = QMessageBox.question(self, 'Confirmar', f"¿Eliminar a {device_name}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.inventory_table.removeRow(row)
            self._save_inventory_to_csv()

    def run_gather_facts(self):
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Selecciona un dispositivo primero.")
            return

        row = selected_rows[0].row()
        device_name = self.inventory_table.item(row, 0).text()
        device_info = {
            "hostname": self.inventory_table.item(row, 1).text(),
            "device_type": self.inventory_table.item(row, 2).text()
        }

        username, ok = QInputDialog.getText(self, 'Credenciales', f'Usuario para {device_name}:')
        if not ok or not username.strip(): return
        password, ok = QInputDialog.getText(self, 'Credenciales', f'Contraseña:', QLineEdit.EchoMode.Password)
        if not ok: return

        self._switch_page(4, self.btn_logs)
        self.update_log(f"\n--- Procesando {device_name} ---")

        self.worker = ConnectionWorker(device_info, username.strip(), password)
        self.worker.log_signal.connect(self.update_log)
        self.worker.start()

    # ==========================================
    # LÓGICA DE DESCUBRIMIENTO (NMAP) - FASE 3
    # ==========================================
    def _build_discovery_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        title = QLabel("Descubrimiento de Red (Nmap)")
        title.setProperty("class", "page-title")
        layout.addWidget(title)

        # Formulario superior
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Rango de Red:"))
        
        self.input_network = QLineEdit("192.168.56.0/24")
        self.input_network.setStyleSheet("padding: 5px; font-size: 14px;")
        form_layout.addWidget(self.input_network)
        
        self.cb_os_detect = QCheckBox("Detección Avanzada de SO (Requiere privilegios)")
        form_layout.addWidget(self.cb_os_detect)
        
        self.btn_scan = QPushButton("Escanear Red")
        self.btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scan.setStyleSheet("background-color: #007acc; color: white; padding: 8px; font-weight: bold;")
        self.btn_scan.clicked.connect(self.run_nmap_scan)
        form_layout.addWidget(self.btn_scan)
        
        layout.addLayout(form_layout)

        # Tabla de resultados Nmap
        self.nmap_table = QTableWidget()
        self.nmap_table.setColumnCount(4)
        self.nmap_table.setHorizontalHeaderLabels(["IP", "Hostname", "Estado", "Sistema Operativo"])
        self.nmap_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.nmap_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.nmap_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.nmap_table)

        # Botones inferiores
        btn_layout = QHBoxLayout()
        self.btn_add_to_inv = QPushButton("Añadir Seleccionados al Inventario")
        self.btn_add_to_inv.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_to_inv.setStyleSheet("background-color: #d9534f; color: white; padding: 10px; font-weight: bold;")
        self.btn_add_to_inv.clicked.connect(self.add_scanned_to_inventory)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add_to_inv)
        layout.addLayout(btn_layout)

        return page

    def run_nmap_scan(self):
        network = self.input_network.text().strip()
        if not network:
            QMessageBox.warning(self, "Error", "Introduce un rango de red válido.")
            return

        os_detect = self.cb_os_detect.isChecked()
        
        self.nmap_table.setRowCount(0) # Limpiar tabla anterior
        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("Escaneando...")
        
        self.update_log(f"\n--- Nuevo Escaneo Nmap: {network} ---")
        
        # Arrancar hilo de escaneo
        self.scan_worker = ScannerWorker(network, os_detect)
        self.scan_worker.log_signal.connect(self.update_log)
        self.scan_worker.result_signal.connect(self.populate_nmap_table)
        self.scan_worker.finished_signal.connect(self.on_scan_finished)
        self.scan_worker.start()

    def populate_nmap_table(self, devices):
        for device in devices:
            row = self.nmap_table.rowCount()
            self.nmap_table.insertRow(row)
            self.nmap_table.setItem(row, 0, QTableWidgetItem(device.get('ip', 'N/A')))
            self.nmap_table.setItem(row, 1, QTableWidgetItem(device.get('hostname', 'N/A')))
            self.nmap_table.setItem(row, 2, QTableWidgetItem(device.get('status', 'N/A')))
            
            os_info = device.get('os', 'Desconocido')
            if 'os_accuracy' in device:
                os_info += f" ({device['os_accuracy']}%)"
            self.nmap_table.setItem(row, 3, QTableWidgetItem(os_info))

    def on_scan_finished(self):
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText("Escanear Red")

    def add_scanned_to_inventory(self):
        selected_rows = self.nmap_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Aviso", "Selecciona al menos un dispositivo de la tabla de escaneo.")
            return

        tipos_soportados = ["mikrotik_routeros", "cisco_ios", "linux", "windows"]

        for model_index in selected_rows:
            row = model_index.row()
            ip = self.nmap_table.item(row, 0).text()
            hostname_nmap = self.nmap_table.item(row, 1).text()
            
            # Preguntamos qué tipo de dispositivo es (para que Netmiko/Ansible sepa cómo hablarle)
            tipo, ok = QInputDialog.getItem(self, "Clasificar Dispositivo", f"Selecciona el tipo de SO para la IP {ip}:", tipos_soportados, 0, False)
            if not ok or not tipo:
                continue # Si cancela, pasamos al siguiente
                
            # Preguntamos qué nombre queremos ponerle
            nombre, ok = QInputDialog.getText(self, "Nombrar Dispositivo", f"Nombre lógico para {ip}:", text=hostname_nmap if hostname_nmap != 'N/A' else f"host_{ip.replace('.','_')}")
            if not ok or not nombre:
                continue

            # Lo añadimos a la tabla del inventario principal
            inv_row = self.inventory_table.rowCount()
            self.inventory_table.insertRow(inv_row)
            self.inventory_table.setItem(inv_row, 0, QTableWidgetItem(nombre.strip()))
            self.inventory_table.setItem(inv_row, 1, QTableWidgetItem(ip))
            self.inventory_table.setItem(inv_row, 2, QTableWidgetItem(tipo))

        self._save_inventory_to_csv()
        QMessageBox.information(self, "Éxito", "Dispositivos añadidos al inventario correctamente.")

    # ==========================================
    # LÓGICA DE DESPLIEGUES Y ANSIBLE (ESTILO FORMULARIO PROFESIONAL)
    # ==========================================
    def _build_actions_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        title = QLabel("Despliegues y Orquestación (Ansible/Netmiko)")
        title.setProperty("class", "page-title")
        layout.addWidget(title)
        
        desc = QLabel("Configura los parámetros del despliegue. Las tareas se ejecutarán de forma asíncrona.")
        desc.setStyleSheet("margin-bottom: 20px; font-size: 14px; color: #888;")
        layout.addWidget(desc)

        # Contenedor del formulario (Estilo profesional)
        form_group = QGroupBox("Asistente de Configuración de Tareas")
        form_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Desplegables
        self.cb_role = QComboBox()
        self.cb_role.setStyleSheet("padding: 5px; font-size: 13px;")
        self.cb_role.addItems(["-- Seleccione el Rol del Equipo --", "Equipos de Red (Routers)", "Servidores", "Equipos Cliente"])
        
        self.cb_os = QComboBox()
        self.cb_os.setStyleSheet("padding: 5px; font-size: 13px;")
        self.cb_os.setEnabled(False) # Desactivado hasta que elijas rol

        self.cb_task = QComboBox()
        self.cb_task.setStyleSheet("padding: 5px; font-size: 13px;")
        self.cb_task.setEnabled(False) # Desactivado hasta que elijas SO

        form_layout.addRow("1. Rol Objetivo:", self.cb_role)
        form_layout.addRow("2. Sistema Operativo:", self.cb_os)
        form_layout.addRow("3. Tarea a Ejecutar:", self.cb_task)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Botón de ejecución
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_execute_task = QPushButton("Iniciar Despliegue")
        self.btn_execute_task.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_execute_task.setStyleSheet("background-color: #007acc; color: white; padding: 10px 20px; font-weight: bold; font-size: 14px;")
        self.btn_execute_task.setEnabled(False) # Desactivado hasta que el formulario esté completo
        self.btn_execute_task.clicked.connect(self._on_execute_task)
        
        btn_layout.addWidget(self.btn_execute_task)
        layout.addLayout(btn_layout)
        layout.addStretch()

        # Conectar las señales (La magia de la cascada)
        self.cb_role.currentIndexChanged.connect(self._update_os_choices)
        self.cb_os.currentIndexChanged.connect(self._update_task_choices)
        self.cb_task.currentIndexChanged.connect(self._validate_task_form)

        return page

    def _update_os_choices(self):
        """Actualiza el desplegable de SO según el Rol elegido."""
        self.cb_os.clear()
        self.cb_task.clear()
        self.cb_task.setEnabled(False)
        self.btn_execute_task.setEnabled(False)

        role = self.cb_role.currentText()
        
        if role == "Equipos de Red (Routers)":
            self.cb_os.addItems(["-- Seleccione Fabricante --", "Cisco IOS / Mikrotik RouterOS"])
            self.cb_os.setEnabled(True)
        elif role == "Servidores":
            self.cb_os.addItems(["-- Seleccione SO --", "Linux (Ubuntu/Debian)", "Windows Server"])
            self.cb_os.setEnabled(True)
        elif role == "Equipos Cliente":
            self.cb_os.addItems(["-- Seleccione SO --", "Linux (Ubuntu Desktop)", "Windows (10/11)"])
            self.cb_os.setEnabled(True)
        else:
            self.cb_os.setEnabled(False)

    def _update_task_choices(self):
        """Actualiza el desplegable de Tareas según el SO elegido."""
        self.cb_task.clear()
        self.btn_execute_task.setEnabled(False)
        
        role = self.cb_role.currentText()
        os_type = self.cb_os.currentText()

        if "--" in os_type or not os_type:
            self.cb_task.setEnabled(False)
            return

        self.cb_task.setEnabled(True)
        self.cb_task.addItem("-- Seleccione Tarea --")

        if role == "Equipos de Red (Routers)":
            self.cb_task.addItems(["Desplegar LAN Base", "Configurar OSPF"])
        
        elif role == "Servidores":
            if "Linux" in os_type:
                self.cb_task.addItems(["Desplegar Servidor DHCP (Ansible)"])
            elif "Windows" in os_type:
                self.cb_task.addItems(["(No hay playbooks disponibles para WinServer)"])
                
        elif role == "Equipos Cliente":
            if "Linux" in os_type:
                self.cb_task.addItems(["Setup Base Cliente Linux (Ansible)"])
            elif "Windows" in os_type:
                self.cb_task.addItems(["Setup Base Cliente Windows (Ansible)"])

    def _validate_task_form(self):
        """Habilita el botón de ejecutar solo si hay una tarea válida seleccionada."""
        task = self.cb_task.currentText()
        if task and "--" not in task and "(No hay" not in task:
            self.btn_execute_task.setEnabled(True)
        else:
            self.btn_execute_task.setEnabled(False)

    def _on_execute_task(self):
        """Enruta la tarea seleccionada en el formulario hacia el script correcto."""
        task = self.cb_task.currentText()
        
        # Mapeo del texto del formulario a las funciones reales
        if task == "Desplegar LAN Base":
            self.launch_action("Despliegue LAN Base (Routers)", run_deploy_lan)
        elif task == "Configurar OSPF":
            self.launch_action("Configuración OSPF (Routers)", run_deploy_ospf)
        elif task == "Desplegar Servidor DHCP (Ansible)":
            self.launch_action("Despliegue de Servidor DHCP", run_deploy_dhcp)
        elif task == "Setup Base Cliente Linux (Ansible)":
            pb = os.path.join('playbooks', 'setup_linux_client.yml')
            inv = os.path.join('inventory', 'ansible_hosts')
            self.launch_action("Setup Clientes Linux", run_ansible_playbook, pb, inv)
        elif task == "Setup Base Cliente Windows (Ansible)":
            pb = os.path.join('playbooks', 'setup_windows_client.yml')
            inv = os.path.join('inventory', 'ansible_hosts')
            self.launch_action("Setup Clientes Windows", run_ansible_playbook, pb, inv)

    def launch_action(self, task_name, target_function, *args):
        # ... (Tu código de launch_action original se queda exactamente igual) ...
        reply = QMessageBox.question(self, 'Confirmar Ejecución', 
                                    f"¿Lanzar tarea: {task_name}?\n\nEste proceso afectará a los hosts definidos en el inventario.", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self._switch_page(4, self.btn_logs)
            self.update_log(f"\n{'='*40}\n🚀 INICIANDO ORQUESTACIÓN: {task_name.upper()}\n{'='*40}")
            
            self.worker_action = ActionWorker(target_function, *args)
            self.worker_action.log_signal.connect(self.update_log)
            self.worker_action.start()

    # ==========================================
    # LÓGICA DE LA CONSOLA (LOGS)
    # ==========================================
    def _build_logs_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Consola de Tareas")
        title.setProperty("class", "page-title")
        layout.addWidget(title)
        
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setStyleSheet("background-color: #1e1e1e; color: #ce9178; font-family: 'Consolas', monospace; font-size: 14px; border: 1px solid #3e3e42; padding: 10px;")
        layout.addWidget(self.log_text_edit)
        
        return page

    def update_log(self, message):
        self.log_text_edit.append(message)
        self.log_text_edit.verticalScrollBar().setValue(self.log_text_edit.verticalScrollBar().maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())