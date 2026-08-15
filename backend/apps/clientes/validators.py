import re

from django.core.exceptions import ValidationError


def somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def _digito_verificador(numeros: list[int], pesos: list[int]) -> int:
    soma = sum(n * p for n, p in zip(numeros, pesos))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf: str) -> bool:
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    numeros = [int(d) for d in cpf]
    d1 = _digito_verificador(numeros[:9], list(range(10, 1, -1)))
    d2 = _digito_verificador(numeros[:10], list(range(11, 1, -1)))
    return numeros[9] == d1 and numeros[10] == d2


def cnpj_valido(cnpj: str) -> bool:
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    numeros = [int(d) for d in cnpj]
    d1 = _digito_verificador(numeros[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = _digito_verificador(numeros[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return numeros[12] == d1 and numeros[13] == d2


def validar_documento(valor: str) -> None:
    """Aceita CPF (11 digitos) ou CNPJ (14 digitos), com ou sem mascara."""
    digitos = somente_digitos(valor)
    if len(digitos) == 11:
        if not cpf_valido(digitos):
            raise ValidationError("CPF invalido.")
    elif len(digitos) == 14:
        if not cnpj_valido(digitos):
            raise ValidationError("CNPJ invalido.")
    else:
        raise ValidationError("Documento deve ser um CPF (11 digitos) ou CNPJ (14 digitos).")
