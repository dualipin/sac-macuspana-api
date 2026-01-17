import requests
from typing import Dict
from django.conf import settings


class CurpServiceError(Exception):
    """Errores de integración con la API de CURP."""

    def __init__(self, message: str, code: str = "curp_service_error"):
        super().__init__(message)
        self.code = code


def consultar_curp(curp: str) -> Dict:
    curp_upper = curp.upper()

    params = {"curp": curp_upper}

    headers = {
        "Accept": "application/json",
        "User-Agent": "bruno-runtime/2.15.1",
        "Accept-Language": "es-MX,es;q=0.9",
    }

    try:
        resp = requests.get(
            settings.CURP_API_URL,
            headers=headers,
            params=params,
            verify=True,
            timeout=10,
        )

        if resp.status_code >= 500:
            raise CurpServiceError("Error temporal del proveedor")

        if resp.status_code == 400:
            raise CurpServiceError("Solicitud inválida a proveedor CURP.")

        if resp.status_code == 404:
            raise CurpServiceError("Endpoint no encontrado.")

        # Verificar que la respuesta no esté vacía
        if not resp.text or resp.text.strip() == "":
            raise CurpServiceError("Respuesta vacía del servidor")

        # Verificar que el Content-Type sea JSON
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise CurpServiceError(
                f"Respuesta no es JSON. Content-Type: {content_type}. Contenido: {resp.text[:200]}"
            )

        try:
            data = resp.json()
        except requests.JSONDecodeError:
            raise CurpServiceError(
                f"Respuesta no es JSON válido. Contenido: {resp.text[:200]}"
            )

        # Verificar estructura de la respuesta
        if "status" not in data:
            raise CurpServiceError(f'Respuesta sin campo "status". Datos: {data}')

        if data["status"] != "success":
            raise CurpServiceError("CURP no encontrada o inválida.")

        if "procesado" not in data:
            raise CurpServiceError(f'Respuesta sin campo "procesado". Datos: {data}')

        procesado = data["procesado"]

        if not procesado or not procesado.get("nombres"):
            raise CurpServiceError("CURP no encontrada en el padrón.")

        return procesado

    except (requests.Timeout, requests.ConnectionError) as ex:

        raise CurpServiceError(f"Error de conexión: {str(ex)}") from ex

    except requests.HTTPError as ex:

        raise CurpServiceError(f"Error HTTP: {str(ex)}") from ex

    except CurpServiceError:

        # Re-lanzar errores personalizados
        raise

    except Exception as ex:
        # Cualquier otro error inesperado

        raise CurpServiceError(f"Error inesperado: {str(ex)}") from ex
