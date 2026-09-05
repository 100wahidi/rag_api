import re
from typing import Any
from jinja2 import Environment, BaseLoader
from .schema import GeneratedCV

LATEX_ESCAPE_RULES = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
    '\\': r'\textbackslash{}',
}

_ESCAPE_REGEX = re.compile(
    '|'.join(re.escape(str(key)) for key in sorted(LATEX_ESCAPE_RULES.keys(), key=lambda item: -len(item)))
)

def escape_latex(text: Any) -> str:
    """Recursively escape LaTeX special characters in strings or data structures."""
    if isinstance(text, str):
        return _ESCAPE_REGEX.sub(lambda match: LATEX_ESCAPE_RULES[match.group()], text)
    elif isinstance(text, list):
        return [escape_latex(item) for item in text]
    elif isinstance(text, dict):
        return {k: escape_latex(v) for k, v in text.items()}
    return text

LATEX_CV_TEMPLATE = r"""
        \documentclass[10pt,a4paper]{article}
        \usepackage[margin=0.8cm]{geometry}
        \usepackage[T1]{fontenc}
        \usepackage[utf8]{inputenc}
        \usepackage{lmodern}
        \usepackage{enumitem}
        \usepackage{titlesec}
        \usepackage[hidelinks]{hyperref}
        \usepackage{xcolor}

        \pagestyle{empty}
        \setlength{\parindent}{0pt}
        \setlength{\parskip}{0pt}
        \definecolor{accent}{RGB}{0,80,60}

        \titleformat{\section}{\large\bfseries\color{accent}}{}{0pt}{}[\titlerule]
        \titlespacing*{\section}{0pt}{0.3em}{0.4em}
        \setlist[itemize]{leftmargin=1.2em,itemsep=0.15em,topsep=0.2em}

        \begin{document}

        % ================= HEADER =================
        \begin{center}
            {\LARGE \textbf{\VAR{ cv.header.name }}}\par\vspace{0.3em}
            \VAR{ cv.header.city } $\bullet$ \VAR{ cv.header.phone } $\bullet$ \href{mailto:\VAR{ cv.header.email }}{\VAR{ cv.header.email }}
            \BLOCK{ if cv.header.linkedin } $\bullet$ \href{\VAR{ cv.header.linkedin }}{LinkedIn}\BLOCK{ endif }
            \BLOCK{ if cv.header.github } $\bullet$ \href{\VAR{ cv.header.github }}{GitHub}\BLOCK{ endif } \par\vspace{0.3em}
            \textbf{\Large \VAR{ cv.header.title }}
        \end{center}

        % ================= SUMMARY =================
        \section*{Professional Summary}
        \VAR{ cv.professional_summary }

        % ================= TECHNICAL COMPETENCIES =================
        \section*{Core Technical Competencies}
        \BLOCK{ if cv.technical_competencies }
        \begin{itemize}[leftmargin=0.1em,label={}]
        \BLOCK{ for competency in cv.technical_competencies }
            \item \VAR{ competency }
        \BLOCK{ endfor }
        \end{itemize}
        \BLOCK{ endif }

        % ================= PROFESSIONAL EXPERIENCE =================
        \section*{Professional Experience}
        \BLOCK{ for exp in cv.experiences }
            {\bfseries \VAR{ exp.company }} \hfill \textit{\VAR{ exp.start_date } -- \VAR{ exp.end_date }} \par
        \textit{\VAR{ exp.role }} \hfill \textit{\VAR{ exp.location }}
        \BLOCK{ if exp.bullets }% filepath: c:\Users\user\Desktop\API_Oauth\modules\generation\latex_renderer.py
        % ...existing code...

        % ================= PROFESSIONAL EXPERIENCE =================
        \section*{Professional Experience}
        \BLOCK{ for exp in cv.experiences }
        \leavevmode
        {\bfseries \VAR{ exp.company }} \hfill
        \textit{\VAR{ exp.start_date -- exp.end_date }}\par
        \textit{\VAR{ exp.role }} \hfill \textit{\VAR{ exp.location }}\par
        \BLOCK{ if exp.bullets }
        \begin{itemize}
        \BLOCK{ for bullet in exp.bullets }
        \item \VAR{ bullet }
        \BLOCK{ endfor }
        \end{itemize}
        \BLOCK{ endif }
        \vspace{0.15cm}
        \BLOCK{ endfor }

        % ================= PROJECTS =================
        \BLOCK{ if cv.projects }
        \section*{Key Projects}
        \BLOCK{ for project in cv.projects }
        \leavevmode
        \textbf{\VAR{ project.title }} \hfill
        \textit{\VAR{ project.technologies }}\par
        \BLOCK{ if project.bullets }
        \begin{itemize}
        \BLOCK{ for bullet in project.bullets }
        \item \VAR{ bullet }
        \BLOCK{ endfor }
        \end{itemize}
        \BLOCK{ endif }
        \vspace{0.15cm}
        \BLOCK{ endfor }
        \BLOCK{ endif }

        % ...existing code...
        \begin{itemize}
            \BLOCK{ for bullet in exp.bullets }
            \item \VAR{ bullet }
            \BLOCK{ endfor }
        \end{itemize}
        \BLOCK{ endif }
        \vspace{0.15cm}
        \BLOCK{ endfor }

        % ================= PROJECTS =================
        \BLOCK{ if cv.projects }
        \section*{Key Projects}
        \BLOCK{ for project in cv.projects }
        \leavevmode
        \textbf{\VAR{ project.title }} \hfill \textit{\VAR{ project.technologies }}
        \BLOCK{ if project.bullets }
        \begin{itemize}
            \BLOCK{ for bullet in project.bullets }
            \item \VAR{ bullet }
            \BLOCK{ endfor }
        \end{itemize}
        \BLOCK{ endif }
        \vspace{0.15cm}
        \BLOCK{ endfor }
        \BLOCK{ endif }

        % ================= EDUCATION =================
        \section*{Education}
        \BLOCK{ for edu in cv.education }
            \leavevmode
            {\bfseries \VAR{ edu.degree }} \hfill \textit{\VAR{ edu.school }} \par
        \textit{Graduation: \VAR{ edu.graduation_year }}
        \BLOCK{ if edu.description } -- \VAR{ edu.description }\BLOCK{ endif }
        \vspace{0.15cm}
        \BLOCK{ endfor }

        % ================= LANGUAGES & LEADERSHIP =================
        \BLOCK{ if cv.languages or cv.leadership }
        \section*{Languages \& Additional}
        \BLOCK{ if cv.languages }\textbf{Languages:} \VAR{ cv.languages | join(', ') } \par \BLOCK{ endif }
        \BLOCK{ if cv.leadership }\textbf{Leadership/Activities:} \VAR{ cv.leadership }\BLOCK{ endif }
        \BLOCK{ endif }

        \end{document}
        
        """

class LaTeXRenderer:
    def __init__(self):
        self.env = Environment(
            block_start_string=r'\BLOCK{',
            block_end_string=r'}',
            variable_start_string=r'\VAR{',
            variable_end_string=r'}',
            comment_start_string=r'\#{',
            comment_end_string=r'}',
            loader=BaseLoader(),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
        )
        self.template = self.env.from_string(LATEX_CV_TEMPLATE)

    def render(self, data: GeneratedCV) -> str:
        raw_dict = data.model_dump()
        escaped_dict = escape_latex(raw_dict)
        return self.template.render(cv=escaped_dict)