# File: apps.py

from django.apps import AppConfig as _AppConfig
from django.utils.translation import ugettext_lazy as _
from django.core import checks as _checks

from demos.common.utils.config import registry
config = registry.get_config('bds')


class AppConfig(_AppConfig):
    name = 'demos.apps.bds'
    verbose_name = _('Ballot Distribution Center')



@_checks.register(deploy=True)
def tar_storage_check(app_configs, **kwargs):
    """Tests basic socket connectivity with crypto service
    """

    import tempfile
    import os
    import os.path

    try:
        fd, path = tempfile.mkstemp(dir=os.path.join(config.FILESYSTEM_ROOT, 'ballots'))
        os.close(fd)
        os.unlink(path)
        
        return []
    except Exception as e:
        return [_checks.Error("Tar storage \"%s/ballots\" check failed: %s" % \
                                (config.FILESYSTEM_ROOT, e),
                              hint="Check that directory exists and is writable")
                ]

#eof
