"""
V546 — ADRIndexGenerator
P7(ADR 목록 수동 관리 오버헤드) 해소.

literary_system/docs/adr/ 디렉토리에서 ADR-*.md 파일을 스캔하여
INDEX.md (표 형식) 및 graph.mermaid (의존 그래프)를 자동 생성한다.
LLM-0 정책 준수: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

ADR_FILENAME_RE = re.compile(r"ADR-(\d+)[_-](.+)\.md$", re.IGNORECASE)
ADR_SUPERSEDES_RE = re.compile(r"Supersedes:\s*(ADR-\d+)", re.IGNORECASE)
ADR_STATUS_RE = re.compile(r"Status:\s*(Accepted|Proposed|Deprecated|Superseded)",
                            re.IGNORECASE)
ADR_TITLE_RE = re.compile(r"^#\s+ADR-\d+[:\s]+(.+)$", re.MULTILINE)


@dataclass
class ADREntry:
    number: int
    slug: str
    title: str
    status: str = "Accepted"
    supersedes: List[str] = field(default_factory=list)
    filename: str = ""

    @property
    def adr_id(self) -> str:
        return f"ADR-{self.number:03d}"


class ADRIndexGenerator:
    """
    ADR 디렉토리 스캔 → INDEX.md + graph.mermaid 자동 생성. (P7 해소)
    """

    def __init__(self, adr_dir: str | Path | None = None,
                 output_dir: str | Path | None = None) -> None:
        if adr_dir is None:
            # 기본 경로: literary_system/docs/adr/
            base = Path(__file__).parent.parent.parent
            adr_dir = base / "docs" / "adr"
        self._adr_dir = Path(adr_dir)
        self._output_dir = Path(output_dir) if output_dir else self._adr_dir

    def scan(self) -> List[ADREntry]:
        """ADR 디렉토리를 스캔하여 ADREntry 목록 반환."""
        entries: List[ADREntry] = []
        if not self._adr_dir.exists():
            logger.warning("ADR 디렉토리 없음: %s", self._adr_dir)
            return entries

        for md_file in sorted(self._adr_dir.glob("ADR-*.md")):
            m = ADR_FILENAME_RE.match(md_file.name)
            if not m:
                continue
            num = int(m.group(1))
            slug = m.group(2).replace("_", " ").replace("-", " ").strip()
            content = md_file.read_text(encoding="utf-8", errors="ignore")

            # 제목 추출
            tm = ADR_TITLE_RE.search(content)
            title = tm.group(1).strip() if tm else slug

            # 상태 추출
            sm = ADR_STATUS_RE.search(content)
            status = sm.group(1).capitalize() if sm else "Accepted"

            # Supersedes 추출
            supersedes = ADR_SUPERSEDES_RE.findall(content)

            entries.append(ADREntry(
                number=num, slug=slug, title=title,
                status=status, supersedes=supersedes,
                filename=md_file.name,
            ))

        logger.info("ADRIndexGenerator: %d개 ADR 스캔 완료", len(entries))
        return entries

    def generate_index(self, entries: Optional[List[ADREntry]] = None) -> str:
        """INDEX.md 내용 생성 (문자열 반환)."""
        if entries is None:
            entries = self.scan()

        lines = [
            "# ADR Index",
            "",
            "Literary OS 공식 ADR 목록. `adr_index_generator.py`에 의해 자동 생성됨.",
            "",
            "| ADR ID | 제목 | 상태 | Supersedes |",
            "|--------|------|------|------------|",
        ]
        for e in sorted(entries, key=lambda x: x.number):
            sup = ", ".join(e.supersedes) if e.supersedes else "—"
            lines.append(f"| [{e.adr_id}]({e.filename}) | {e.title} | {e.status} | {sup} |")

        lines += ["", f"*총 {len(entries)}개 ADR*", ""]
        return "\n".join(lines)

    def generate_mermaid(self, entries: Optional[List[ADREntry]] = None) -> str:
        """graph.mermaid Mermaid 의존 그래프 생성."""
        if entries is None:
            entries = self.scan()

        lines = ["graph LR"]
        for e in sorted(entries, key=lambda x: x.number):
            label = f"{e.adr_id}[\"{e.title[:30]}...\"]" \
                if len(e.title) > 30 else f"{e.adr_id}[\"{e.title}\"]"
            lines.append(f"    {label}")
            for sup in e.supersedes:
                lines.append(f"    {e.adr_id} -->|supersedes| {sup}")

        return "\n".join(lines) + "\n"

    def write(self, entries: Optional[List[ADREntry]] = None) -> Dict[str, Path]:
        """INDEX.md와 graph.mermaid를 output_dir에 저장."""
        if entries is None:
            entries = self.scan()

        self._output_dir.mkdir(parents=True, exist_ok=True)

        index_path = self._output_dir / "INDEX.md"
        mermaid_path = self._output_dir / "graph.mermaid"

        index_path.write_text(self.generate_index(entries), encoding="utf-8")
        mermaid_path.write_text(self.generate_mermaid(entries), encoding="utf-8")

        logger.info("ADR INDEX.md → %s", index_path)
        logger.info("ADR graph.mermaid → %s", mermaid_path)
        return {"index": index_path, "mermaid": mermaid_path}
