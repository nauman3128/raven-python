"""
raven.contrib.django
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""


default_app_config = 'raven.contrib.django.apps.RavenConfig'

from .client import DjangoClient  # NOQA
