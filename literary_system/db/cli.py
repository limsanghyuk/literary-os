"""
literary_system/db/cli.py
V582 — LOSDB CLI (argparse 기반)
ADR-041: LOSDB Phase A CLI — status/analyze/migrate/health

G32 준수: print() 사용 금지 → _emit() 래퍼(sys.stdout.write) 사용
--json 플래그는 최상위 파서 인수 (서브커맨드 앞에 위치해야 함)
  예: losdb --json status
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Optional

from .migration_manager import Migration
from .schema_registry import BackendType, SchemaRegistry
from .sql_real_adapter import SQLiteRealAdapter

logger = logging.getLogger(__name__)


# ── G32 준수 출력 헬퍼 ────────────────────────────────────────────────────────

def _emit(msg: str = "") -> None:
    """CLI stdout 출력 헬퍼 — sys.stdout.write 사용 (G32: print() 금지 준수)."""
    sys.stdout.write(str(msg) + "\n")


def _err(msg: str = "") -> None:
    """CLI stderr 출력 헬퍼."""
    sys.stderr.write(str(msg) + "\n")


# ── 파서 구성 ─────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="losdb",
        description="LOSDB — Literary OS Database CLI (V582, ADR-041)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 형태로 출력 (서브커맨드 앞에 위치: losdb --json status)",
    )
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="DB 현재 상태 출력")

    # analyze
    sub.add_parser("analyze", help="SchemaRegistry 상세 분석")

    # health
    sub.add_parser("health", help="어댑터 연결 상태 확인")

    # migrate
    mig = sub.add_parser("migrate", help="마이그레이션 실행 (MOCK 기본)")
    mig.add_argument(
        "target_version",
        nargs="?",
        default="1.0.0",
        help="대상 버전 (기본: 1.0.0)",
    )
    mig.add_argument(
        "--backend",
        default="sql",
        choices=["sql", "graph", "vector"],
        help="마이그레이션 백엔드 (기본: sql)",
    )
    mig.add_argument(
        "--real",
        action="store_true",
        help="REAL 모드 실행 (기본: MOCK)",
    )

    return parser


# ── 서브커맨드 구현 ───────────────────────────────────────────────────────────

def _cmd_status(args: argparse.Namespace) -> int:
    """status: DB 현재 상태"""
    reg = SchemaRegistry.get_instance()
    versions = reg.all_versions()
    history = reg.migration_history()

    data = {
        "command": "status",
        "schema_versions": versions,
        "migration_count": len(history),
        "backends": list(versions.keys()),
    }
    if args.json:
        _emit(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        _emit("=== LOSDB Status ===")
        for backend, info in versions.items():
            _emit(f"  [{backend}] version={info.get('version', '?')} "
                  f"applied_at={info.get('applied_at', '?')}")
        _emit(f"  migration_history: {len(history)}건")
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    """analyze: SchemaRegistry 상세 분석"""
    reg = SchemaRegistry.get_instance()
    versions = reg.all_versions()
    history = reg.migration_history()

    data = {
        "command": "analyze",
        "schema_versions": versions,
        "migration_history": [r.to_dict() for r in history],
        "summary": {
            "total_migrations": len(history),
            "backends_tracked": len(versions),
        },
    }
    if args.json:
        _emit(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        _emit("=== LOSDB Analyze ===")
        _emit(f"  추적 백엔드 수: {len(versions)}")
        _emit(f"  총 마이그레이션: {len(history)}건")
        for backend, info in versions.items():
            _emit(f"  [{backend}] {info}")
    return 0


def _cmd_health(args: argparse.Namespace) -> int:
    """health: 어댑터 연결 상태"""
    adapter = SQLiteRealAdapter(mock=True)
    ok = adapter.check_connection()
    schema = adapter.schema_info()

    data = {
        "command": "health",
        "status": "ok" if ok else "error",
        "adapter": schema,
        "connection": ok,
    }
    if args.json:
        _emit(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        status_str = "OK" if ok else "ERROR"
        _emit(f"=== LOSDB Health: {status_str} ===")
        _emit(f"  adapter: {schema['adapter']} v{schema['version']}")
        _emit(f"  mock: {schema['mock']}")
        _emit(f"  connection: {ok}")
    return 0 if ok else 1


def _cmd_migrate(args: argparse.Namespace) -> int:
    """migrate: 마이그레이션 실행"""
    use_mock = not getattr(args, "real", False)
    adapter = SQLiteRealAdapter(mock=use_mock)

    migration = Migration(
        migration_id=f"CLI_migrate_{args.target_version}",
        backend=BackendType.SQL,
        from_version="0.0.0",
        to_version=args.target_version,
        description=f"CLI 마이그레이션 → {args.target_version}",
        up_script="",
        down_script="",
    )
    ok = adapter.apply(migration)

    data = {
        "command": "migrate",
        "target_version": args.target_version,
        "backend": args.backend,
        "mock": use_mock,
        "success": ok,
        "migration_id": migration.migration_id,
    }
    if args.json:
        _emit(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        result_str = "SUCCESS" if ok else "FAILED"
        _emit(f"=== LOSDB Migrate: {result_str} ===")
        _emit(f"  target_version: {args.target_version}")
        _emit(f"  backend: {args.backend}")
        _emit(f"  mock: {use_mock}")
        _emit(f"  result: {result_str}")
    return 0 if ok else 1


# ── main 진입점 ───────────────────────────────────────────────────────────────

_DISPATCH = {
    "status":  _cmd_status,
    "analyze": _cmd_analyze,
    "health":  _cmd_health,
    "migrate": _cmd_migrate,
}


def main(argv: Optional[list] = None) -> int:
    """LOSDB CLI 메인. 반환값: 0=성공, 1=실패."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    handler = _DISPATCH.get(args.command)
    if handler is None:
        _err(f"알 수 없는 커맨드: {args.command}")
        return 1

    try:
        return handler(args)
    except Exception as exc:
        logger.exception("LOSDB CLI 오류: %s", exc)
        _err(f"오류: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
