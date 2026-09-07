import sys
import legacy_app as legacy

# Mantém compatibilidade com os módulos de extensão existentes.
sys.modules["app"] = legacy

import logo_feature  # noqa: E402,F401
from whatsapp_alerts import app  # noqa: E402,F401
import compliance  # noqa: E402,F401
