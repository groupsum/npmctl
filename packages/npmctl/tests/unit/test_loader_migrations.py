from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from npmctl.errors import MigrationError, ValidationError
from npmctl.loader import load_desired_state
from npmctl.migrations import migrate_document, migrate_path


def test_load_desired_state_full(desired_file: Path) -> None:
    state = load_desired_state(desired_file)
    assert len(state.proxy_hosts) == 1
    assert len(state.certificates) == 1
    assert len(state.access_lists) == 1


def test_load_rejects_missing_schema_header(tmp_path: Path, desired_doc) -> None:
    desired_doc.pop("apiVersion")
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(desired_doc), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_desired_state(path)


def test_load_rejects_unsupported_api_version(tmp_path: Path, desired_doc) -> None:
    desired_doc["apiVersion"] = "npmctl.com/v2"
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(desired_doc), encoding="utf-8")

    with pytest.raises(ValidationError, match="apiVersion"):
        load_desired_state(path)


def test_load_rejects_duplicate_domains(tmp_path: Path, desired_doc) -> None:
    duplicate = dict(desired_doc["proxy_hosts"][0])
    duplicate["meta"] = {"managed_by": "npmctl", "owner": "workload-a", "resource_id": "proxy.dupe"}
    desired_doc["proxy_hosts"].append(duplicate)
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(desired_doc), encoding="utf-8")
    with pytest.raises(ValidationError, match="duplicate proxy host domain"):
        load_desired_state(path)


def test_load_rejects_duplicate_metadata_identities_across_files(tmp_path: Path, desired_doc) -> None:
    first = dict(desired_doc)
    second = {
        "apiVersion": "npmctl.com/v1",
        "schemaVersion": 1,
        "proxy_hosts": [
            {
                "domain_names": ["other.example.com"],
                "forward_host": "other",
                "forward_port": 3000,
                "meta": {"managed_by": "npmctl", "owner": "workload-a", "resource_id": "proxy.app"},
            }
        ],
    }
    (tmp_path / "a.yaml").write_text(yaml.safe_dump(first), encoding="utf-8")
    (tmp_path / "b.yaml").write_text(yaml.safe_dump(second), encoding="utf-8")

    with pytest.raises(ValidationError, match="duplicate meta.resource_id"):
        load_desired_state(tmp_path)


def test_load_discovers_directory_files_in_stable_order(tmp_path: Path) -> None:
    (tmp_path / "nested").mkdir()
    docs = {
        "b.yaml": ("proxy.b", "b.example.com"),
        "a.yaml": ("proxy.a", "a.example.com"),
        "nested/c.yaml": ("proxy.c", "c.example.com"),
    }
    for relative, (resource_id, domain) in docs.items():
        path = tmp_path / relative
        path.write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "npmctl.com/v1",
                    "schemaVersion": 1,
                    "proxy_hosts": [
                        {
                            "domain_names": [domain],
                            "forward_host": "app",
                            "forward_port": 3000,
                            "meta": {"managed_by": "npmctl", "owner": "workload-a", "resource_id": resource_id},
                        }
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    state = load_desired_state(tmp_path)

    assert [Path(path).name for path in state.source_files] == ["a.yaml", "b.yaml", "c.yaml"]
    assert [host.identity.resource_id for host in state.proxy_hosts] == ["proxy.a", "proxy.b", "proxy.c"]


@pytest.mark.parametrize("content", ["[not, an, object]\n", "proxy_hosts: [\n"])
def test_load_rejects_malformed_or_non_object_documents(tmp_path: Path, content: str) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValidationError):
        load_desired_state(path)


def test_migrate_legacy_document_adds_v1_headers() -> None:
    migrated, changed, before = migrate_document({"proxy_hosts": []})
    assert changed is True
    assert before is None
    assert migrated["apiVersion"] == "npmctl.com/v1"
    assert migrated["schemaVersion"] == 1


def test_migrate_path_check_and_write(tmp_path: Path) -> None:
    path = tmp_path / "legacy.yaml"
    path.write_text("proxy_hosts: []\n", encoding="utf-8")
    results = migrate_path(path, write=False)
    assert results[0].changed is True
    assert "apiVersion" not in path.read_text()
    migrate_path(path, write=True)
    assert "apiVersion" in path.read_text()


def test_migrate_rejects_unknown_future_version() -> None:
    with pytest.raises(MigrationError):
        migrate_document({"apiVersion": "npmctl.com/v1", "schemaVersion": 999})
