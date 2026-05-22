"""LoRADatasetBuilder — CorpusEntry → Alpaca JSONL 변환기.

ADR-056: instruction/input/output + entry_id/content_hash/source_type/license.
DSR 삭제된 항목은 자동 제외.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

ALPACA_INSTRUCTION = (
    "당신은 한국 드라마 작법 전문가입니다. "
    "주어진 장르·작품 정보를 바탕으로 고품질 씬을 작성하세요."
)
ALPACA_INPUT_TEMPLATE = "장르: {genre} | 작품: {title}\n\n{text}"


@dataclass
class LoRASample:
    """Alpaca 형식의 단일 LoRA 학습 샘플."""

    instruction: str
    input: str
    output: str
    entry_id: str
    content_hash: str
    source_type: str
    license: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LoRADatasetBuilder:
    """CorpusEntry 리스트를 LoRASample 리스트로 변환.

    Usage:
        builder = LoRADatasetBuilder()
        samples = builder.build(entries)
        builder.save(samples, Path("train.jsonl"))
    """

    def __init__(self, dsr_deleted_ids: Optional[Set[str]] = None) -> None:
        self._dsr_deleted: Set[str] = dsr_deleted_ids or set()

    def build(self, entries: List[Any]) -> List[LoRASample]:
        """entries → LoRASample 리스트. DSR 삭제 항목 제외."""
        samples: List[LoRASample] = []
        for entry in entries:
            eid = getattr(entry, "entry_id", None) or (entry.get("entry_id", "") if hasattr(entry, "get") else "")
            if eid in self._dsr_deleted:
                continue
            text = getattr(entry, "text", None) or (entry.get("text", "") if hasattr(entry, "get") else "")
            genre = getattr(entry, "genre", None) or (entry.get("genre", "drama") if hasattr(entry, "get") else "drama")
            title = getattr(entry, "source_title", None) or getattr(entry, "title", None) or (entry.get("title", "unknown") if hasattr(entry, "get") else "unknown")
            source_type = (
                getattr(entry, "source_type", None) or (entry.get("source_type", "synthetic") if hasattr(entry, "get") else "synthetic")
            )
            license_val = (
                getattr(entry, "license", None) or (entry.get("license", "CC-BY-4.0") if hasattr(entry, "get") else "CC-BY-4.0")
            )
            content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
            sample = LoRASample(
                instruction=ALPACA_INSTRUCTION,
                input=ALPACA_INPUT_TEMPLATE.format(
                    genre=genre, title=title, text=text[:512]
                ),
                output=text,
                entry_id=eid,
                content_hash=content_hash,
                source_type=source_type,
                license=license_val,
            )
            samples.append(sample)
        return samples

    @staticmethod
    def save(samples: List[LoRASample], path: Path) -> None:
        """JSONL 파일로 저장."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for s in samples:
                fh.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")

    @staticmethod
    def load(path: Path) -> List[LoRASample]:
        """JSONL 파일에서 로드."""
        path = Path(path)
        samples: List[LoRASample] = []
        if not path.exists():
            return samples
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                samples.append(LoRASample(**data))
        return samples
