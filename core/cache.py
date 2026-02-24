"""
Sistema de cache com TTL (Time To Live) para otimizar operações Git.
Reduz chamadas desnecessárias ao repositório.
"""
import time
from typing import Any, Callable, Optional
from functools import wraps


class CacheEntry:
    """Representa um item em cache com controle de expiração."""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.ttl = ttl  # Time To Live em segundos
        self.timestamp = time.time()

    def is_expired(self) -> bool:
        """Verifica se o cache expirou."""
        return time.time() - self.timestamp > self.ttl


class SimpleCache:
    """Cache simples em memória com expiração automática."""

    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> Optional[Any]:
        """Retorna valor do cache se válido."""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                return entry.value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 5):
        """Armazena valor no cache com TTL."""
        self._cache[key] = CacheEntry(value, ttl)

    def clear(self, key: str = None):
        """Limpa cache (específico ou total)."""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()


# Instância global de cache
_cache = SimpleCache()


def cached(ttl: int = 5):
    """
    Decorator para cachear resultado de funções com TTL.

    Uso:
        @cached(ttl=10)
        def list_branches(repo_path):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Criar chave única baseada em função + argumentos
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Tentar recuperar do cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator


def get_cache() -> SimpleCache:
    """Retorna a instância global de cache."""
    return _cache

