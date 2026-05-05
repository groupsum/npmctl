from __future__ import annotations

import json
from pathlib import Path

import pytest

from npmctl.cli import (
    EXIT_API,
    EXIT_CAPABILITY,
    EXIT_CONFLICT,
    EXIT_OK,
    EXIT_USAGE_OR_VALIDATION,
    main,
)
from npmctl.errors import ApiError


def test_validate_command_text_and_json_output(desired_file: Path, capsys) -> None:
    assert main(["validate", str(desired_file)]) == EXIT_OK
    text = capsys.readouterr().out
    assert "desired state valid" in text
    assert "proxy hosts: 1" in text

    assert main(["--output", "json", "validate", str(desired_file)]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["proxy_hosts"] == 1
    assert payload["certificates"] == 1
    assert payload["access_lists"] == 1


def test_schema_command_outputs_capabilities_json(tmp_path: Path, capsys) -> None:
    schema = {
        "openapi": "3.0.0",
        "paths": {
            "/nginx/proxy-hosts": {"get": {}, "post": {}},
            "/nginx/proxy-hosts/{id}": {"put": {}, "delete": {}},
        },
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")

    assert main(["--output", "json", "schema", "capabilities", "--schema", str(schema_path)]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["proxy_hosts"]["create"] is True
    assert payload["proxy_hosts"]["delete"] is True
    assert payload["certificates"]["list"] is False


def test_missing_api_arguments_exit_with_usage_error(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["health"])

    assert exc_info.value.code == EXIT_USAGE_OR_VALIDATION
    assert "--base-url, --identity, and --secret are required" in capsys.readouterr().err


def test_bad_command_line_option_combination_is_rejected(tmp_path: Path, capsys) -> None:
    path = tmp_path / "legacy.yaml"
    path.write_text("proxy_hosts: []\n", encoding="utf-8")

    assert main(["migrate", str(path), "--write", "--check"]) == EXIT_USAGE_OR_VALIDATION

    assert "cannot be combined" in capsys.readouterr().err


def test_json_error_output_shape_for_validation_errors(tmp_path: Path, capsys) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("apiVersion: wrong\nschemaVersion: 1\n", encoding="utf-8")

    assert main(["--output", "json", "validate", str(path)]) == EXIT_USAGE_OR_VALIDATION
    payload = json.loads(capsys.readouterr().err)
    assert payload == {
        "ok": False,
        "error": {
            "code": "validation_error",
            "message": f"{path}.apiVersion must be 'npmctl.io/v1'; run npmctl migrate if needed",
        },
    }


def test_cli_redacts_secret_in_api_errors(monkeypatch, capsys) -> None:
    class FailingClient:
        def __init__(self, *, base_url: str, identity: str, secret: str, timeout_s: float) -> None:
            self.secret = secret

        def health(self):
            raise ApiError(f"backend echoed secret {self.secret}")

    monkeypatch.setattr("npmctl.cli.NpmClient", FailingClient)

    assert (
        main(
            [
                "--base-url",
                "http://npm.test/api",
                "--identity",
                "admin@example.com",
                "--secret",
                "supersecret",
                "health",
            ]
        )
        == EXIT_API
    )

    err = capsys.readouterr().err
    assert "supersecret" not in err
    assert "***" in err


def test_exit_code_mapping_for_conflict_api_capability_and_migration_errors(
    fake_npm_server, desired_file: Path, tmp_path: Path, capsys
) -> None:
    state, base_url = fake_npm_server
    state.create(
        "proxy_hosts",
        {
            "domain_names": ["app.example.com"],
            "forward_host": "app",
            "forward_port": 3000,
            "forward_scheme": "http",
            "access_list_id": 0,
            "certificate_id": 0,
            "ssl_forced": 1,
            "caching_enabled": 0,
            "block_exploits": 1,
            "advanced_config": "",
            "meta": {},
            "allow_websocket_upgrade": 1,
            "http2_support": 1,
            "enabled": 1,
            "locations": [],
            "hsts_enabled": 0,
            "hsts_subdomains": 0,
        },
    )
    common = ["--base-url", base_url, "--identity", "admin@example.com", "--secret", "changeme"]
    assert main([*common, "plan", str(desired_file)]) == EXIT_CONFLICT

    missing_caps = tmp_path / "missing-caps.json"
    missing_caps.write_text(json.dumps({"openapi": "3.0.0", "paths": {}}), encoding="utf-8")
    assert main(["schema", "check", "--schema", str(missing_caps)]) == EXIT_CAPABILITY

    future = tmp_path / "future.yaml"
    future.write_text("apiVersion: npmctl.io/v1\nschemaVersion: 999\n", encoding="utf-8")
    assert main(["migrate", str(future)]) == EXIT_USAGE_OR_VALIDATION

    class FailingClient:
        def __init__(self, **_: object) -> None:
            pass

        def health(self):
            raise ApiError("backend failed")

    from npmctl import cli

    original_client = cli.NpmClient
    try:
        cli.NpmClient = FailingClient
        assert main([*common, "health"]) == EXIT_API
    finally:
        cli.NpmClient = original_client

    capsys.readouterr()
