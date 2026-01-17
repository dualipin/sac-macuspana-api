import re
import hashlib
from rest_framework import serializers
from ciudadanos.models import Ciudadano


def validate_curp_format(value: str):
    # 1. Formato
    regex = r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$'
    curp_upper = value.upper()
    if not re.match(regex, curp_upper):
        raise serializers.ValidationError("Formato de CURP inválido.")

    # 2. Unicidad usando el Hash
    c_hash = hashlib.sha256(curp_upper.encode()).hexdigest()
    if Ciudadano.objects.filter(curp_hash=c_hash).exists():
        raise serializers.ValidationError("Esta CURP ya está registrada.")

    return curp_upper


def check_curp_unica(value: str):
    curp_upper = value.upper()
    # Generamos el hash para comparar
    hash_curp = hashlib.sha256(curp_upper.encode()).hexdigest()

    if Ciudadano.objects.filter(curp_hash=hash_curp).exists():
        raise serializers.ValidationError("La CURP ya está registrada.")
