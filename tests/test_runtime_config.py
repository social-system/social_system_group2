import importlib

from app.db.session import Base
from app.db.session import get_engine_kwargs, normalize_database_url
from app.main import parse_cors_allow_origins


def test_normalize_database_url_converts_render_postgres_scheme():
    assert (
        normalize_database_url("postgres://user:pass@example.com:5432/db")
        == "postgresql+psycopg://user:pass@example.com:5432/db"
    )


def test_normalize_database_url_converts_postgresql_scheme():
    assert (
        normalize_database_url("postgresql://user:pass@example.com:5432/db")
        == "postgresql+psycopg://user:pass@example.com:5432/db"
    )


def test_normalize_database_url_keeps_psycopg_scheme():
    url = "postgresql+psycopg://user:pass@example.com:5432/db"
    assert normalize_database_url(url) == url


def test_normalize_database_url_keeps_sqlite_scheme():
    assert normalize_database_url("sqlite:///./receipts.db") == "sqlite:///./receipts.db"


def test_get_engine_kwargs_uses_sqlite_connect_args_only_for_sqlite():
    sqlite_kwargs = get_engine_kwargs("sqlite:///./receipts.db")
    postgres_kwargs = get_engine_kwargs("postgresql+psycopg://user:pass@example.com/db")

    assert sqlite_kwargs["pool_pre_ping"] is True
    assert sqlite_kwargs["connect_args"] == {"check_same_thread": False}
    assert postgres_kwargs == {"pool_pre_ping": True}


def test_parse_cors_allow_origins_defaults_to_localhost():
    assert parse_cors_allow_origins(None) == ["http://localhost:5173"]
    assert parse_cors_allow_origins(" , ") == ["http://localhost:5173"]


def test_parse_cors_allow_origins_splits_and_trims_values():
    assert parse_cors_allow_origins(
        " https://frontend.example.com, https://another.example.com, "
    ) == ["https://frontend.example.com", "https://another.example.com"]


def test_parse_cors_allow_origins_rejects_wildcard():
    try:
        parse_cors_allow_origins("*")
    except ValueError as exc:
        assert "must not contain '*'" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_importing_main_does_not_create_tables(monkeypatch):
    def fail_create_all(*args, **kwargs):
        raise AssertionError("app.main import must not create tables")

    monkeypatch.setattr(Base.metadata, "create_all", fail_create_all)

    import app.main as main_module

    importlib.reload(main_module)
