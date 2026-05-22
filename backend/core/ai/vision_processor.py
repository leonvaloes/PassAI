import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class VisionProcessor:
    """Processor for vision tasks using Codex CLI image input."""

    def __init__(
        self,
        codex_command: str = "codex",
        model: Optional[str] = None,
        timeout: int = 600,
        sandbox: str = "read-only",
    ):
        self.codex_command = codex_command
        self.model = model
        self.timeout = timeout
        self.sandbox = sandbox
        self.workdir = self._resolve_workdir()

    def get_detailed_description(self, image_path: str) -> Dict[str, Any]:
        """
        Get a detailed technical description of the image to pass to another LLM.
        """
        prompt = """You are Codex acting as a technical vision analyst.
Describe this software screenshot in detail for another AI to understand.
Transcribe visible code, logs, labels, errors, and UI state as exactly as possible.
Do not offer solutions. Return only the description."""

        result = self._run_codex_image(image_path, prompt)
        if result["success"]:
            return {
                "success": True,
                "description": result["answer"],
                "model": self.model or "codex-default",
            }
        return result

    def query_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Ask a specific question about an image."""
        codex_prompt = f"""You are Codex answering a question about the attached image.
Answer directly and concisely.

Question: {prompt}
"""
        return self._run_codex_image(image_path, codex_prompt)

    def _run_codex_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        try:
            image = Path(image_path).expanduser().resolve()
            if not image.exists():
                return {"success": False, "error": f"Image file not found: {image}"}

            if not shutil.which(self.codex_command):
                return {
                    "success": False,
                    "error": f"Codex CLI not found: {self.codex_command}",
                }

            with tempfile.TemporaryDirectory(prefix="passai-codex-vision-") as tmp_dir:
                output_path = Path(tmp_dir) / "last-message.txt"
                cmd = [
                    self.codex_command,
                    "exec",
                    "--cd",
                    str(self.workdir),
                    "--sandbox",
                    self.sandbox,
                    "--image",
                    str(image),
                    "--output-last-message",
                    str(output_path),
                    "-",
                ]

                if self.model:
                    cmd[2:2] = ["--model", self.model]

                env = os.environ.copy()
                env.setdefault("NO_COLOR", "1")

                result = subprocess.run(
                    cmd,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    cwd=str(self.workdir),
                    env=env,
                    timeout=self.timeout,
                )

                if result.returncode != 0:
                    details = (result.stderr or result.stdout or "").strip()
                    return {"success": False, "error": f"Codex vision failed: {details}"}

                answer = (
                    output_path.read_text(encoding="utf-8").strip()
                    if output_path.exists()
                    else (result.stdout or "").strip()
                )
                return {
                    "success": True,
                    "answer": answer,
                    "model": self.model or "codex-default",
                }

        except Exception as exc:
            logger.error("Vision query error: %s", exc, exc_info=True)
            return {"success": False, "error": str(exc)}

    def is_available(self) -> bool:
        """Check if Codex CLI is available."""
        return shutil.which(self.codex_command) is not None

    def _resolve_workdir(self) -> Path:
        current = Path(__file__).resolve()
        for parent in [current.parent, *current.parents]:
            if (parent / ".git").exists():
                return parent
        return Path.cwd().resolve()
