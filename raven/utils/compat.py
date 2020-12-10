"""
raven.utils.compat
~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import urllib

try:
    from urllib.error import HTTPError
except ImportError:
    from urllib.error import HTTPError  # NOQA


try:
    import http.client as httplib  # NOQA
except ImportError:
    from http import client as httplib  # NOQA


try:
    import urllib.request as urllib2
except ImportError:
    import urllib.request, urllib.error, urllib.parse

Request = urllib.request.Request
urlopen = urllib.request.urlopen

try:
    from urllib.parse import quote as urllib_quote
except ImportError:
    from urllib.parse import quote as urllib_quote  # NOQA


try:
    from queue import Queue
except ImportError:
    from queue import Queue  # NOQA


try:
    import urllib.parse as _urlparse
except ImportError:
    from urllib import parse as _urlparse  # NOQA

urlparse = _urlparse

try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase  # NOQA
