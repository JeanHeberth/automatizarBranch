"""
Configuração central de testes e fixtures compartilhadas.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_repo_path():
    """Fixture que fornece um caminho de repositório mockado."""
    return "/tmp/test_repo"


@pytest.fixture
def mock_git_output():
    """Fixture que fornece saída mockada de comandos Git."""
    return MagicMock()


@pytest.fixture(autouse=True)
def clear_cache():
    """Limpa cache antes de cada teste (autouse)."""
    from core.cache import get_cache
    cache = get_cache()
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def mock_subprocess():
    """Fixture que mocka subprocess.run para testes Git."""
    with patch('core.git_operations.subprocess.run') as mock:
        yield mock


@pytest.fixture
def test_logger(caplog):
    """Fixture que fornece logger para testes."""
    import logging
    logger = logging.getLogger("git_automation")
    logger.setLevel(logging.DEBUG)
    yield logger


@pytest.fixture
def isolated_environment(tmp_path, monkeypatch):
    """Fixture que fornece ambiente isolado para testes."""
    monkeypatch.chdir(tmp_path)
    return tmp_path

