"""
Codex-backed generation router.

PassAI does not call a model API or a local model server here. It delegates
generation to the Codex CLI, following the same agentic idea used by career-ops:
the app prepares context and Codex produces the reasoning/output.
"""

import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported generation providers."""

    CODEX = "codex"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """Codex router configuration."""

    default_provider: LLMProvider = LLMProvider.CODEX
    codex_command: str = "codex"
    codex_model: Optional[str] = None
    codex_profile: Optional[str] = None
    codex_timeout: int = 600
    codex_sandbox: str = "read-only"
    codex_workdir: Optional[str] = None
    max_tokens: int = 500
    temperature: float = 0.7
    enable_fallback: bool = False
    fallback_order: Optional[List[LLMProvider]] = None
    max_retries: int = 1

    def __post_init__(self):
        if isinstance(self.default_provider, str):
            value = self.default_provider.lower()
            self.default_provider = LLMProvider.LOCAL if value == "local" else LLMProvider(value)

        if self.default_provider == LLMProvider.LOCAL:
            self.default_provider = LLMProvider.CODEX

        self.codex_command = os.getenv("CODEX_COMMAND", self.codex_command)
        self.codex_model = self.codex_model or os.getenv("CODEX_MODEL") or None
        self.codex_profile = self.codex_profile or os.getenv("CODEX_PROFILE") or None

        self.fallback_order = [LLMProvider.CODEX]
        self.enable_fallback = False


class LLMRouter:
    """
    Router for Codex CLI generation.

    The public interface is intentionally kept compatible with the old router:
    - generate(prompt, ...)
    - generate_suggestion(...)
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.workdir = self._resolve_workdir(self.config.codex_workdir)
        self.stats = {
            "total_requests": 0,
            "codex_requests": 0,
            "fallbacks": 0,
            "errors": 0,
            "total_tokens": 0,
        }
        logger.info("LLM Router initialized with Codex CLI provider")

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        seed: Optional[int] = None,
    ) -> str:
        """Generate text by invoking Codex CLI."""
        self.stats["total_requests"] += 1
        try:
            wrapped_prompt = self._wrap_raw_prompt(prompt, max_tokens=max_tokens)
            return self._run_codex(wrapped_prompt)
        except Exception:
            self.stats["errors"] += 1
            raise

    def generate_suggestion(
        self,
        conversation_history: List[Dict],
        current_intent: str = "neutral",
        user_goal: str = "sales",
        screen_context: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
    ) -> Dict[str, Any]:
        """Generate a chat-style response by invoking Codex CLI."""
        self.stats["total_requests"] += 1
        start_time = time.time()

        try:
            prompt = self._build_codex_prompt(
                conversation_history=conversation_history,
                current_intent=current_intent,
                user_goal=user_goal,
                screen_context=screen_context,
            )
            response = self._run_codex(prompt).strip()
            return {
                "suggestion": response,
                "tokens": 0,
                "model": self.config.codex_model or "codex-default",
                "provider": "codex",
                "latency": time.time() - start_time,
            }
        except Exception:
            self.stats["errors"] += 1
            raise

    def _run_codex(self, prompt: str) -> str:
        if not shutil.which(self.config.codex_command):
            raise RuntimeError(
                f"Codex CLI not found: {self.config.codex_command}. "
                "Install/authenticate Codex CLI before using PassAI generation."
            )

        with tempfile.TemporaryDirectory(prefix="passai-codex-") as tmp_dir:
            output_path = Path(tmp_dir) / "last-message.txt"
            cmd = [
                self.config.codex_command,
                "exec",
                "--cd",
                str(self.workdir),
                "--sandbox",
                self.config.codex_sandbox,
                "--output-last-message",
                str(output_path),
                "-",
            ]

            if self.config.codex_model:
                cmd[2:2] = ["--model", self.config.codex_model]
            if self.config.codex_profile:
                cmd[2:2] = ["--profile", self.config.codex_profile]

            env = os.environ.copy()
            env.setdefault("NO_COLOR", "1")

            result = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                capture_output=True,
                cwd=str(self.workdir),
                env=env,
                timeout=self.config.codex_timeout,
            )

            if result.returncode != 0:
                details = (result.stderr or result.stdout or "").strip()
                raise RuntimeError(f"Codex generation failed: {details}")

            self.stats["codex_requests"] += 1

            if output_path.exists():
                return output_path.read_text(encoding="utf-8").strip()

            return (result.stdout or "").strip()

    def _wrap_raw_prompt(self, prompt: str, max_tokens: int) -> str:
        return f"""You are Codex running inside the PassAI project.
Complete the task below and return only the requested output. Do not explain the process.
Target maximum length: about {max_tokens} tokens.

TASK:
{prompt}
"""

    def _build_codex_prompt(
        self,
        conversation_history: List[Dict],
        current_intent: str,
        user_goal: str,
        screen_context: Optional[str],
    ) -> str:
        lines = [self._get_system_prompt(user_goal), ""]

        if screen_context:
            lines.extend(["SCREEN CONTEXT:", screen_context, ""])

        if current_intent:
            lines.extend(["CURRENT INTENT:", current_intent, ""])

        lines.append("CONVERSATION:")
        for msg in conversation_history[-10:]:
            speaker = str(msg.get("speaker", "user")).upper()
            text = msg.get("text") or msg.get("content") or ""
            if text:
                lines.append(f"{speaker}: {text}")

        lines.extend(["", "Return only the answer text that should be shown to the user."])
        return "\n".join(lines)

    def _get_system_prompt(self, user_goal: str) -> str:
        if user_goal == "Answer":
            return """You are Codex guiding the PassAI system.
Answer the user's question directly, accurately, and concisely.
Use conversation and screen context when provided.
Do not mention APIs, providers, or implementation details unless the user asks."""

        if user_goal == "Analyze":
            return """You are Codex guiding the PassAI system.
Analyze the provided conversation and return concrete, useful observations.
Keep the response concise and actionable."""

        if user_goal == "sales":
            return """You are Codex guiding the PassAI system during a live conversation.
Suggest natural, persuasive responses that build trust, address objections, and move the conversation forward.
Keep suggestions conversational and authentic."""

        if user_goal == "pitch":
            return """You are Codex guiding the PassAI system during a pitch.
Focus on clear value, confidence, storytelling, and a concrete next step."""

        return "You are Codex guiding the PassAI system. Be helpful, direct, and practical."

    def _resolve_workdir(self, configured: Optional[str]) -> Path:
        if configured:
            return Path(configured).expanduser().resolve()

        candidates = [Path.cwd(), Path(__file__).resolve()]
        for candidate in candidates:
            current = candidate if candidate.is_dir() else candidate.parent
            for parent in [current, *current.parents]:
                if (parent / ".git").exists():
                    return parent

        return Path.cwd().resolve()

    def check_providers(self) -> Dict[str, bool]:
        return {
            "codex": shutil.which(self.config.codex_command) is not None,
            "local": shutil.which(self.config.codex_command) is not None,
        }

    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()

    def reset_stats(self):
        for key in self.stats:
            self.stats[key] = 0
