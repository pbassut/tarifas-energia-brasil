"""Versao: 0.1.0
Criado em: 2026-05-27 23:30:00 -03:00
Criado por: brainstorming colaborativo
Projeto/pasta: ha.ext.tarifas
"""

from __future__ import annotations

import importlib.util
import ssl
import sys
import types
from enum import StrEnum
from pathlib import Path


def _install_fake_homeassistant_modules() -> None:
    """Instala stubs minimos para importar o pacote sem Home Assistant real."""

    homeassistant = sys.modules.get("homeassistant", types.ModuleType("homeassistant"))
    const = sys.modules.get("homeassistant.const", types.ModuleType("homeassistant.const"))

    class Platform(StrEnum):
        SENSOR = "sensor"

    const.Platform = Platform
    homeassistant.const = const
    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.const"] = const


_install_fake_homeassistant_modules()


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_BASE_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "tarifas_energia_brasil"
_PKG_NAME = "tarifas_energia_brasil_testpkg_ssl"

if _PKG_NAME not in sys.modules:
    pkg = types.ModuleType(_PKG_NAME)
    pkg.__path__ = [str(_BASE_DIR)]  # type: ignore[attr-defined]
    sys.modules[_PKG_NAME] = pkg

ssl_context_module = _load_module(
    f"{_PKG_NAME}.ssl_context",
    _BASE_DIR / "ssl_context.py",
)


def test_chain_pem_exists_with_multiple_certificates():
    """O PEM empacotado precisa existir e conter pelo menos 2 certificados."""

    pem_path = ssl_context_module.chain_pem_path()
    assert pem_path.is_file(), f"Bundle de certificados ausente: {pem_path}"

    raw = pem_path.read_text(encoding="ascii")
    assert raw.count("-----BEGIN CERTIFICATE-----") >= 2
    assert raw.count("-----END CERTIFICATE-----") == raw.count("-----BEGIN CERTIFICATE-----")


def test_build_aneel_ssl_context_returns_cached_instance():
    """Repetidas chamadas devem reaproveitar o mesmo SSLContext (lru_cache)."""

    ssl_context_module.build_aneel_ssl_context.cache_clear()
    ctx1 = ssl_context_module.build_aneel_ssl_context()
    ctx2 = ssl_context_module.build_aneel_ssl_context()

    assert isinstance(ctx1, ssl.SSLContext)
    assert ctx1 is ctx2


def test_build_aneel_ssl_context_loads_sectigo_certificates():
    """O contexto deve passar a confiar nos certificados Sectigo empacotados."""

    ssl_context_module.build_aneel_ssl_context.cache_clear()
    ctx = ssl_context_module.build_aneel_ssl_context()
    subjects = {
        dict(ch[0] for ch in cert.get("subject", [])).get("commonName", "")
        for cert in ctx.get_ca_certs()
    }

    assert "Sectigo Public Server Authentication CA OV R36" in subjects
    assert "Sectigo Public Server Authentication Root R46" in subjects


