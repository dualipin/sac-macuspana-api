import os
import mimetypes
from datetime import datetime
from django.core.exceptions import ValidationError


def parsear_fecha(fecha: str):
    return datetime.strptime(fecha, "%d/%m/%Y").date().isoformat()


def validar_archivo_documento(archivo):
    """
    Valida que el archivo sea PDF, JPG o PNG y no exceda 5MB
    """
    # Validar tamaño máximo: 5MB
    max_size = 5 * 1024 * 1024  # 5MB en bytes
    if archivo.size > max_size:
        raise ValidationError(
            f"El archivo no debe exceder 5MB. Tamaño actual: {archivo.size / 1024 / 1024:.2f}MB"
        )

    # Validar extensión
    ext = os.path.splitext(archivo.name)[1].lower()
    extensiones_permitidas = [".pdf", ".jpg", ".jpeg", ".png"]
    if ext not in extensiones_permitidas:
        raise ValidationError(
            f"Formato de archivo no permitido. Solo se permiten: PDF, JPG, PNG"
        )

    # Validar tipo MIME
    mime_type, _ = mimetypes.guess_type(archivo.name)
    tipos_mime_permitidos = ["application/pdf", "image/jpeg", "image/png"]

    if mime_type not in tipos_mime_permitidos:
        raise ValidationError(f"Tipo de archivo no válido. Se detectó: {mime_type}")
