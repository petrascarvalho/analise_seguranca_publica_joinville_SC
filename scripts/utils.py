from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_path(*parts: str) -> Path:
    """Resolve caminhos a partir da raiz do projeto, sem depender do cwd."""
    return PROJECT_ROOT.joinpath(*parts)
