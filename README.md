# Automatización de Racks de Red y Equipos Cliente

[cite_start]**Autor:** Martín Gardachal Rodríguez [cite: 55, 122]
[cite_start]**Ciclo:** 2º ASIR - Proyecto Intermodular [cite: 51, 54]
[cite_start]**Curso:** 2025/26 [cite: 51]

## 📝 Descripción del Proyecto
[cite_start]Este proyecto consiste en el desarrollo de una solución integral para la automatización de la configuración de racks de red (Cisco, TP-Link y Mikrotik) y equipos cliente (Windows/Linux)[cite: 68, 130]. [cite_start]La solución integra la gestión de routers y switches, configurando VLANs, seguridad de puertos, servicios de red (DNS/DHCP) y protocolos de enrutamiento como OSPF[cite: 69, 131].

## 🚀 Características Principales
- [cite_start]**Gestión Modular:** Implementación en Python utilizando Programación Orientada a Objetos (POO)[cite: 105, 133].
- [cite_start]**Automatización de Red:** Uso de librerías como Netmiko y NAPALM para la configuración de dispositivos multi-fabricante[cite: 72, 171].
- [cite_start]**Despliegue de Servicios:** Playbooks de Ansible para la configuración simultánea de servicios críticos y sistemas operativos[cite: 73, 110].
- [cite_start]**Detección Automática:** Scripts para la identificación de sistemas operativos y aplicación de configuraciones personalizadas[cite: 108, 132].
- [cite_start]**Interfaz Gráfica:** Panel de gestión desarrollado en Tkinter/PyQt[cite: 75, 113].

## 📁 Estructura del Repositorio
- [cite_start]`scripts/`: Scripts de Python para tareas específicas (backups, despliegue de OSPF, etc.)[cite: 156].
- [cite_start]`ansible/`: Playbooks e inventarios para la gestión con Ansible[cite: 155].
- [cite_start]`src/`: Código fuente principal, incluyendo módulos de lógica (`modules/`) y la GUI (`gui.py`)[cite: 180].
- [cite_start]`inventory/`: Archivos de definición de dispositivos y hosts[cite: 142].
- `tests/`: Pruebas unitarias para validar la lógica del sistema.

## 🛠️ Tecnologías Utilizadas
- [cite_start]**Lenguajes:** Python 3.x[cite: 156].
- [cite_start]**Automatización:** Ansible[cite: 155].
- [cite_start]**Librerías Python:** Netmiko, NAPALM, Paramiko, PyWinRM[cite: 87, 171].
- [cite_start]**Entornos:** GNS3 / EVE-NG para simulaciones y hardware real para validación[cite: 111, 150].