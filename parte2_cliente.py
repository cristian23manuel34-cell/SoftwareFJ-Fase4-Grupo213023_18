from parte1_log_excepciones import (
    log,
    DatoInvalidoError,
    ParametroFaltanteError
)

class Cliente:

    def __init__(self, nombre, cedula, correo, telefono):

        if nombre.strip() == "":
            raise ParametroFaltanteError ("El nombre no puede estar vacío")

        if cedula.strip() == "":
            raise ParametroFaltanteError("La cédula no puede estar vacía")

        if "@" not in correo:
            raise DatoInvalidoError("Correo electrónico inválido")

        if telefono.strip() == "":
            raise ParametroFaltanteError("El teléfono no puede estar vacío")

        self.__nombre = nombre
        self.__cedula = cedula
        self.__correo = correo
        self.__telefono = telefono

        log.info(f"Cliente registrado: {nombre}")

    def mostrar_info(self):
        print("Nombre:", self.__nombre)
        print("Cédula:", self.__cedula)
        print("Correo:", self.__correo)
        print("Teléfono:", self.__telefono)

        

    def actualizar_correo(self, nuevo_correo):

        if "@" not in nuevo_correo:
            raise DatoInvalidoError("Correo electrónico inválido")

        self.__correo = nuevo_correo

    def actualizar_telefono(self, nuevo_telefono):

        if nuevo_telefono.strip() == "":
            raise ParametroFaltanteError("El teléfono no puede estar vacío")

        self.__telefono = nuevo_telefono

