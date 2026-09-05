import asyncio
import re
import tempfile
from pathlib import Path


class LatexCompilationError(Exception):
    """Raised when LaTeX compilation produces syntax or engine errors."""
    pass


class LatexTimeoutError(Exception):
    """Raised when compilation exceeds execution quota."""
    pass


class LatexCompiler:
    def __init__(self, binary_path: str):
        self._binary_path = binary_path

    @staticmethod
    def _parse_log_diagnostic(log_path: Path, raw_stderr: bytes) -> str:
        """Extracts the first critical TeX syntax error from log files."""
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"!(.*?)(?=\n\n|\n\?|\Z)", log_text, re.DOTALL)
            if match:
                return match.group(1).strip().replace("\n", " ")
        return raw_stderr.decode("utf-8", errors="replace").strip() or "Syntax error during LaTeX compilation."

    async def compile(self, latex_source: str, timeout: float = 8.0) -> bytes:
        # Isolated scratchpad workspace
        with tempfile.TemporaryDirectory(prefix="cv_tex_") as temp_dir:
            work_dir = Path(temp_dir).resolve()
            tex_file = work_dir / "document.tex"
            pdf_file = work_dir / "document.pdf"
            log_file = work_dir / "document.log"

            tex_file.write_text(latex_source, encoding="utf-8")

            cmd = [
                self._binary_path,
                "-no-shell-escape",
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={str(work_dir)}",
                str(tex_file.name),
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                # Guaranteed process cleanup
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass
                raise LatexTimeoutError(f"Compilation exceeded deadline of {timeout}s.")

            if process.returncode != 0 or not pdf_file.exists():
                detail = self._parse_log_diagnostic(log_file, stderr)
                raise LatexCompilationError(detail)

            return pdf_file.read_bytes()