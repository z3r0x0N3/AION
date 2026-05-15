from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class CredentialProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None:
        ...

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        ...

    @abstractmethod
    def list_keys(self) -> list[str]:
        ...


class EnvCredentialProvider(CredentialProvider):
    PREFIX = "AION_CRED_"

    def get(self, key: str) -> str | None:
        return os.environ.get(f"{self.PREFIX}{key.upper()}")

    def set(self, key: str, value: str) -> None:
        os.environ[f"{self.PREFIX}{key.upper()}"] = value

    def delete(self, key: str) -> bool:
        var = f"{self.PREFIX}{key.upper()}"
        if var in os.environ:
            del os.environ[var]
            return True
        return False

    def list_keys(self) -> list[str]:
        prefix = self.PREFIX
        return [k[len(prefix):].lower() for k in os.environ if k.startswith(prefix)]


class FileCredentialProvider(CredentialProvider):
    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else Path.home() / ".aion" / "credentials.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text())
            except (json.JSONDecodeError, ValueError):
                self._data = {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._data, indent=2))

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value
        self._save()

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False

    def list_keys(self) -> list[str]:
        return list(self._data.keys())


class KeyringCredentialProvider(CredentialProvider):
    SERVICE = "aion"

    def get(self, key: str) -> str | None:
        try:
            import keyring
            return keyring.get_password(self.SERVICE, key)
        except ImportError:
            return None

    def set(self, key: str, value: str) -> None:
        try:
            import keyring
            keyring.set_password(self.SERVICE, key, value)
        except ImportError:
            pass

    def delete(self, key: str) -> bool:
        try:
            import keyring
            keyring.delete_password(self.SERVICE, key)
            return True
        except ImportError:
            return False
        except keyring.errors.PasswordDeleteError:
            return False

    def list_keys(self) -> list[str]:
        return []


class CredentialManager:
    def __init__(self) -> None:
        self._providers: dict[str, CredentialProvider] = {
            "env": EnvCredentialProvider(),
            "file": FileCredentialProvider(),
        }
        self._active: str = "file"
        try:
            import keyring
            self._providers["keyring"] = KeyringCredentialProvider()
            self._active = "keyring"
        except ImportError:
            pass

    @property
    def active_provider(self) -> str:
        return self._active

    def set_active(self, name: str) -> bool:
        if name in self._providers:
            self._active = name
            return True
        return False

    def provider(self, name: str | None = None) -> CredentialProvider:
        return self._providers[name or self._active]

    def get(self, key: str, provider_name: str | None = None) -> str | None:
        return self.provider(provider_name).get(key)

    def set(self, key: str, value: str, provider_name: str | None = None) -> None:
        self.provider(provider_name).set(key, value)

    def delete(self, key: str, provider_name: str | None = None) -> bool:
        return self.provider(provider_name).delete(key)

    def list_keys(self, provider_name: str | None = None) -> list[str]:
        return self.provider(provider_name).list_keys()

    @property
    def available_providers(self) -> list[str]:
        return list(self._providers.keys())
