"""A suíte ordinária e o Replay rodam sempre offline, mesmo com uma chave de
API presente no ambiente. Só os testes de integração opt-in (`CXLAB_TEST_*`)
liberam rede real; todo o resto tem `socket.socket.connect` negado, para que
uma chamada de rede indevida quebre o teste em vez de silenciosamente sair
para a internet.
"""

import os
import socket

import pytest

_HABILITACOES = ("CXLAB_TEST_GATEWAY", "CXLAB_TEST_ANTHROPIC")


@pytest.fixture(autouse=True)
def rede_negada(monkeypatch):
    if any(os.environ.get(var) == "1" for var in _HABILITACOES):
        yield
        return

    def _negar(*_args, **_kwargs):
        raise OSError("rede negada pela suíte de testes offline")

    monkeypatch.setattr(socket.socket, "connect", _negar)
    yield
