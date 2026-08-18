"""Fixtures compartilhadas por toda a suite de testes.

A API exige autenticacao (JWT); o fixture `api_client` abaixo autentica um
usuario de teste automaticamente via `force_authenticate`, para que os testes
continuem exercitando as REGRAS DE NEGOCIO (validacoes, disponibilidade,
status), sem cada um precisar fazer login manualmente.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def usuario_teste(db):
    return get_user_model().objects.create_user(username="usuario_teste", password="senha-teste-123")


@pytest.fixture
def api_client(usuario_teste) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=usuario_teste)
    return client
