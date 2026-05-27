"""Versao: 0.1.0
Criado em: 2026-05-27 23:00:00 -03:00
Criado por: brainstorming colaborativo
Projeto/pasta: ha.ext.tarifas
"""

from __future__ import annotations

import ssl
from functools import lru_cache
from pathlib import Path

_CHAIN_PATH = Path(__file__).parent / "certs" / "aneel-trust-chain.pem"


def chain_pem_path() -> Path:
    """Retorna caminho do PEM empacotado com o chain Sectigo."""

    return _CHAIN_PATH


@lru_cache(maxsize=1)
def build_aneel_ssl_context() -> ssl.SSLContext:
    """Constroi SSLContext com trust store padrao + intermediarios Sectigo.

    dadosabertos.aneel.gov.br envia apenas o certificado leaf no handshake
    TLS. Sem o intermediario, Python falha com 'unable to get local issuer
    certificate' em ambientes com trust store recente (HA OS 17.3+, Python
    3.14+). Empacotamos o chain para que a verificacao funcione sem
    dependencia do CA store do sistema.

    Faz I/O bloqueante (leitura do PEM). Quando chamada do event loop do
    Home Assistant, invoque via `hass.async_add_executor_job`.
    """

    context = ssl.create_default_context()
    context.load_verify_locations(cafile=str(_CHAIN_PATH))
    return context
