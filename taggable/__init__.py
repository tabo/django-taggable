"""

    taggable
    --------

    :synopsys: Efficient Tagging implementation for Django 1.1+
    :copyright: 2010 by `Gustavo Picon <https://tabo.pe>`_
    :license: Apache License 2.0
    :version: 0.01
    :url: http://code.tabo.pe/django-taggable/
    :documentation:
       `taggable-docs
       <http://docs.tabo.pe/django-taggable/tip/>`_
    :tests:
       `taggable-tests
       <http://code.tabo.pe/django-taggable/src/tip/taggable/tests.py>`_

"""

from taggable import signals

__version__ = '0.01'

signals.register()
del signals
