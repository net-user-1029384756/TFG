import logging
import os

def setup_logger(name="tfg_automation"):
    """
    Configura y devuelve un logger profesional.
    Muestra INFO por consola y guarda DEBUG en un archivo .log.
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicar handlers si se llama varias veces
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Crear carpeta de logs si no existe
        os.makedirs("logs", exist_ok=True)
        
        # Handler para consola (Terminal)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Handler para archivo (Evidencia para el TFG)
        file_handler = logging.FileHandler("logs/automatizacion.log", encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Formato estándar
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
    return logger

# Instancia global para importar en otros scripts
log = setup_logger()