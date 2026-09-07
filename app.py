import sys
import legacy_app as legacy

# Mantém compatibilidade com o módulo de extensão existente.
sys.modules["app"] = legacy

from logo_feature import app  # noqa: E402,F401
