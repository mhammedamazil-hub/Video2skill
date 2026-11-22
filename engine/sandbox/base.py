# Disposable execution environments for running skill steps safely.

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SandboxResult:
    ok: bool
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: int
    artifacts: list[str] = field(default_factory=list)
    sandboxed: bool = False
    driver: str = "none"
    refused: bool = False
    refuse_reason: str = ""


class Sandbox:
    """Runs a command in a disposable, restricted environment.

    Supported drivers:
      - bubblewrap (Linux): unshared mount/pid/net namespace, read-only host fs
      - none: refuses to run (never executes unconfined)
    """

    def __init__(
        self,
        enabled: bool = True,
        driver: str = "none",
        timeout_ms: int = 300000,
        max_memory_mb: int = 2048,
        network: bool = False,
    ) -> None:
        self.enabled = enabled
        self.driver = driver
        self.timeout_ms = timeout_ms
        self.max_memory_mb = max_memory_mb
        self.network = network

    def run(
        self,
        cmd: list[str],
        workdir: str | None = None,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        import time

        start = time.time()

        # Never run unconfined if no supported sandbox exists.
        if not self.enabled or self.driver == "none":
            return SandboxResult(
                ok=False,
                exit_code=None,
                stdout="",
                stderr="",
                duration_ms=int((time.time() - start) * 1000),
                artifacts=[],
                sandboxed=False,
                driver="none",
                refused=True,
                refuse_reason=(
                    "No supported sandbox driver available. "
                    "Install bubblewrap (Linux) or configure a sandbox driver, "
                    "or run steps manually. Execution is refused, not downgraded."
                ),
            )

        if self.driver == "bubblewrap":
            return self._run_bubblewrap(cmd, workdir, env, start)

        return SandboxResult(
            ok=False,
            exit_code=None,
            stdout="",
            stderr=f"unsupported sandbox driver: {self.driver}",
            duration_ms=int((time.time() - start) * 1000),
            artifacts=[],
            sandboxed=False,
            driver=self.driver,
            refused=True,
            refuse_reason=f"unsupported sandbox driver: {self.driver}",
        )

    def _run_bubblewrap(self, cmd, workdir, env, start) -> SandboxResult:
        bwrap = shutil.which("bwrap")
        if not bwrap:
            return SandboxResult(
                ok=False,
                exit_code=None,
                stdout="",
                stderr="bubblewrap (bwrap) not found on PATH.",
                duration_ms=int((time.time() - start) * 1000),
                artifacts=[],
                sandboxed=False,
                driver="bubblewrap",
                refused=True,
                refuse_reason="bubblewrap not installed; execution refused.",
            )

        work = workdir or tempfile.mkdtemp(prefix="v2s-sandbox-")
        bw_cmd = [
            bwrap,
            "--unshare-pid",
            "--unshare-net",
            "--die-with-parent",
            "--proc", "/proc",
            "--dev", "/dev",
            "--bind", work, work,
            "--cwd", work,
        ]
        if not self.network:
            # --unshare-net already blocks network; kept explicit for clarity.
            pass
        bw_cmd += cmd

        merged_env = dict(os.environ)
        merged_env.update(env or {})
        # Drop potentially dangerous vars.
        for k in ("LD_PRELOAD", "LD_LIBRARY_PATH"):
            merged_env.pop(k, None)

        try:
            res = subprocess.run(
                bw_cmd,
                cwd=work,
                env=merged_env,
                capture_output=True,
                text=True,
                timeout=self.timeout_ms / 1000.0,
            )
            return SandboxResult(
                ok=res.returncode == 0,
                exit_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                duration_ms=int((time.time() - start) * 1000),
                artifacts=[],
                sandboxed=True,
                driver="bubblewrap",
                refused=False,
            )
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(
                ok=False,
                exit_code=-1,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "") + "\n[command timed out]",
                duration_ms=self.timeout_ms,
                artifacts=[],
                sandboxed=True,
                driver="bubblewrap",
                refused=False,
            )
