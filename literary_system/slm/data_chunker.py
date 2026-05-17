"""V328 Task16: DataChunker — TraceDatasetStore → SLMDatasetBuilder 파이프라인 (단절 H)."""
from __future__ import annotations
from typing import Iterator, Any
import json, os

class DataChunker:
    def __init__(self, chunk_size: int = 50):
        self.chunk_size = chunk_size

    def iter_chunks(self, jsonl_path: str) -> list[list[dict]]:
        rows: list[dict] = []
        try:
            with open(jsonl_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
        except Exception:
            pass
        if not rows:
            return []
        return [rows[i:i+self.chunk_size]
                for i in range(0, len(rows), self.chunk_size)]

    def run_pipeline(self, trace_store, slm_builder, export_path: str) -> dict:
        pairs_total = 0
        chunks_processed = 0
        try:
            jsonl_path = export_path
            if hasattr(trace_store, "export_slm_dataset"):
                trace_store.export_slm_dataset(jsonl_path)
            for chunk in self.iter_chunks(jsonl_path):
                if hasattr(slm_builder, "add_batch"):
                    slm_builder.add_batch(chunk)
                elif hasattr(slm_builder, "add"):
                    for row in chunk:
                        slm_builder.add(row)
                pairs_total += len(chunk)
                chunks_processed += 1
        except Exception:
            pass
        return {"chunks_processed": chunks_processed, "pairs_total": pairs_total}
