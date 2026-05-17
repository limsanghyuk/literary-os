from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from literary_system.adapters.creative_project_adapter import CreativeProjectAdapter
from literary_system.analyzer.orchestrator import StandardLiteraryAnalyzer
from literary_system.librarian.orchestrator import ChiefLibrarian


class CreativeProjectPipeline:
    def __init__(self, out_root: str | Path, *, spec_path: str | Path | None = None) -> None:
        self.out_root = Path(out_root)
        self.spec_path = spec_path
        self.analyzer = StandardLiteraryAnalyzer()
        self.librarian = ChiefLibrarian(out_root=self.out_root)

    def run(self, package_root: str | Path) -> dict[str, Any]:
        adapter = CreativeProjectAdapter(package_root, spec_path=self.spec_path)
        inputs, context, diagnostics = adapter.load()
        bundle = self.analyzer.analyze(inputs, context)
        report = self.librarian.ingest(bundle)
        self.out_root.mkdir(parents=True, exist_ok=True)
        (self.out_root / 'adapter_diagnostics.json').write_text(
            json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding='utf-8'
        )
        (self.out_root / 'bundle.json').write_text(
            json.dumps(bundle, ensure_ascii=False, indent=2), encoding='utf-8'
        )
        (self.out_root / 'report.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8'
        )
        return {
            'diagnostics': diagnostics,
            'bundle': bundle,
            'report': report,
        }
