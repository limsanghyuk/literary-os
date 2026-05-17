from __future__ import annotations

from typing import Any


class AuthorityController:
    def normalize_bundle(self, bundle: dict[str, Any]) -> dict[str, Any]:
        for packet in bundle["packets"]:
            payload = packet["payload"]
            if "display_name" in payload:
                payload["display_name"] = payload["display_name"].strip()
            if "motif" in payload:
                payload["motif"] = payload["motif"].strip()
            if "scene_goal" in payload:
                payload["scene_goal"] = " ".join(str(payload["scene_goal"]).split())
        return bundle
