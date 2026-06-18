"""
finetune/cloud_storage.py — 클라우드 비공개 데이터 저장(저작권 안전) (V786, ADR-247).

회사 핸드오프 §3.1 미구현 보강: 선호쌍(verbatim 포함)을 클라우드 학습에 쓰되
**비공개·일시적·암호화** 저장 + **자동 삭제**(저작권 안전). V777 RunPodJobLifecycle의
주입형 Uploader/Downloader 실체.

원칙(ADR-243/§3.1):
- 올리는 건 비공개·임시(공개 저장소 금지), 회수는 verbatim 없는 LoRA 어댑터만.
- 업로드 전 클라이언트측 암호화, 학습 후 즉시 삭제.
- ※암호화는 SHA256-CTR 키스트림(의존성 0, 전송·휴면 기본보호). 운영은 Fernet/age 권장(명시).
LLM-0: 저장·암호화 결정론(LLM 미호출).
"""
from __future__ import annotations
import abc
import hashlib
import os
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# transport: (method, url, headers, body|None) -> (status, bytes)
Transport = Callable[[str, str, Dict[str, str], Optional[bytes]], Tuple[int, bytes]]
# url_provider: (key, op in {"put","get","delete"}) -> presigned url
UrlProvider = Callable[[str, str], str]


def _keystream(key: bytes, n: int) -> bytes:
    out = bytearray(); ctr = 0
    while len(out) < n:
        out += hashlib.sha256(key + ctr.to_bytes(8, "big")).digest(); ctr += 1
    return bytes(out[:n])


def encrypt_bytes(data: bytes, key: str) -> bytes:
    """SHA256-CTR 키스트림 XOR(대칭). 기본 보호용 — 운영은 AEAD 권장."""
    kb = hashlib.sha256(key.encode("utf-8")).digest()
    ks = _keystream(kb, len(data))
    return bytes(b ^ k for b, k in zip(data, ks))


# 대칭: 복호화 = 암호화
decrypt_bytes = encrypt_bytes


def _urllib_transport(method: str, url: str, headers: Dict[str, str],
                      body: Optional[bytes]) -> Tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() if hasattr(e, "read") else b""
    except Exception:
        return 0, b""


class CloudStore(abc.ABC):
    """비공개 클라우드 저장 계약: put(암호화 업로드) / get(다운로드 복호화) / delete."""

    @abc.abstractmethod
    def put(self, local_path: str) -> str: ...
    @abc.abstractmethod
    def get(self, url: str, dest_path: str) -> bool: ...
    @abc.abstractmethod
    def delete(self, url: str) -> bool: ...


class PresignedHttpStore(CloudStore):
    """프리사인 URL(S3/B2/MinIO 호환) 기반 비공개 저장 + 클라이언트 암호화 + 삭제 추적."""

    def __init__(self, url_provider: UrlProvider, encrypt_key: str = "",
                 transport: Optional[Transport] = None) -> None:
        self._url = url_provider
        self._key = encrypt_key or os.environ.get("LOS_CLOUD_ENC_KEY", "")
        self._t = transport or _urllib_transport
        self._uploaded: List[str] = []     # 자동삭제 추적

    def url_for(self, key: str, op: str) -> str:
        """키·연산에 대한 프리사인 URL(어댑터 회수용 등)."""
        return self._url(key, op)

    def _key_of(self, local_path: str) -> str:
        h = hashlib.sha256(local_path.encode()).hexdigest()[:12]
        return f"litos-private/{h}-{os.path.basename(local_path)}"

    def put(self, local_path: str) -> str:
        with open(local_path, "rb") as f:
            data = f.read()
        if self._key:
            data = encrypt_bytes(data, self._key)
        key = self._key_of(local_path)
        url = self._url(key, "put")
        status, _ = self._t("PUT", url, {"Content-Type": "application/octet-stream"}, data)
        if status not in (200, 201, 204):
            raise IOError(f"업로드 실패 {status}")
        get_url = self._url(key, "get")
        self._uploaded.append(key)
        return get_url

    def get(self, url: str, dest_path: str) -> bool:
        status, body = self._t("GET", url, {}, None)
        if status != 200:
            return False
        if self._key:
            body = decrypt_bytes(body, self._key)
        with open(dest_path, "wb") as f:
            f.write(body)
        return True

    def delete(self, url_or_key: str) -> bool:
        url = self._url(url_or_key, "delete") if not url_or_key.startswith("http") else url_or_key
        status, _ = self._t("DELETE", url, {}, None)
        return status in (200, 202, 204)

    def cleanup(self) -> int:
        """업로드한 모든 임시 객체 자동 삭제(저작권 안전). 삭제 건수 반환."""
        n = 0
        for key in list(self._uploaded):
            if self.delete(key):
                n += 1
            self._uploaded.remove(key)
        return n


@dataclass
class StorageReport:
    uploaded_url: str
    encrypted:    bool
    deleted:      int

    def to_dict(self) -> Dict[str, Any]:
        return {"uploaded_url": self.uploaded_url, "encrypted": self.encrypted, "deleted": self.deleted}
