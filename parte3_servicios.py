# =====================================================================
# SISTEMA INTEGRAL DE GESTIÓN DE CLIENTES, SERVICIOS Y RESERVAS
# Empresa: Software FJ | Programación 213023 - UNAD | Fase 4
# PARTE 3 - Entidad abstracta, clase abstracta Servicio y servicios
# =====================================================================

import math                             # sirve para revisar que un costo sea un número finito
from abc import ABC, abstractmethod     # permite declarar clases y métodos abstractos
from datetime import datetime           # guarda la fecha de creación de cada entidad

from parte1_log_excepciones import (    # se reutiliza todo lo definido en la Parte 1
    log,                                # logger que escribe en software_fj.log
    SoftwareFJError,                    # excepción base del sistema
    DatoInvalidoError,                  # dato con formato o rango incorrecto
    ParametroFaltanteError,             # falta un dato obligatorio
    OperacionNoPermitidaError,          # acción no válida en el estado actual
    ServicioNoDisponibleError,          # servicio que no se puede usar ahora
    CalculoInconsistenteError,          # costo que no tiene sentido
)


class Entidad(ABC):
    """Clase abstracta que representa cualquier entidad general del sistema."""

    def __init__(self):
        self._fecha_creacion = datetime.now()   # momento en que se creó el objeto

    @property
    def fecha_creacion(self):
        return self._fecha_creacion             # solo lectura

    @abstractmethod
    def describir(self):
        """Cada entidad debe saber describirse con un texto."""


def validar_porcentaje(valor, nombre):
    """Revisa que un impuesto o descuento esté entre 0 y 1 (0.19 = 19 %)."""
    # bool se descarta porque Python lo trata como número
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise DatoInvalidoError(f"El {nombre} debe ser un número entre 0 y 1.")
    # un descuento mayor al 100 % o un impuesto negativo no tienen sentido
    if not 0 <= valor <= 1:
        raise CalculoInconsistenteError(
            f"El {nombre} debe estar entre 0 y 1, se recibió {valor}."
        )
    return float(valor)                         # se devuelve como decimal


class Servicio(Entidad):
    """Clase abstracta con lo que comparten todos los servicios de Software FJ."""

    IVA = 0.19                                  # impuesto de referencia para las pruebas

    def __init__(self, codigo, nombre, tarifa_hora, disponible=True):
        # primero se revisa que no falte ningún dato obligatorio
        if codigo is None or nombre is None or tarifa_hora is None:
            raise ParametroFaltanteError("Código, nombre y tarifa son obligatorios.")
        super().__init__()                      # registra la fecha de creación
        self.codigo = codigo                    # cada asignación pasa por su setter,
        self.nombre = nombre                    # que es donde se hace la validación
        self.tarifa_hora = tarifa_hora
        self.disponible = disponible

    # ---------- propiedades con encapsulación ----------
    @property
    def codigo(self):
        return self.__codigo

    @codigo.setter
    def codigo(self, valor):
        # el código debe ser un texto con contenido
        if not isinstance(valor, str) or not valor.strip():
            raise DatoInvalidoError("El código del servicio debe ser un texto no vacío.")
        self.__codigo = valor.strip().upper()   # se guarda en mayúsculas y sin espacios

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        # el nombre debe tener al menos tres caracteres
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoInvalidoError("El nombre del servicio debe tener al menos 3 caracteres.")
        self.__nombre = valor.strip()

    @property
    def tarifa_hora(self):
        return self.__tarifa_hora

    @tarifa_hora.setter
    def tarifa_hora(self, valor):
        try:
            tarifa = float(valor)               # se intenta convertir a número
        except (TypeError, ValueError) as error:
            # encadenamiento: se conserva el error original como causa
            raise DatoInvalidoError(f"La tarifa '{valor}' no es un número.") from error
        # la tarifa debe ser positiva y finita
        if not math.isfinite(tarifa) or tarifa <= 0:
            raise DatoInvalidoError("La tarifa por hora debe ser mayor que cero.")
        self.__tarifa_hora = tarifa

    @property
    def disponible(self):
        return self.__disponible

    @disponible.setter
    def disponible(self, valor):
        # solo se acepta True o False
        if not isinstance(valor, bool):
            raise DatoInvalidoError("La disponibilidad debe ser True o False.")
        self.__disponible = valor

    # ---------- métodos que cada servicio debe sobrescribir ----------
    @abstractmethod
    def validar_parametros(self, duracion):
        """Revisa que la duración sea válida para este tipo de servicio."""

    @abstractmethod
    def calcular_costo_base(self, duracion):
        """Devuelve el costo sin impuestos ni descuentos."""

    # describir() ya es abstracto porque viene de Entidad

    # ---------- método común con variantes (sobrecarga) ----------
    def calcular_costo(self, duracion, impuesto=None, descuento=None):
        """
        Sobrecarga mediante parámetros opcionales:
          calcular_costo(d)                      -> costo base
          calcular_costo(d, impuesto)            -> base más impuesto
          calcular_costo(d, descuento=x)         -> base menos descuento
          calcular_costo(d, impuesto, descuento) -> descuento y luego impuesto
        """
        # un servicio fuera de servicio no se puede cotizar
        if not self.disponible:
            raise ServicioNoDisponibleError(f"El servicio {self.codigo} no está disponible.")
        self.validar_parametros(duracion)               # cada subclase valida a su manera
        costo = self.calcular_costo_base(duracion)      # cada subclase calcula a su manera
        if descuento is not None:                       # si llega descuento, va primero
            costo -= costo * validar_porcentaje(descuento, "descuento")
        if impuesto is not None:                        # el impuesto va sobre lo ya descontado
            costo += costo * validar_porcentaje(impuesto, "impuesto")
        # revisión final: el resultado debe ser un número finito y no negativo
        if not math.isfinite(costo) or costo < 0:
            raise CalculoInconsistenteError(f"Costo inconsistente en {self.codigo}: {costo}")
        return round(costo, 2)                          # se entrega con dos decimales

    def _validar_duracion(self, duracion, minimo, maximo):
        """Validación de duración que reutilizan las subclases."""
        if duracion is None:                            # la duración es obligatoria
            raise ParametroFaltanteError("Falta la duración del servicio.")
        # debe ser un número (bool no cuenta)
        if isinstance(duracion, bool) or not isinstance(duracion, (int, float)):
            raise DatoInvalidoError(f"La duración '{duracion}' no es un número.")
        # debe estar dentro del rango permitido para el servicio
        if not minimo <= duracion <= maximo:
            raise DatoInvalidoError(
                f"La duración debe estar entre {minimo} y {maximo} horas, se recibió {duracion}."
            )

    def __str__(self):
        return self.describir()                         # al imprimir se muestra la descripción


class ReservaSala(Servicio):
    """Servicio 1: reserva de salas de reuniones."""

    def __init__(self, codigo, nombre, tarifa_hora, capacidad, disponible=True):
        super().__init__(codigo, nombre, tarifa_hora, disponible)   # datos comunes
        # la capacidad debe ser un entero entre 1 y 100 personas
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or not 1 <= capacidad <= 100:
            raise DatoInvalidoError("La capacidad de la sala debe ser un entero entre 1 y 100.")
        self.__capacidad = capacidad

    @property
    def capacidad(self):
        return self.__capacidad

    def validar_parametros(self, duracion):
        self._validar_duracion(duracion, 1, 12)         # una sala: mínimo 1 hora, máximo 12

    def calcular_costo_base(self, duracion):
        costo = self.tarifa_hora * duracion             # tarifa por horas
        if self.capacidad > 20:                         # salas grandes: recargo del 10 %
            costo *= 1.10
        return costo

    def describir(self):
        return (f"[{self.codigo}] Sala '{self.nombre}' para {self.capacidad} personas, "
                f"${self.tarifa_hora:,.0f} por hora")


class AlquilerEquipo(Servicio):
    """Servicio 2: alquiler de equipos."""

    def __init__(self, codigo, nombre, tarifa_hora, cantidad, disponible=True):
        super().__init__(codigo, nombre, tarifa_hora, disponible)   # datos comunes
        # la cantidad de equipos debe ser un entero positivo
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad < 1:
            raise DatoInvalidoError("La cantidad de equipos debe ser un entero mayor que cero.")
        self.__cantidad = cantidad

    @property
    def cantidad(self):
        return self.__cantidad

    def validar_parametros(self, duracion):
        self._validar_duracion(duracion, 1, 72)         # un equipo: entre 1 y 72 horas

    def calcular_costo_base(self, duracion):
        costo = self.tarifa_hora * duracion * self.cantidad   # horas por número de equipos
        if duracion >= 24:                              # un día o más: rebaja del 5 %
            costo *= 0.95
        return costo

    def describir(self):
        return (f"[{self.codigo}] Alquiler de {self.cantidad} x '{self.nombre}', "
                f"${self.tarifa_hora:,.0f} por hora y por equipo")


class AsesoriaEspecializada(Servicio):
    """Servicio 3: asesorías especializadas."""

    NIVELES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}   # factor según el asesor

    def __init__(self, codigo, nombre, tarifa_hora, nivel="junior", disponible=True):
        super().__init__(codigo, nombre, tarifa_hora, disponible)   # datos comunes
        # el nivel debe ser uno de los tres definidos
        if not isinstance(nivel, str) or nivel.strip().lower() not in self.NIVELES:
            raise DatoInvalidoError(f"Nivel '{nivel}' no válido. Use: {', '.join(self.NIVELES)}.")
        self.__nivel = nivel.strip().lower()

    @property
    def nivel(self):
        return self.__nivel

    def validar_parametros(self, duracion):
        self._validar_duracion(duracion, 0.5, 8)        # una asesoría: de media hora a 8 horas

    def calcular_costo_base(self, duracion):
        # la tarifa se multiplica por el factor del nivel del asesor
        return self.tarifa_hora * duracion * self.NIVELES[self.nivel]

    def describir(self):
        return (f"[{self.codigo}] Asesoría '{self.nombre}' nivel {self.nivel}, "
                f"${self.tarifa_hora:,.0f} por hora")


class CatalogoServicios:
    """Guarda los servicios en una lista interna (sin base de datos)."""

    def __init__(self):
        self.__servicios = []                           # lista interna de servicios

    def agregar(self, servicio):
        # solo se aceptan objetos que hereden de Servicio
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("Solo se pueden agregar objetos de tipo Servicio.")
        # no se permiten códigos repetidos
        if any(s.codigo == servicio.codigo for s in self.__servicios):
            raise OperacionNoPermitidaError(f"Ya existe un servicio con código {servicio.codigo}.")
        self.__servicios.append(servicio)               # se guarda en la lista
        log.info(f"Servicio agregado: {servicio.describir()}")

    def buscar(self, codigo):
        # se recorre la lista hasta encontrar el código pedido
        for servicio in self.__servicios:
            if servicio.codigo == str(codigo).strip().upper():
                return servicio
        raise ServicioNoDisponibleError(f"No existe un servicio con código {codigo}.")

    def listar(self):
        return list(self.__servicios)                   # copia para proteger la lista interna


# Prueba rápida del módulo: solo corre al ejecutar este archivo directamente
if __name__ == "__main__":
    catalogo = CatalogoServicios()

    # datos de prueba: tres correctos y uno con la tarifa mal escrita
    datos = [
        (ReservaSala, ("S01", "Sala Andes", 80000, 25)),
        (AlquilerEquipo, ("E01", "Portátil i7", 15000, 3)),
        (AsesoriaEspecializada, ("A01", "Arquitectura de software", 120000, "senior")),
        (AlquilerEquipo, ("E02", "Proyector", "gratis", 1)),
    ]

    for clase, argumentos in datos:
        try:
            catalogo.agregar(clase(*argumentos))        # se intenta crear y guardar
        except SoftwareFJError as error:
            # el error queda en el log y el ciclo sigue con el siguiente dato
            log.error(f"No se creó el servicio {argumentos[0]}: {error} | causa: {error.__cause__!r}")
            print("Error controlado:", error)
        else:
            print("Servicio creado:", argumentos[0])    # solo entra si no hubo error

    # polimorfismo: el mismo llamado da resultados distintos según el servicio
    for servicio in catalogo.listar():
        print(servicio)
        print("   2 horas, costo base:      ", servicio.calcular_costo(2))
        print("   2 horas con IVA:          ", servicio.calcular_costo(2, Servicio.IVA))
        print("   2 horas, IVA y 10 % dcto.:", servicio.calcular_costo(2, Servicio.IVA, 0.10))
