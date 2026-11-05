# Portability and environment

Essay Studio is an ordinary folder of readable instructions, references, local scripts and assets. It can be cloned or extracted into a new workspace. It does not depend on a private ChatGPT Library ID, a hidden plugin, this conversation's scratch directory or a personal-skill installation to run. Historical identifiers inside the case archive document provenance only; the underlying files are included wherever recoverable.

## Capability levels

| Available capability | Work supported |
|---|---|
| Read repository files | Discussion, reference learning, outlines, critique and project records |
| Python plus dependencies | Native DOCX, calculations, comments extraction and structural audits |
| XeLaTeX or functioning LuaLaTeX with TikZ/PGFPlots | Exact chart/diagram rendering |
| LibreOffice/soffice | Local DOCX→PDF conversion |
| PyMuPDF/Pillow | Page rasterization and visual QA artifacts |
| Browser/search tools or equivalent access | Current primary-source research and real prototype inspection |
| Image-generation tools | Conceptual imagery/mockups when the task benefits |
| Separate agents | Independent review passes and cold-start validation |

The agent must discover its actual tools. Never fabricate a research visit, image generation, independent review, deployment or export when that capability is unavailable. Use existing supplied assets where suitable. If generation is unavailable, preserve a precise image brief/prompt and identify the missing step outside the audience deliverable. If separate agents are unavailable, run distinct passes and report their scope accurately.

Run `python studio.py doctor` to inventory dependencies. Binary availability alone does not prove an engine can compile: the validation run found a LuaLaTeX binary with incomplete packages and used a working XeLaTeX configuration. Render a representative chart through the actual engine before promising a working chart pipeline.

## Dependency setup

Use an isolated environment and `requirements.txt`; optional independent QR decoding uses `requirements-optional.txt`. `requirements-tested.txt` records versions actually exercised during this delivery, not a promise that all future environments match them. Install system LaTeX/Office tools using the host's normal approved mechanism when needed. No tools are silently installed by importing the package.

Pass paths containing spaces as separate quoted arguments. Keep project content/configuration local; use repository-relative links for bundled resources. Avoid fixed absolute workspace paths in reusable scripts. In this environment the runtime provided standard commands through PATH; those private command locations are not prerequisites for another user.

## Repository-only delivery

The ZIP contains the full requested private archive and a repository-ready skill folder. It has no `.git` history, credentials, active remote or personal-skill registration. The user can create their own private repository and add these files. Automatic agent loading varies; the explicit starting prompt in README works with any capable agent that can read the folder. Publishing, installing or submitting an essay remains a separate user action.
