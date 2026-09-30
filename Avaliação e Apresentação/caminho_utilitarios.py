import sys
from pathlib import Path


def preparar_sys_path():
    """Adiciona ao sys.path a pasta de População (utilitarios_comuns.py) e a pasta atual."""
    raiz_repo = Path(__file__).resolve().parent.parent
    pasta_utilitarios = raiz_repo / "Seleção e Transformação" / "População"
    if not (pasta_utilitarios / "utilitarios_comuns.py").exists():
        raise ModuleNotFoundError(
            f"Não encontrei 'utilitarios_comuns.py' em: {pasta_utilitarios}"
        )
    sys.path.append(str(pasta_utilitarios))
    sys.path.append(str(Path.cwd()))
    return pasta_utilitarios
