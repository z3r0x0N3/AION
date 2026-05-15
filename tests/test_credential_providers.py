import tempfile
from pathlib import Path

from aion.credential_providers import (
    CredentialManager, EnvCredentialProvider, FileCredentialProvider,
    KeyringCredentialProvider,
)


class TestEnvCredentialProvider:
    def test_set_get(self):
        provider = EnvCredentialProvider()
        provider.set("test_key", "test_value")
        assert provider.get("test_key") == "test_value"
        provider.delete("test_key")
        assert provider.get("test_key") is None


class TestFileCredentialProvider:
    def test_set_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "creds.json"
            provider = FileCredentialProvider(path)
            provider.set("api_key", "secret123")
            assert provider.get("api_key") == "secret123"

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "creds.json"
            provider = FileCredentialProvider(path)
            provider.set("key", "val")
            provider2 = FileCredentialProvider(path)
            assert provider2.get("key") == "val"

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = FileCredentialProvider(Path(tmpdir) / "c.json")
            provider.set("k", "v")
            assert provider.delete("k") is True
            assert provider.delete("k") is False

    def test_list_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = FileCredentialProvider(Path(tmpdir) / "c.json")
            provider.set("a", "1")
            provider.set("b", "2")
            keys = provider.list_keys()
            assert "a" in keys
            assert "b" in keys


class TestCredentialManager:
    def test_get_set(self):
        mgr = CredentialManager()
        mgr.set("test_cred", "value123", "file")
        assert mgr.get("test_cred", "file") == "value123"

    def test_available_providers(self):
        mgr = CredentialManager()
        assert "env" in mgr.available_providers
        assert "file" in mgr.available_providers

    def test_set_active(self):
        mgr = CredentialManager()
        assert mgr.set_active("env") is True
        assert mgr.active_provider == "env"
        assert mgr.set_active("nonexistent") is False
