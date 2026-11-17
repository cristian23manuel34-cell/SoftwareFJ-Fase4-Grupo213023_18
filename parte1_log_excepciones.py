# =====================================================================
# SISTEMA INTEGRAL DE GESTIÓN DE CLIENTES, SERVICIOS Y RESERVAS
# Empresa: Software FJ | Programación 213023 - UNAD | Fase 4
# PARTE 1 - Log del sistema y excepciones personalizadas
# =====================================================================

import logging                          # módulo estándar para registrar eventos en archivo
import re                               # expresiones regulares para validar nombre y correo
from abc import ABC, abstractmethod     # permite declarar clases y métodos abstractos
from datetime import datetime           # guarda la fecha de creación de cada entidad

ARCHIVO_LOG = "software_fj.log"         # archivo donde quedan todos los eventos y errores

logging.basicConfig(                    # configuración del registro de eventos
    filename=ARCHIVO_LOG,               # se escribe en el archivo, no en pantalla
    level=logging.INFO,                 # guarda INFO, WARNING, ERROR y CRITICAL
    format="%(asctime)s | %(levelname)-8s | %(message)s",  # fecha | nivel | mensaje
    encoding="utf-8",                   # conserva tildes y eñes
    force=True                          # si se ejecuta de nuevo, reinicia la configuración
)
log = logging.getLogger("SoftwareFJ")   # logger propio de la aplicación


class SoftwareFJError(Exception):
    """Excepción base del sistema; todas las propias heredan de esta."""


class DatoInvalidoError(SoftwareFJError):
    """Un dato no cumple el formato o el rango permitido."""


class ParametroFaltanteError(SoftwareFJError):
    """Falta un dato obligatorio o llegó vacío."""


class OperacionNoPermitidaError(SoftwareFJError):
    """La operación no es válida para el estado actual del objeto."""


class ServicioNoDisponibleError(SoftwareFJError):
    """El servicio existe pero no se puede reservar en este momento."""


class ReservaInvalidaError(SoftwareFJError):
    """La reserva no se pudo crear o liquidar."""


class CalculoInconsistenteError(SoftwareFJError):
    """El cálculo del costo da un valor sin sentido (descuento > 100 %, total negativo...)."""


log.info("===== Nueva ejecución del sistema Software FJ =====")  # marca de inicio en el log
print("Parte 1 cargada. Log configurado en:", ARCHIVO_LOG)        # confirmación en pantalla
