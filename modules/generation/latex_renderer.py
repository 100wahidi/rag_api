import re
from typing import Any
from jinja2 import Environment, BaseLoader

LATEX_ESCAPE_RULES = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}

_ESCAPE_REGEX = re.compile(
    "|".join(re.escape(k) for k in sorted(LATEX_ESCAPE_RULES.keys(), key=lambda x: -len(x)))
)


def filter_latex_escape(value: Any) -> str:
    """Jinja2 filter to lazily escape LaTeX special characters during interpolation."""
    if value is None:
        return ""
    text = str(value)
    return _ESCAPE_REGEX.sub(lambda m: LATEX_ESCAPE_RULES[m.group()], text)


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
    {\LARGE \textbf{\VAR{ cv.header.name | tex }}}\par\vspace{0.3em}
    \VAR{ cv.header.city | tex } $\bullet$ \VAR{ cv.header.phone | tex } $\bullet$ \href{mailto:\VAR{ cv.header.email }}{\VAR{ cv.header.email | tex }}
    \BLOCK{ if cv.header.linkedin } $\bullet$ \href{\VAR{ cv.header.linkedin }}{LinkedIn}\BLOCK{ endif }
    \BLOCK{ if cv.header.github } $\bullet$ \href{\VAR{ cv.header.github }}{GitHub}\BLOCK{ endif }\par\vspace{0.3em}
    \textbf{\Large \VAR{ cv.header.title | tex }}
\end{center}

% ================= SUMMARY =================
\BLOCK{ if cv.professional_summary }
\section*{Professional Summary}
\VAR{ cv.professional_summary | tex }
\BLOCK{ endif }

% ================= TECHNICAL COMPETENCIES =================
\BLOCK{ if cv.technical_competencies }
\section*{Core Technical Competencies}
\begin{itemize}[leftmargin=0.1em,label={}]
\BLOCK{ for comp in cv.technical_competencies }
    \item \VAR{ comp | tex }
\BLOCK{ endfor }
\end{itemize}
\BLOCK{ endif }

% ================= PROFESSIONAL EXPERIENCE =================
\BLOCK{ if cv.experiences }
\section*{Professional Experience}
\BLOCK{ for exp in cv.experiences }
\leavevmode
{\bfseries \VAR{ exp.company | tex }} \hfill \textit{\VAR{ exp.start_date | tex } -- \VAR{ exp.end_date | tex }}\par
\textit{\VAR{ exp.role | tex }} \hfill \textit{\VAR{ exp.location | tex }}\par
\BLOCK{ if exp.bullets }
\begin{itemize}
\BLOCK{ for bullet in exp.bullets }
    \item \VAR{ bullet | tex }
\BLOCK{ endfor }
\end{itemize}
\BLOCK{ endif }
\vspace{0.15cm}
\BLOCK{ endfor }
\BLOCK{ endif }

% ================= PROJECTS =================
\BLOCK{ if cv.projects }
\section*{Key Projects}
\BLOCK{ for project in cv.projects }
\leavevmode
\textbf{\VAR{ project.title | tex }} \hfill \textit{\VAR{ project.technologies | tex }}\par
\BLOCK{ if project.bullets }
\begin{itemize}
\BLOCK{ for bullet in project.bullets }
    \item \VAR{ bullet | tex }
\BLOCK{ endfor }
\end{itemize}
\BLOCK{ endif }
\vspace{0.15cm}
\BLOCK{ endfor }
\BLOCK{ endif }

% ================= EDUCATION =================
\BLOCK{ if cv.education }
\section*{Education}
\BLOCK{ for edu in cv.education }
\leavevmode
{\bfseries \VAR{ edu.degree | tex }} \hfill \textit{\VAR{ edu.school | tex }}\par
\textit{Graduation: \VAR{ edu.graduation_year | tex }}
\BLOCK{ if edu.description } -- \VAR{ edu.description | tex }\BLOCK{ endif }\par
\vspace{0.15cm}
\BLOCK{ endfor }
\BLOCK{ endif }

% ================= LANGUAGES & LEADERSHIP =================
\BLOCK{ if cv.languages or cv.leadership }
\section*{Languages \& Additional}
\BLOCK{ if cv.languages }\textbf{Languages:} \VAR{ cv.languages | join(', ') | tex }\par\BLOCK{ endif }
\BLOCK{ if cv.leadership }\textbf{Leadership/Activities:} \VAR{ cv.leadership | tex }\BLOCK{ endif }
\BLOCK{ endif }

\end{document}
"""


class LaTeXRenderer:
    def __init__(self):
        self.env = Environment(
            block_start_string=r"\BLOCK{",
            block_end_string=r"}",
            variable_start_string=r"\VAR{",
            variable_end_string=r"}",
            comment_start_string=r"\#{",
            comment_end_string=r"}",
            loader=BaseLoader(),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
        )
        # Register lazy escaping filter
        self.env.filters["tex"] = filter_latex_escape
        self.template = self.env.from_string(LATEX_CV_TEMPLATE)

    def render(self, data: Any) -> str:
        # Pass data directly without mutating intermediate dictionaries
        return self.template.render(cv=data)
