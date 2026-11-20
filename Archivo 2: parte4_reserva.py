# =====================================================================
# SISTEMA INTEGRAL DE GESTIÓN DE CLIENTES, SERVICIOS Y RESERVAS
# Empresa: Software FJ | Programación 213023 - UNAD | Fase 4
# PARTE 4 - Clase Reserva y gestor de reservas
# =====================================================================

from parte1_log_excepciones import (    # log y excepciones de la Parte 1
    log,
    SoftwareFJError,
    DatoInvalidoError,
    ParametroFaltanteError,
    OperacionNoPermitidaError,
    ServicioNoDisponibleError,
    ReservaInvalidaError,
    CalculoInconsistenteError,
)
from parte2_cliente import Cliente      # clase Cliente de la Parte 2
from parte3_servicios import (          # entidad abstracta y servicios de la Parte 3
    Entidad,
    Servicio,
    ReservaSala,
    AlquilerEquipo,
    AsesoriaEspecializada,
)


class Reserva(Entidad):
    """Une un cliente, un servicio y una duración, y controla el estado."""

    PENDIENTE = "PENDIENTE"             # estados posibles de una reserva
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    PROCESADA = "PROCESADA"

    _consecutivo = 0                    # contador para numerar las reservas

    def __init__(self, cliente, servicio, duracion):
        # ningún dato puede faltar
        if cliente is None or servicio is None or duracion is None:
            raise ParametroFaltanteError("La reserva necesita cliente, servicio y duración.")
        # el cliente debe ser un objeto de la Parte 2
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("El cliente indicado no está registrado como Cliente.")
        # el servicio debe ser un objeto de la Parte 3
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("El servicio indicado no es un servicio del sistema.")
        # no se reserva un servicio que está fuera de servicio
        if not servicio.disponible:
            raise ServicioNoDisponibleError(f"El servicio {servicio.codigo} no está disponible.")
        try:
            servicio.validar_parametros(duracion)       # el servicio decide si la duración sirve
        except DatoInvalidoError as error:
            # encadenamiento: la reserva falla y se conserva el motivo original
            raise ReservaInvalidaError(
                f"Duración no válida para el servicio {servicio.codigo}."
            ) from error

        super().__init__()                              # registra la fecha de creación
        Reserva._consecutivo += 1                       # siguiente número de reserva
        self.__numero = Reserva._consecutivo
        self.__cliente = cliente
        self.__servicio = servicio
        self.__duracion = duracion
        self.__estado = Reserva.PENDIENTE               # toda reserva nace pendiente
        self.__costo = None                             # se conoce solo después de procesar

    # ---------- propiedades de solo lectura ----------
    @property
    def numero(self):
        return self.__numero

    @property
    def cliente(self):
        return self.__cliente

    @property
    def servicio(self):
        return self.__servicio

    @property
    def duracion(self):
        return self.__duracion

    @property
    def estado(self):
        return self.__estado

    @property
    def costo(self):
        return self.__costo

    # ---------- operaciones ----------
    def confirmar(self):
        """Pasa la reserva de PENDIENTE a CONFIRMADA."""
        # solo se confirma lo que está pendiente
        if self.__estado != Reserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"La reserva {self.__numero} está {self.__estado} y no se puede confirmar."
            )
        # el servicio pudo quedar fuera de servicio después de crear la reserva
        if not self.__servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio {self.__servicio.codigo} ya no está disponible."
            )
        self.__estado = Reserva.CONFIRMADA
        log.info(f"Reserva {self.__numero} confirmada.")

    def cancelar(self):
        """Cancela la reserva si todavía no está cancelada ni procesada."""
        if self.__estado in (Reserva.CANCELADA, Reserva.PROCESADA):
            raise OperacionNoPermitidaError(
                f"La reserva {self.__numero} está {self.__estado} y no se puede cancelar."
            )
        self.__estado = Reserva.CANCELADA
        log.info(f"Reserva {self.__numero} cancelada.")

    def procesar(self, impuesto=None, descuento=None):
        """Calcula el costo final y deja la reserva PROCESADA."""
        # solo se procesa una reserva confirmada
        if self.__estado != Reserva.CONFIRMADA:
            raise OperacionNoPermitidaError(
                f"La reserva {self.__numero} está {self.__estado}; debe confirmarse antes de procesar."
            )
        log.info(f"Inicia el procesamiento de la reserva {self.__numero}.")
        try:
            # el cálculo lo hace el servicio, con sus variantes de impuesto y descuento
            costo = self.__servicio.calcular_costo(self.__duracion, impuesto, descuento)
        except SoftwareFJError as error:
            # error conocido del sistema: se envuelve como error de reserva
            raise ReservaInvalidaError(
                f"No se pudo procesar la reserva {self.__numero}."
            ) from error
        except (ArithmeticError, TypeError, ValueError) as error:
            # error inesperado de cálculo: se convierte en una excepción propia
            raise CalculoInconsistenteError(
                f"Falló el cálculo de la reserva {self.__numero}."
            ) from error
        else:
            self.__costo = costo                        # solo si el cálculo salió bien
            self.__estado = Reserva.PROCESADA
            log.info(f"Reserva {self.__numero} procesada por ${costo:,.2f}.")
            return costo
        finally:
            # este registro se hace siempre, haya salido bien o mal
            log.info(f"Termina el procesamiento de la reserva {self.__numero} "
                     f"en estado {self.__estado}.")

    def describir(self):
        # si Cliente expone la propiedad nombre se usa; si no, un texto genérico
        nombre = getattr(self.__cliente, "nombre", "cliente registrado")
        costo = f"${self.__costo:,.2f}" if self.__costo is not None else "sin calcular"
        return (f"Reserva {self.__numero} | {nombre} | {self.__servicio.codigo} | "
                f"{self.__duracion} h | {self.__estado} | {costo}")

    def __str__(self):
        return self.describir()                         # al imprimir se muestra la descripción


class GestorReservas:
    """Guarda las reservas en una lista y evita que un error detenga el programa."""

    def __init__(self):
        self.__reservas = []                            # lista interna de reservas

    def crear_reserva(self, cliente, servicio, duracion):
        """Devuelve la reserva creada, o None si hubo un error controlado."""
        try:
            reserva = Reserva(cliente, servicio, duracion)
        except SoftwareFJError as error:
            self.__reportar("crear la reserva", error)  # queda en el log y el programa sigue
            return None
        else:
            self.__reservas.append(reserva)             # solo se guarda si se creó bien
            log.info(f"Reserva creada: {reserva}")
            return reserva

    def buscar(self, numero):
        # se recorre la lista hasta encontrar el número pedido
        for reserva in self.__reservas:
            if reserva.numero == numero:
                return reserva
        raise ReservaInvalidaError(f"No existe la reserva número {numero}.")

    def confirmar_reserva(self, numero):
        return self.__operar(numero, "confirmar")

    def cancelar_reserva(self, numero):
        return self.__operar(numero, "cancelar")

    def procesar_reserva(self, numero, impuesto=None, descuento=None):
        return self.__operar(numero, "procesar", impuesto=impuesto, descuento=descuento)

    def listar(self):
        return list(self.__reservas)                    # copia para proteger la lista interna

    def __operar(self, numero, accion, **opciones):
        """Ejecuta confirmar, cancelar o procesar sin dejar caer el programa."""
        try:
            reserva = self.buscar(numero)               # puede fallar si el número no existe
            resultado = getattr(reserva, accion)(**opciones)   # ejecuta el método pedido
        except SoftwareFJError as error:
            self.__reportar(f"{accion} la reserva {numero}", error)
            return None
        else:
            # procesar devuelve el costo; confirmar y cancelar devuelven True
            return resultado if resultado is not None else True

    @staticmethod
    def __reportar(accion, error):
        """Escribe el error y su causa en el log y lo muestra en pantalla."""
        # __cause__ existe cuando la excepción fue encadenada con "raise ... from"
        causa = f" Causa: {error.__cause__}" if error.__cause__ else ""
        mensaje = f"No se pudo {accion}: {error}{causa}"
        log.error(mensaje)
        print("Error controlado ->", mensaje)


# Prueba rápida del módulo: solo corre al ejecutar este archivo directamente
if __name__ == "__main__":
    gestor = GestorReservas()

    # un cliente y tres servicios de prueba
    cliente = Cliente("Laura Gómez", "1098765432", "laura@correo.com", "3001234567")
    sala = ReservaSala("S01", "Sala Andes", 80000, 25)
    equipo = AlquilerEquipo("E01", "Portátil i7", 15000, 3)
    asesoria = AsesoriaEspecializada("A01", "Arquitectura de software", 120000, "experto")

    # 1. reserva correcta: se crea, se confirma y se procesa con IVA
    r1 = gestor.crear_reserva(cliente, sala, 3)
    gestor.confirmar_reserva(r1.numero)
    print("Costo reserva 1:", gestor.procesar_reserva(r1.numero, impuesto=Servicio.IVA))

    # 2. duración fuera de rango: falla y el programa sigue
    gestor.crear_reserva(cliente, asesoria, 20)

    # 3. reserva sin cliente: parámetro faltante
    gestor.crear_reserva(None, equipo, 5)

    # 4. procesar sin confirmar: operación no permitida
    r4 = gestor.crear_reserva(cliente, equipo, 24)
    gestor.procesar_reserva(r4.numero)

    # 5. descuento del 500 %: cálculo inconsistente, llega encadenado
    gestor.confirmar_reserva(r4.numero)
    gestor.procesar_reserva(r4.numero, descuento=5)

    # 6. servicio que queda fuera de servicio antes de confirmar
    r6 = gestor.crear_reserva(cliente, asesoria, 2)
    asesoria.disponible = False
    gestor.confirmar_reserva(r6.numero)

    # 7. cancelar dos veces: la segunda no se permite
    gestor.cancelar_reserva(r6.numero)
    gestor.cancelar_reserva(r6.numero)

    # resumen final: el programa llegó hasta aquí sin detenerse
    print("\nReservas registradas:")
    for reserva in gestor.listar():
        print("  ", reserva)
