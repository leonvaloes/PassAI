from __future__ import annotations

import json
import os
import threading
import uuid
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class JsonStore:
    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path)
        self.lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(self._empty_state())

    def _empty_state(self) -> dict[str, Any]:
        return {
            "active_user_id": None,
            "users": [],
            "jobs": [],
            "variants": [],
        }

    def _read(self) -> dict[str, Any]:
        with self.lock:
            with self.path.open("r", encoding="utf-8") as handle:
                return json.load(handle)

    def _write(self, data: dict[str, Any]) -> None:
        with self.lock:
            with self.path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self._read())

    def list_users(self) -> list[dict[str, Any]]:
        return self._read()["users"]

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        state = self._read()
        return next((user for user in state["users"] if user["id"] == user_id), None)

    def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        state = self._read()
        if any(user["profile_name"] == payload["profile_name"] for user in state["users"]):
            raise ValueError(f"Profile name '{payload['profile_name']}' already exists")

        timestamp = utc_now()
        user = {
            "id": uuid.uuid4().hex,
            **payload,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        state["users"].append(user)
        if not state["active_user_id"]:
            state["active_user_id"] = user["id"]
        self._write(state)
        return user

    def update_user(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        state = self._read()
        user = next((entry for entry in state["users"] if entry["id"] == user_id), None)
        if not user:
            raise KeyError(user_id)

        new_profile_name = payload.get("profile_name")
        if new_profile_name and any(
            entry["profile_name"] == new_profile_name and entry["id"] != user_id
            for entry in state["users"]
        ):
            raise ValueError(f"Profile name '{new_profile_name}' already exists")

        user.update(payload)
        user["updated_at"] = utc_now()
        self._write(state)
        return user

    def delete_user(self, user_id: str) -> None:
        state = self._read()
        state["users"] = [user for user in state["users"] if user["id"] != user_id]
        if state["active_user_id"] == user_id:
            state["active_user_id"] = state["users"][0]["id"] if state["users"] else None
        self._write(state)

    def get_active_user_id(self) -> str | None:
        return self._read()["active_user_id"]

    def set_active_user_id(self, user_id: str) -> None:
        state = self._read()
        if not any(user["id"] == user_id for user in state["users"]):
            raise KeyError(user_id)
        state["active_user_id"] = user_id
        self._write(state)

    def create_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        state = self._read()
        job = {
            "id": uuid.uuid4().hex,
            "created_at": utc_now(),
            **payload,
        }
        state["jobs"].append(job)
        self._write(state)
        return job

    def list_jobs(self) -> list[dict[str, Any]]:
        return self._read()["jobs"]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        state = self._read()
        return next((job for job in state["jobs"] if job["id"] == job_id), None)

    def delete_job(self, job_id: str) -> None:
        state = self._read()
        state["jobs"] = [job for job in state["jobs"] if job["id"] != job_id]
        state["variants"] = [variant for variant in state["variants"] if variant["job_id"] != job_id]
        self._write(state)

    def save_variants(self, job_id: str, variants: list[dict[str, Any]], replace: bool = False) -> None:
        state = self._read()
        if replace:
            state["variants"] = [variant for variant in state["variants"] if variant["job_id"] != job_id]
        state["variants"].extend(variants)
        self._write(state)

    def list_variants(self, job_id: str) -> list[dict[str, Any]]:
        state = self._read()
        variants = [variant for variant in state["variants"] if variant["job_id"] == job_id]
        return sorted(variants, key=lambda item: item["ranking_score"], reverse=True)

    def get_variant(self, variant_id: str) -> dict[str, Any] | None:
        state = self._read()
        return next((variant for variant in state["variants"] if variant["id"] == variant_id), None)

    def delete_variant(self, variant_id: str) -> None:
        state = self._read()
        state["variants"] = [variant for variant in state["variants"] if variant["id"] != variant_id]
        self._write(state)
