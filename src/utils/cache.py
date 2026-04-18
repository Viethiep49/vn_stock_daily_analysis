"""
cache.py — Caching system cho data provider và LLM responses
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional, Callable
from functools import wraps
import sqlite3
from contextlib import contextmanager


class CacheConfig:
    """Cấu hình cache"""
    CACHE_DIR = Path(".cache")
    DB_PATH = CACHE_DIR / "cache.db"

    TTL = {
        'historical_data': 3600,
        'realtime_quote': 300,
        'financial_report': 86400,
        'llm_response': 7200,
        'news_sentiment': 1800,
    }

    MAX_CACHE_SIZE_MB = 500


class LocalCache:
    """SQLite-based local cache với LRU eviction"""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.config.CACHE_DIR.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    ttl INTEGER NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL NOT NULL
                )
            ''')
            conn.execute(
                'CREATE INDEX IF NOT EXISTS idx_created ON cache_entries(created_at)')

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.config.DB_PATH))
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        # Avoid caching raw pandas DataFrame objects directly inside kwargs.
        # Typically we just use symbol and basic args.
        raw = f"{prefix}:{args}:{sorted([(k,v) for k,v in kwargs.items() if not k.startswith('_')])}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, prefix: str, *args, **kwargs) -> Optional[Any]:
        key = self._generate_key(prefix, *args, **kwargs)

        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT value, created_at, ttl FROM cache_entries WHERE key = ?', (key,))
            row = cursor.fetchone()

            if not row:
                return None

            value, created_at, ttl = row
            if time.time() - created_at > ttl:
                self.delete(key)
                return None

            conn.execute(
                'UPDATE cache_entries SET access_count = access_count + 1, last_accessed = ? WHERE key = ?',
                (time.time(), key)
            )

            return json.loads(value)

    def set(
            self,
            prefix: str,
            value: Any,
            ttl: Optional[int] = None,
            *args,
            **kwargs):
        key = self._generate_key(prefix, *args, **kwargs)
        ttl = ttl or self.config.TTL.get(prefix, 3600)

        with self._get_connection() as conn:
            # use INSERT OR REPLACE because we are in sqlite
            conn.execute('''INSERT OR REPLACE INTO cache_entries
                   (key, value, created_at, ttl, last_accessed)
                   VALUES (?, ?, ?, ?, ?)''', (key, json.dumps(
                value, default=str), time.time(), ttl, time.time()))

    def delete(self, key: str):
        with self._get_connection() as conn:
            conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))

# Decorator để cache function calls


def cached(prefix: str, ttl: Optional[int] = None):
    def decorator(func: Callable):
        cache = LocalCache()

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip first argument if it's 'self'
            cache_args = args[1:] if args and hasattr(
                args[0], '__class__') else args
            result = cache.get(prefix, func.__name__, *cache_args, **kwargs)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            # Serialize before caching, handle pandas Dataframes if needed but normally we cache dicts or strings
            # In data_provider, it returns DataFrame, so we might need a custom
            # serializer or serialize to json dict
            if hasattr(result, 'to_dict'):
                dict_result = result.to_dict(orient='records')
                cache.set(prefix,
                          {'__is_dataframe': True,
                           'data': dict_result},
                          ttl,
                          func.__name__,
                          *cache_args,
                          **kwargs)
            else:
                cache.set(
                    prefix,
                    result,
                    ttl,
                    func.__name__,
                    *cache_args,
                    **kwargs)
            return result
        return wrapper
    return decorator
