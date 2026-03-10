---
name: vm-automation-vbox-gui
overview: Extender la GUI para crear y provisionar máquinas virtuales en VirtualBox usando configuraciones YAML y Ansible, integrándose con el resto del proyecto de automatización de red.
todos:
  - id: design-yaml-schema
    content: Definir esquema YAML y crear 2–3 ejemplos de configuración de VMs en configs/vms/.
    status: pending
  - id: implement-vbox-wrapper
    content: Implementar modulo vbox_manager.py con funciones para crear y arrancar VMs a partir de configuraciones YAML usando VBoxManage.
    status: pending
  - id: integrate-ansible-inventory
    content: Conectar las VMs creadas con el inventario Ansible y definir qué playbooks se ejecutan por rol de VM.
    status: pending
  - id: extend-gui-for-vm-creation
    content: Añadir a la GUI un formulario para definir VMs (rol, SO, recursos, red) y lanzar la creación/provisioning.
    status: pending
  - id: document-flow-and-optional-pxe
    content: Documentar el flujo end-to-end en la memoria del TFG y, si hay tiempo, diseñar un escenario PXE opcional como mejora futura.
    status: pending
isProject: false
---

### Objetivo general

Integrar en la GUI un flujo que permita: (1) definir máquinas virtuales (rol, SO, recursos, redes) mediante formularios que generen ficheros YAML, (2) crear esas VMs en VirtualBox usando `VBoxManage` y discos/ISOs existentes en tu SSD, y (3) provisionarlas automáticamente con Ansible (instalación de servicios y configuración de clientes), dejando la puerta abierta a explorar PXE más adelante.

---

### Arquitectura propuesta

- **Capa de definición (YAML de VMs)**
  - Un esquema YAML por "perfil" de VM (ej. `configs/vms/dhcp_linux.yml`, `configs/vms/core_router_client_windows.yml`).
  - Cada YAML describe:
    - `name`: nombre de la VM.
    - `role`: servicio o cliente (`dhcp_server`, `dns_server`, `linux_client`, `windows_client`, etc.).
    - `os_type`: `linux` o `windows` (y subtipo VirtualBox, p.ej. `Debian_64`, `Windows11_64`).
    - `resources`: `cpus`, `memory_mb`, `disk_gb` o ruta a disco base/plantilla.
    - `storage`: ruta al SSD donde están ISOs/discos base.
    - `network`: adaptadores, tipo de red (`nat`, `hostonly`, `bridged`) y, si procede, nombre del switch/hostonly de VirtualBox.
    - `ansible_group`: grupo de inventario al que se añadirá tras la creación (ej. `dhcp_servers`, `linux_clients`, `windows_clients`).
- **Capa de creación de VMs (wrapper de VBoxManage)**
  - Módulo nuevo, por ejemplo `[src/modules/vbox_manager.py](src/modules/vbox_manager.py)`, con funciones de alto nivel:
    - `create_vm_from_config(config: dict) -> None`.
    - Pasos internos:
      - `VBoxManage createvm --name ... --ostype ... --register`.
      - `VBoxManage modifyvm ...` para CPU, RAM, red, etc.
      - Crear/adjuntar disco virtual (o clonar desde un disco plantilla si ya tienes VMs base en el SSD).
      - Adjuntar ISO de instalación si procediera (para escenarios manuales) o disco ya preinstalado para escenarios automáticos.
    - Comprobaciones de seguridad: que las rutas al SSD existen, que no se repite el nombre de VM, etc.
- **Capa de provisioning (Ansible)**
  - Roles/playbooks por rol lógico, reutilizando la estructura que ya tienes en `playbooks/`:
    - Playbook de servicios (p.ej. `playbooks/deploy_dhcp.yml`, `playbooks/deploy_dns.yml`, `playbooks/setup_linux_client.yml`, `playbooks/setup_windows_client.yml`).
    - Cada YAML de VM incluirá `ansible_group`; al crear la VM, se añadirá/actualizará `inventory/ansible_hosts` con la nueva máquina (cuando tenga IP asignada).
  - Flujo típico:
    1. Crear VM en VirtualBox y arrancarla.
    2. Asignarle IP (estática o por DHCP del lab).
    3. Registrar esa IP en `inventory/ansible_hosts` bajo el grupo adecuado.
    4. Ejecutar el playbook correspondiente desde Python (como ya haces con `scripts/deploy_dhcp.py`).
- **GUI (`src/gui.py`) como orquestador**
  - Nueva sección/pestaña o menú en la GUI que permita:
    - Elegir **rol**: `Servidor DHCP`, `Servidor DNS`, `Cliente Linux`, `Cliente Windows`, etc.
    - Elegir **SO** (`linux`/`windows`) y subtipo (lista de OS soportados por VirtualBox: `Debian_64`, `Ubuntu_64`, `Windows10_64`, etc.).
    - Definir **recursos** básicos (RAM, CPU, tamaño de disco o plantilla base).
    - Seleccionar **red** (adaptador host-only del lab, red NAT, etc.).
  - Al pulsar "Crear VM":
    - La GUI genera un YAML bajo `configs/vms/` con los parámetros elegidos.
    - Llama al módulo `vbox_manager` en un `QThread` similar a `AnsiblePlaybookWorker` para no bloquear la interfaz.
    - Opcionalmente, tras la creación, lanza automáticamente el playbook Ansible correspondiente para provisionar esa VM.
- **PXE (opcional, fase posterior)**
  - En lugar de usar ISO o discos plantilla, podrías:
    - Tener una VM de `PXE/TFTP/DHCP` en el lab que sirva imágenes de instalación automatizada (kickstart/preseed, Windows Deployment Services, etc.).
    - Crear las nuevas VMs arrancando por red (NIC PXE) y dejando que se auto-instalen.
  - Esto añade bastante complejidad (otro servidor DHCP/TFTP, plantillas de instalación, coordinación con tu DHCP actual), por lo que la recomendación es:
    - Empezar con **plantillas de disco preinstaladas + Ansible**.
    - Dejar PXE como mejora avanzada para documentar en la memoria si te da tiempo.

---

### Plan por fases para implementar esto

#### Fase 1: Diseño de esquema YAML y directorio de configs

- Crear un directorio `configs/vms/` en el proyecto.
- Definir un esquema YAML sencillo (aunque sea "de facto") para VMs, por ejemplo:

```yaml
  name: dhcp1
  role: dhcp_server
  os_type: linux
  vbox_ostype: Debian_64
  resources:
    cpus: 1
    memory_mb: 1024
    disk_gb: 10
  storage:
    base_folder: "D:/VMs"  # ruta a tu SSD
  network:
    adapter1:
      type: hostonly
      name: "vboxnet0"
  ansible_group: dhcp_servers
  

```

- Añadir 2–3 ejemplos de YAML para distintos roles (servidor DHCP Linux, cliente Linux, cliente Windows) que puedas reutilizar.

#### Fase 2: Wrapper de VBoxManage en Python

- Crear `[src/modules/vbox_manager.py](src/modules/vbox_manager.py)` con funciones como:
  - `load_vm_config(path: str) -> dict` (usa `yaml.safe_load`).
  - `create_vm(config: dict) -> None` que ejecute secuencialmente:
    - `VBoxManage createvm` con `--name` y `--ostype`.
    - `VBoxManage modifyvm` para memoria, CPUs, NICs, VRAM, etc.
    - Creación/adjunte de disco:
      - `VBoxManage createmedium` + `VBoxManage storagectl` + `VBoxManage storageattach`, o
      - `VBoxManage clonevm` desde una VM plantilla ya instalada en tu SSD.
    - Lanzar la VM (`VBoxManage startvm --type headless` si quieres).
  - Gestionar rutas al SSD usando una constante configurable (p.ej. `VBOX_BASE_FOLDER`) o leyéndola de un `.env`/config.
- Probar primero con un YAML fijo, sin la GUI, para verificar que la VM se crea bien.

#### Fase 3: Integración con Ansible e inventario

- Extender `inventory/ansible_hosts` y tus playbooks para contemplar los nuevos grupos de VMs (clientes y servicios).
- Crear un pequeño script Python, por ejemplo `[scripts/register_vm_in_inventory.py](scripts/register_vm_in_inventory.py)`, que:
  - Reciba parámetros: nombre de host, IP, grupo Ansible.
  - Añada o actualice la entrada correspondiente en `inventory/ansible_hosts`.
- Definir, para cada `role` en los YAML, qué playbook se debe lanzar tras la creación (ej.: `role: dhcp_server` -> `playbooks/deploy_dhcp.yml`).
- Probar el flujo completo en consola:
  1. `create_vm` desde YAML.
  2. Asignar IP (según tu topología); actualizar `ansible_hosts`.
  3. Ejecutar el playbook desde Python (usando `run_ansible_playbook`).

#### Fase 4: Extensión de la GUI

- En `[src/gui.py](src/gui.py)`:
  - Añadir una nueva pestaña o panel "Gestor de VMs" con:
    - Combos desplegables para **rol** y **tipo de SO**.
    - Campos para nombre de VM, RAM, CPU, almacenamiento base (ruta en SSD), objeto de red.
    - Un botón "Generar YAML" y/o "Crear y Provisionar VM".
  - La lógica del botón hará:
    1. Construir un diccionario `config` a partir del formulario.
    2. Guardarlo como YAML en `configs/vms/<name>.yml`.
    3. Lanzar un `QThread` que llame a `vbox_manager.create_vm(config)` y envíe logs a la ventana (similar a `AnsiblePlaybookWorker`).
    4. Opcional: tras creación y fijar la IP, disparar el playbook correspondiente y mostrar su salida en el mismo log.

#### Fase 5: Documentación y, si hay tiempo, PXE

- Documentar en tu memoria:
  - Cómo se definen las VMs por YAML.
  - Capturas de la GUI creando VMs y logs de creación.
  - El flujo completo desde el formulario hasta la VM provisionada con Ansible.
- Si el tiempo lo permite, diseñar un **escenario PXE** aparte para comentarlo como mejora:
  - Una VM dedicada como servidor PXE/TFTP/DHCP con un rol Ansible específico.
  - Nuevos YAML donde `boot_method: pxe` en lugar de adjuntar ISO.
  - Diagrama en la memoria explicando el boot PXE y su relación con tu sistema de automatización.

---

### Resumen de recomendación

- Empezar **YA** con: YAML de definición + wrapper de `VBoxManage` + integración con Ansible, todo pensado para VirtualBox local con tus discos/plantillas en el SSD.
- Dejar PXE como una capa avanzada, interesante para explicar en el TFG, pero no imprescindible para tener una demo sólida: con VMs preinstaladas + Ansible ya demuestras automatización de infraestructura de manera muy convincente. En la memoria se puede documentar PXE como mejora futura (servidor TFTP/DHCP dedicado, plantillas de instalación y arranque por red), sin necesidad de implementarlo en código para este TFG.

