


import logbook
from raven.utils.testutils import TestCase
from raven.utils import six
from raven.base import Client
from raven.handlers.logbook import SentryHandler


class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


class LogbookHandlerTest(TestCase):
    def setUp(self):
        self.logger = logbook.Logger(__name__)

    def test_logger(self):
        client = TempStoreClient(include_paths=['tests', 'raven'])
        handler = SentryHandler(client)
        logger = self.logger

        with handler.applicationbound():
            logger.error('This is a test error')

            self.assertEqual(len(client.events), 1)
            event = client.events.pop(0)
            self.assertEqual(event['logger'], __name__)
            self.assertEqual(event['level'], 'error')
            self.assertEqual(event['message'], 'This is a test error')
            self.assertFalse('exception' in event)
            self.assertTrue('sentry.interfaces.Message' in event)
            msg = event['sentry.interfaces.Message']
            self.assertEqual(msg['message'], 'This is a test error')
            self.assertEqual(msg['params'], ())

            logger.warning('This is a test warning')
            self.assertEqual(len(client.events), 1)
            event = client.events.pop(0)
            self.assertEqual(event['logger'], __name__)
            self.assertEqual(event['level'], 'warning')
            self.assertEqual(event['message'], 'This is a test warning')
            self.assertFalse('exception' in event)
            self.assertTrue('sentry.interfaces.Message' in event)
            msg = event['sentry.interfaces.Message']
            self.assertEqual(msg['message'], 'This is a test warning')
            self.assertEqual(msg['params'], ())

            logger.info('This is a test info with a url', extra=dict(
                url='http://example.com',
            ))
            self.assertEqual(len(client.events), 1)
            event = client.events.pop(0)
            if six.PY3:
                expected = "'http://example.com'"
            else:
                expected = "u'http://example.com'"
            self.assertEqual(event['extra']['url'], expected)
            self.assertFalse('exception' in event)
            self.assertTrue('sentry.interfaces.Message' in event)
            msg = event['sentry.interfaces.Message']
            self.assertEqual(msg['message'], 'This is a test info with a url')
            self.assertEqual(msg['params'], ())

            try:
                raise ValueError('This is a test ValueError')
            except ValueError:
                logger.info('This is a test info with an exception', exc_info=True)

            self.assertEqual(len(client.events), 1)
            event = client.events.pop(0)

            self.assertEqual(event['message'], 'This is a test info with an exception')
            assert 'exception' in event
            exc = event['exception']['values'][0]
            self.assertEqual(exc['type'], 'ValueError')
            self.assertEqual(exc['value'], 'This is a test ValueError')
            self.assertTrue('sentry.interfaces.Message' in event)
            msg = event['sentry.interfaces.Message']
            self.assertEqual(msg['message'], 'This is a test info with an exception')
            self.assertEqual(msg['params'], ())

            # test args
            logger.info('This is a test of {0}', 'args')
            self.assertEqual(len(client.events), 1)
            event = client.events.pop(0)
            self.assertEqual(event['message'], 'This is a test of args')
            assert 'exception' not in event
            self.assertTrue('sentry.interfaces.Message' in event)
            msg = event['sentry.interfaces.Message']
            self.assertEqual(msg['message'], 'This is a test of {0}')
            expected = ("'args'",) if six.PY3 else ("u'args'",)
            self.assertEqual(msg['params'], expected)

    def test_client_arg(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client)
        self.assertEqual(handler.client, client)

    def test_client_kwarg(self):
        client = TempStoreClient(include_paths=['tests'])
        handler = SentryHandler(client=client)
        self.assertEqual(handler.client, client)

    def test_first_arg_as_dsn(self):
        handler = SentryHandler('http://public:secret@example.com/1')
        self.assertTrue(isinstance(handler.client, Client))

    def test_custom_client_class(self):
        handler = SentryHandler('http://public:secret@example.com/1', client_cls=TempStoreClient)
        self.assertTrue(type(handler.client), TempStoreClient)

    def test_invalid_first_arg_type(self):
        self.assertRaises(ValueError, SentryHandler, object)

    def test_missing_client_arg(self):
        self.assertRaises(TypeError, SentryHandler)
