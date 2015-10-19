# File: config.py

TEXT_LEN = 128  # chars
RECEIPT_LEN = 6   # base32
VOTECODE_LEN = 6   # chars
CREDENTIAL_LEN = 8   # bytes
SECURITY_CODE_LEN = 8   # base32

# ------------------------------------------------------------------------------

import sys
from django.conf import settings

_config = sys.modules[__name__]

for iapp in settings.DEMOS_APPS
    for key, value in settings.DEMOS_CONFIG[iapp].items():
	setattr(_config, key, value)

URL = settings.DEMOS_URL
MAIN = settings.DEMOS_MAIN

LANGUAGES = settings.LANGUAGES

