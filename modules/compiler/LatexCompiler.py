import asyncio
import re
import shutil
import tempfile
from pathlib import Path


class LatexCompiler:
    def __init__(self, latex_source: str):
        if len(latex_source) < 10:
            raise ValueError("latex_source must contain at least 10 characters.")
        self.latex_source = latex_source

    @staticmethod
    async def resolve_tex_engine(engine_name: str = "pdflatex") -> str:
        """Resolve the absolute path to the TeX compiler."""
        binary_path = shutil.which(engine_name) or shutil.which(f"{engine_name}.exe")
        if not binary_path:
            raise FileNotFoundError(
                f"TeX Engine '{engine_name}' not found. Install MiKTeX or TeX Live."
            )
        return binary_path

    async def compile_to_pdf(self) -> bytes:
        compiler_path = await self.resolve_tex_engine()
        with tempfile.TemporaryDirectory(prefix="cv_tex_") as temp_dir:
            work_dir = Path(temp_dir).resolve()
            tex_file = work_dir / "document.tex"
            pdf_file = work_dir / "document.pdf"
            log_file = work_dir / "document.log"
            tex_file.write_text(self.latex_source, encoding="utf-8")

            process = await asyncio.create_subprocess_exec(
                compiler_path, "-no-shell-escape", "-interaction=nonstopmode",
                "-halt-on-error", f"-output-directory={work_dir}", str(tex_file),
                cwd=str(work_dir), stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                _, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError("LaTeX compilation timed out after 10.0 seconds.")

            if process.returncode != 0 or not pdf_file.exists():
                log_content = (log_file.read_text(encoding="utf-8", errors="replace")
                               if log_file.exists() else stderr.decode("utf-8", errors="replace"))
                match = re.search(r"!(.*?)(?=\n\n|\n\?|\Z)", log_content, re.DOTALL)
                detail = match.group(1).strip().replace("\n", " ") if match else "Syntax error in LaTeX source."
                raise RuntimeError(f"Compilation failed: {detail}")
            return pdf_file.read_bytes()
