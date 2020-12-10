

import logging
import webob
from exam import fixture

from raven.base import Client
from raven.middleware import Sentry
from raven.utils.compat import Iterator
from raven.utils.testutils import TestCase


class TempStoreClient(Client):
    def __init__(self, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(**kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


class ErroringIterable(Iterator):
    def __init__(self):
        self.closed = False

    def __iter__(self):
        return self

    def __next__(self):
        raise ValueError('hello world')

    def close(self):
        self.closed = True


class ExitingIterable(ErroringIterable):
    def __init__(self, exc_func):
        self._exc_func = exc_func

    def __iter__(self):
        return self

    def __next__(self):
        raise self._exc_func()


class SimpleIteratable(Iterator):
    def __init__(self):
        self.closed = False
        self._iter = iter(['a'])

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iter)

    def close(self):
        self.closed = True


class ExampleApp(object):
    def __init__(self, iterable):
        self.iterable = iterable

    def __call__(self, environ, start_response):
        return self.iterable


class MiddlewareTestCase(TestCase):
    @fixture
    def client(self):
        return TempStoreClient()

    @fixture
    def request(self):
        return webob.Request.blank('/an-error?foo=bar')

    def test_captures_error_in_iteration(self):
        iterable = ErroringIterable()
        app = ExampleApp(iterable)
        middleware = Sentry(app, client=self.client)

        response = middleware(self.request.environ, lambda *args: None)

        with self.assertRaises(ValueError):
            response = list(response)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)

        assert 'exception' in event
        exc = event['exception']['values'][-1]
        self.assertEqual(exc['type'], 'ValueError')
        self.assertEqual(exc['value'], 'hello world')
        self.assertEqual(event['level'], logging.ERROR)
        self.assertEqual(event['message'], 'ValueError: hello world')

        assert 'request' in event
        http = event['request']
        self.assertEqual(http['url'], 'http://localhost/an-error')
        self.assertEqual(http['query_string'], 'foo=bar')
        self.assertEqual(http['method'], 'GET')
        # self.assertEquals(http['data'], {'foo': 'bar'})
        headers = http['headers']
        self.assertTrue('Host' in headers, list(headers.keys()))
        self.assertEqual(headers['Host'], 'localhost:80')
        env = http['env']
        self.assertTrue('SERVER_NAME' in env, list(env.keys()))
        self.assertEqual(env['SERVER_NAME'], 'localhost')
        self.assertTrue('SERVER_PORT' in env, list(env.keys()))
        self.assertEqual(env['SERVER_PORT'], '80')

    def test_systemexit_0_is_ignored(self):
        iterable = ExitingIterable(lambda: SystemExit(0))
        app = ExampleApp(iterable)
        middleware = Sentry(app, client=self.client)

        response = middleware(self.request.environ, lambda *args: None)

        with self.assertRaises(SystemExit):
            response = list(response)

        self.assertEqual(len(self.client.events), 0)

    def test_systemexit_is_captured(self):
        iterable = ExitingIterable(lambda: SystemExit(1))
        app = ExampleApp(iterable)
        middleware = Sentry(app, client=self.client)

        response = middleware(self.request.environ, lambda *args: None)

        with self.assertRaises(SystemExit):
            response = list(response)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)

        assert 'exception' in event
        exc = event['exception']['values'][-1]
        self.assertEqual(exc['type'], 'SystemExit')
        self.assertEqual(exc['value'], '1')
        self.assertEqual(event['level'], logging.ERROR)
        self.assertEqual(event['message'], 'SystemExit: 1')

    def test_keyboard_interrupt_is_captured(self):
        iterable = ExitingIterable(lambda: KeyboardInterrupt())
        app = ExampleApp(iterable)
        middleware = Sentry(app, client=self.client)

        response = middleware(self.request.environ, lambda *args: None)

        with self.assertRaises(KeyboardInterrupt):
            response = list(response)

        self.assertEqual(len(self.client.events), 1)
        event = self.client.events.pop(0)

        assert 'exception' in event
        exc = event['exception']['values'][-1]
        self.assertEqual(exc['type'], 'KeyboardInterrupt')
        self.assertEqual(exc['value'], '')
        self.assertEqual(event['level'], logging.ERROR)

    def test_close(self):
        iterable = SimpleIteratable()
        app = ExampleApp(iterable)
        middleware = Sentry(app, client=self.client)

        response = middleware(self.request.environ, lambda *args: None)
        list(response)  # exhaust iterator
        response.close()
        self.assertTrue(iterable.closed, True)
