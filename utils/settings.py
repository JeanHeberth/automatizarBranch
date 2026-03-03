from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional


def _get_settings_path() -> Path:
    """Retorna o caminho do arquivo de configurações do usuário.

    Arquivo localizado em: ~/.automatizarbranch/settings.json
    """
    home = Path.home()
    cfg_dir = home / ".automatizarbranch"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "settings.json"


def load_settings() -> Dict[str, Any]:
    path = _get_settings_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Se arquivo estiver corrompido, ignorar e retornar vazio
        return {}


def save_settings(settings: Dict[str, Any]) -> None:
    path = _get_settings_path()
    with path.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def get_theme(default: str = "system") -> str:
    settings = load_settings()
    theme = settings.get("theme")
    if theme in {"dark", "light", "system"}:
        return theme
    return default


def set_theme(value: str) -> None:
    if value not in {"dark", "light", "system"}:
        return
    settings = load_settings()
    settings["theme"] = value
    save_settings(settings)


def get_protected_branches(default: Optional[list] = None) -> list:
    """Retorna a lista de branches protegidas do arquivo de configuração do usuário."""
    if default is None:
        default = ["main", "master", "develop"]
    settings = load_settings()
    pb = settings.get("protected_branches")
    if isinstance(pb, list) and pb:
        return pb
    return default


def set_protected_branches(branches: list) -> None:
    """Define a lista de branches protegidas no arquivo de configurações."""
    settings = load_settings()
    settings["protected_branches"] = branches
    save_settings(settings)


def get_default_strategy(default: str = "rebase") -> str:
    settings = load_settings()
    s = settings.get("default_strategy")
    if s in {"rebase", "merge"}:
        return s
    return default


def set_default_strategy(value: str) -> None:
    if value not in {"rebase", "merge"}:
        return
    settings = load_settings()
    settings["default_strategy"] = value
    save_settings(settings)
