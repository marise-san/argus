"""Adiciona src/ ao sys.path para que os testes encontrem o pacote argus."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
