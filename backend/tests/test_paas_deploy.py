"""PaaS one-click deploy (all-in-one image): secret key handling, admin bootstrap, the built UI on the API origin."""
import logging
import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.error_handlers import register_error_handlers
from app.api.static import mount_frontend
from app.core import config, crypto, security
from app.models.database import Database
from app.repositories import UserRepository
from app.services import seed


def test_secret_key_accepts_fernet_and_platform_values():
    k = Fernet.generate_key().decode()
    assert crypto.as_fernet_key(k) == k.encode()
    for raw in ("a" * 64, "c2VjcmV0", "x"):  # Heroku hex secret, short base64, anything
        Fernet(crypto.as_fernet_key(raw))  # a valid key, stable for the same input
        assert crypto.as_fernet_key(raw) == crypto.as_fernet_key(raw)


def test_production_requires_secret_key(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "IS_PROD", True); monkeypatch.delenv("STUDIO_SECRET_KEY", raising=False)
    monkeypatch.setenv("STUDIO_SECRET_KEY_FILE", str(tmp_path / "secret.key"))
    with pytest.raises(RuntimeError, match="STUDIO_SECRET_KEY"): crypto.check_key()
    (tmp_path / "secret.key").write_bytes(Fernet.generate_key()); crypto.check_key()  # an existing key file keeps working
    monkeypatch.setenv("STUDIO_SECRET_KEY_FILE", str(tmp_path / "none.key")); monkeypatch.setenv("STUDIO_SECRET_KEY", "x" * 64)
    crypto.check_key()


def test_production_bootstraps_admin_with_generated_password(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(config, "IS_PROD", True); monkeypatch.delenv("STUDIO_ADMIN_PASSWORD", raising=False)
    monkeypatch.setenv("STUDIO_ADMIN_EMAILS", "owner@example.com")
    d = Database(f"sqlite:///{tmp_path}/p.db"); users = UserRepository(d)
    with caplog.at_level(logging.WARNING): seed.bootstrap(d)
    assert users.get_by_email(config.DEMO_EMAIL) is None  # no demo account in production
    u = users.get_by_email("owner@example.com"); assert u.role == "admin" and u.active
    pw = caplog.text.split("change it now): ")[1].split()[0]
    assert security.verify_password(pw, u.password)
    caplog.clear(); seed.bootstrap(d)
    assert "one-time password" not in caplog.text  # only on the first start


def test_admin_password_from_env(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "IS_PROD", True); monkeypatch.setenv("STUDIO_ADMIN_EMAILS", "owner@example.com")
    monkeypatch.setenv("STUDIO_ADMIN_PASSWORD", "weak")
    d = Database(f"sqlite:///{tmp_path}/w.db")
    with pytest.raises(RuntimeError, match="AUTH_PASSWORD"): seed.bootstrap(d)
    monkeypatch.setenv("STUDIO_ADMIN_PASSWORD", "Correct-horse-42")
    d = Database(f"sqlite:///{tmp_path}/e.db"); seed.bootstrap(d)
    assert security.verify_password("Correct-horse-42", UserRepository(d).get_by_email("owner@example.com").password)


def test_postgres_urls_are_normalised():
    assert config.normalise_db_url("postgres://u:p@h:5432/d") == "postgresql+psycopg://u:p@h:5432/d"
    assert config.normalise_db_url("postgresql://u:p@h/d") == "postgresql+psycopg://u:p@h/d"
    assert config.normalise_db_url("sqlite:////data/studio.db") == "sqlite:////data/studio.db"


def test_frontend_served_with_spa_fallback(tmp_path):
    (tmp_path / "index.html").write_text("<div id=root></div>"); (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    app = FastAPI(); register_error_handlers(app)
    app.get("/api/health")(lambda: {"ok": True})
    mount_frontend(app, str(tmp_path)); c = TestClient(app)
    assert c.get("/api/health").json() == {"ok": True}
    assert c.get("/").text == "<div id=root></div>" and c.get("/workflows/abc").text == "<div id=root></div>"
    assert c.get("/assets/app.js").text == "console.log(1)"
    r = c.get("/api/nope"); assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_frontend_mount_is_off_without_a_build(tmp_path):
    app = FastAPI(); mount_frontend(app, str(tmp_path)); mount_frontend(app, "")
    assert not any(getattr(r, "name", "") == "frontend" for r in app.routes)
