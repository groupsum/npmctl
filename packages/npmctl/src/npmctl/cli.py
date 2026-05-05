"""Command-line interface for npmctl."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Sequence

from npmctl import __version__
from npmctl.apply import ApplyEngine
from npmctl.client import NpmClient
from npmctl.errors import ApiError, CapabilityError, ConflictError, MigrationError, NpmctlError, ValidationError
from npmctl.loader import load_desired_state
from npmctl.migrations import migrate_path
from npmctl.output import format_plan_text, write_error, write_output
from npmctl.planner import PlannerOptions, compute_plan
from npmctl.schema import Capabilities, load_openapi_schema

EXIT_OK = 0
EXIT_CONFLICT = 1
EXIT_USAGE_OR_VALIDATION = 2
EXIT_API = 3
EXIT_CAPABILITY = 4


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(
        prog="npmctl",
        description="Owner-scoped plan/apply/adopt controller for Nginx Proxy Manager resources.",
    )
    parser.add_argument("--version", action="version", version=f"npmctl {__version__}")
    parser.add_argument("--base-url", default=os.getenv("NPM_BASE_URL"), help="NPM API URL, e.g. http://host:81/api")
    parser.add_argument("--identity", default=os.getenv("NPM_IDENTITY"), help="NPM login identity")
    parser.add_argument("--secret", default=os.getenv("NPM_SECRET"), help="NPM login secret")
    parser.add_argument(
        "--timeout", default=float(os.getenv("NPM_TIMEOUT_S", "15")), type=float, help="HTTP timeout seconds"
    )
    parser.add_argument("--output", choices=("text", "json"), default="text", help="Output format")

    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate desired state")
    validate.add_argument("desired_state")

    migrate = sub.add_parser("migrate", help="Migrate desired-state schema")
    migrate.add_argument("path")
    migrate.add_argument("--write", action="store_true", help="Write migrated files")
    migrate.add_argument("--check", action="store_true", help="Fail if migration is needed")

    health = sub.add_parser("health", help="Call NPM API health endpoint")
    health.set_defaults(needs_api=True)

    schema = sub.add_parser("schema", help="OpenAPI schema commands")
    schema_sub = schema.add_subparsers(dest="schema_command", required=True)
    fetch = schema_sub.add_parser("fetch", help="Fetch /schema from NPM")
    fetch.add_argument("--write", help="Write schema JSON to path")
    fetch.set_defaults(needs_api=True)
    caps = schema_sub.add_parser("capabilities", help="Show detected endpoint capabilities")
    caps.add_argument("--schema", help="Schema JSON path; fetches from NPM when omitted")
    caps.set_defaults(needs_api_optional_schema=True)
    check = schema_sub.add_parser("check", help="Validate required endpoint capabilities")
    check.add_argument("--schema", help="Schema JSON path; fetches from NPM when omitted")
    check.set_defaults(needs_api_optional_schema=True)

    plan = sub.add_parser("plan", help="Compute owner-scoped CRUD plan")
    _add_reconcile_args(plan)
    plan.set_defaults(needs_api=True)

    apply = sub.add_parser("apply", help="Apply a clean owner-scoped CRUD plan")
    _add_reconcile_args(apply)
    apply.add_argument("--dry-run", action="store_true", help="Plan but do not mutate NPM")
    apply.set_defaults(needs_api=True)

    adopt = sub.add_parser("adopt", help="Adopt unmanaged matching resources by writing metadata")
    _add_reconcile_args(adopt)
    adopt.add_argument("--allow-field-drift", action="store_true", help="Allow adopting resources whose fields differ")
    adopt.add_argument("--force", action="store_true", help="Alias for --allow-field-drift with explicit intent")
    adopt.set_defaults(needs_api=True, adopt=True)

    return parser


def _add_reconcile_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("desired_state")
    parser.add_argument("--owner", help="Limit operation to one owner scope")
    parser.add_argument("--no-updates", action="store_true", help="Conflict on owned drift instead of updating")
    parser.add_argument("--prune-owned", action="store_true", help="Delete owned resources absent from desired state")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _dispatch(args, parser)
    except ValidationError as exc:
        write_error(args.output, "validation_error", str(exc))
        return EXIT_USAGE_OR_VALIDATION
    except MigrationError as exc:
        write_error(args.output, "migration_error", str(exc))
        return EXIT_USAGE_OR_VALIDATION
    except ConflictError as exc:
        write_error(args.output, "conflict_error", str(exc))
        return EXIT_CONFLICT
    except CapabilityError as exc:
        write_error(args.output, "capability_error", str(exc))
        return EXIT_CAPABILITY
    except ApiError as exc:
        write_error(args.output, "api_error", str(exc))
        return EXIT_API
    except NpmctlError as exc:
        write_error(args.output, "npmctl_error", str(exc))
        return EXIT_USAGE_OR_VALIDATION


def _dispatch(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if args.command == "validate":
        desired = load_desired_state(args.desired_state)
        payload = _desired_summary(desired)
        write_output(args.output, payload, _format_validate_text(payload))
        return EXIT_OK

    if args.command == "migrate":
        results = migrate_path(args.path, write=args.write)
        changed = [result for result in results if result.changed]
        payload = {
            "ok": not bool(changed and args.check),
            "changed": len(changed),
            "files": [str(result.path) for result in changed],
            "written": bool(args.write),
        }
        write_output(args.output, payload, f"migrations needed: {len(changed)}\nwritten: {str(args.write).lower()}")
        return EXIT_USAGE_OR_VALIDATION if changed and args.check else EXIT_OK

    client: NpmClient | None = None
    if getattr(args, "needs_api", False) or (
        getattr(args, "needs_api_optional_schema", False) and not getattr(args, "schema", None)
    ):
        _require_api_args(args, parser)
        client = NpmClient(base_url=args.base_url, identity=args.identity, secret=args.secret, timeout_s=args.timeout)

    if args.command == "health":
        assert client is not None
        payload = client.health()
        write_output(args.output, payload, json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK

    if args.command == "schema":
        return _schema_command(args, client)

    if args.command in {"plan", "apply", "adopt"}:
        assert client is not None
        desired = load_desired_state(args.desired_state)
        capabilities = client.capabilities()
        existing = client.existing_state(
            include_certificates=capabilities.certificates.list,
            include_access_lists=capabilities.access_lists.list,
        )
        options = PlannerOptions(
            owner=args.owner,
            allow_updates=not args.no_updates,
            prune_owned=args.prune_owned,
            adopt=args.command == "adopt",
            strict_adopt=not (getattr(args, "allow_field_drift", False) or getattr(args, "force", False)),
            allow_field_drift=getattr(args, "allow_field_drift", False) or getattr(args, "force", False),
        )
        plan = compute_plan(desired=desired, existing=existing, capabilities=capabilities, options=options)
        if args.command == "plan" or getattr(args, "dry_run", False):
            write_output(args.output, plan.to_dict(), format_plan_text(plan))
            return EXIT_OK if plan.ok else EXIT_CONFLICT
        if not plan.ok:
            write_output(args.output, plan.to_dict(), format_plan_text(plan))
            return EXIT_CONFLICT
        result = ApplyEngine(client=client, capabilities=capabilities).apply(plan)
        payload = plan.to_dict() | {"apply": result.to_dict()}
        text = format_plan_text(plan) + f"\napplied: true\nmutations: {len(result.mutations)}"
        write_output(args.output, payload, text)
        return EXIT_OK

    parser.error(f"unsupported command: {args.command}")
    return EXIT_USAGE_OR_VALIDATION


def _schema_command(args: argparse.Namespace, client: NpmClient | None) -> int:
    if args.schema_command == "fetch":
        assert client is not None
        payload = client.openapi_schema()
        if args.write:
            Path(args.write).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_output(args.output, payload, json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK
    schema_doc = load_openapi_schema(args.schema) if args.schema else client.openapi_schema()  # type: ignore[union-attr]
    capabilities = Capabilities.from_openapi(schema_doc)
    payload = capabilities.to_dict()
    if args.schema_command == "check":
        required = [
            capabilities.proxy_hosts.list,
            capabilities.proxy_hosts.create,
            capabilities.proxy_hosts.update,
            capabilities.proxy_hosts.delete,
        ]
        payload["ok"] = all(required)
        write_output(args.output, payload, json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK if payload["ok"] else EXIT_CAPABILITY
    write_output(args.output, payload, json.dumps(payload, indent=2, sort_keys=True))
    return EXIT_OK


def _require_api_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if not (args.base_url and args.identity and args.secret):
        parser.error("--base-url, --identity, and --secret are required, or set NPM_BASE_URL/NPM_IDENTITY/NPM_SECRET")


def _desired_summary(desired: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "schemaVersion": desired.schema_version,
        "proxy_hosts": len(desired.proxy_hosts),
        "certificates": len(desired.certificates),
        "access_lists": len(desired.access_lists),
        "source_files": list(desired.source_files),
    }


def _format_validate_text(payload: dict[str, Any]) -> str:
    return (
        "desired state valid\n"
        f"proxy hosts: {payload['proxy_hosts']}\n"
        f"certificates: {payload['certificates']}\n"
        f"access lists: {payload['access_lists']}"
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
