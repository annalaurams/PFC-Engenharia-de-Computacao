import sys
from pathlib import Path

def preparar_sys_path():
    raiz_repo = Path(__file__).resolve().parent.parent
    pasta_utilitarios = raiz_repo / "Seleção e Transformação" / "População"
    if not (pasta_utilitarios / "utilitarios_comuns.py").exists():
        raise ModuleNotFoundError(
            f"Não encontrei 'utilitarios_comuns.py' em: {pasta_utilitarios}"
        )
    sys.path.append(str(pasta_utilitarios))
    sys.path.append(str(Path.cwd()))
    return pasta_utilitarios
