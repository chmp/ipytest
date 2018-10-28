from ._config import config
from ._util import emit_deprecation_warning

emit_deprecation_warning(
    "Importing the magics module is deprecated, use 'ipytest.config.magics = True'."
)

config.magics = True
