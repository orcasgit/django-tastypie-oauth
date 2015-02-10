import datetime
import six

from django import VERSION
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from tastypie.test import ResourceTestCase

from polls.models import Poll, Choice

try:
    from django.apps import apps
except ImportError:  # Fallback for Django < 1.7
    from django.db.models import loading
    apps = loading.cache

try:
    from unittest import skipIf
except ImportError:  # Fallback for Python < 2.6
    from unittest2 import skipIf


class CustomSettingsTestCase(ResourceTestCase):
    """
    A TestCase which makes extra models available in the Django project, just for testing.
    Based on http://djangosnippets.org/snippets/1011/ in Django 1.4 style.
    """
    new_settings = {}
    _override = None

    @classmethod
    def setUpClass(cls):
        cls._override = override_settings(**cls.new_settings)
        cls._override.enable()
        if 'INSTALLED_APPS' in cls.new_settings:
            cls.syncdb()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        if 'INSTALLED_APPS' in cls.new_settings:
            cls.syncdb(True)

    @classmethod
    def syncdb(cls, teardown=False):
        apps.loaded = False
        kwargs = {'verbosity': 0, 'interactive': False}
        try:
            call_command('syncdb', **kwargs)
        except CommandError:  # Us migrate command if syncdb isn't available
            if teardown:
                return
            for app_needing_migration in cls.apps_needing_migration:
                call_command('makemigrations', app_needing_migration, **kwargs)
                call_command('migrate', app_needing_migration, **kwargs)


class PollAPITestCaseBase(object):
    def setUp(self):
        super(PollAPITestCaseBase, self).setUp()
        call_command('loaddata', 'polls_api_testdata.json', verbosity=0)
        self.poll_1 = Poll.objects.get(pk=1)
        self.poll_2 = Poll.objects.get(pk=2)
        self.urls = {}
        kwargs = {'api_name': 'v1'}
        for api in ['choice', 'poll']:
            kwargs['resource_name'] = api
            self.urls[api] = reverse('api_dispatch_list', kwargs=kwargs)

        # Create a user.
        username = 'username'
        email = 'username@example.com'
        password = 'password'
        self.user = User.objects.create_user(username, email, password)

        # Our fake oauth token
        self.oauth_token = 'TOKEN'

    def test_unauthorized(self):
        resp = self.api_client.get(self.urls['choice'], format='json')
        self.assertHttpUnauthorized(resp)

    def test_get_choices(self):
        resp = self.api_client.get('%s?oauth_consumer_key=%s' % (
            self.urls['choice'], self.oauth_token), format='json')
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)


class PollAPITestCaseOAuthToolkit(PollAPITestCaseBase, CustomSettingsTestCase):
    apps_needing_migration = ('oauth2_provider',)
    new_settings = dict(
        INSTALLED_APPS=settings.INSTALLED_APPS + ('oauth2_provider',),
        OAUTH_ACCESS_TOKEN_MODEL='oauth2_provider.models.AccessToken')
    def setUp(self):
        super(PollAPITestCaseOAuthToolkit, self).setUp()
        # Prepare OAuth Toolkit Access
        from oauth2_provider.models import AccessToken, Application
        ot_application = Application(
            user=self.user,
            redirect_uris='http://example.com',
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            name='Test Application'
        )
        ot_application.save()
        ot_access_token = AccessToken(
            user=self.user,
            application=ot_application,
            expires=datetime.datetime.now() + datetime.timedelta(days=10),
            scope='read',
            token=self.oauth_token
        )
        ot_access_token.save()


@skipIf(six.PY3 or VERSION[0:2] > (1,8),
        'Django OAuth2 Provider does not support Python 3.x or Django > 1.8')
class PollAPITestCaseOAuth2Provider(PollAPITestCaseBase, CustomSettingsTestCase):
    apps_needing_migration = ('provider.oauth2',)
    new_settings = dict(
        INSTALLED_APPS=settings.INSTALLED_APPS + ('provider', 'provider.oauth2',),
        OAUTH_ACCESS_TOKEN_MODEL='provider.oauth2.models.AccessToken')
    def setUp(self):
        super(PollAPITestCaseOAuth2Provider, self).setUp()
        from provider.oauth2.models import AccessToken, Client
        from provider.constants import CONFIDENTIAL
        # Prepare OAuth2 Provider Access
        op_client = Client(
            user=self.user,
            name='Test Application',
            url='http://example.com',
            redirect_uri='http://example.com',
            client_type=CONFIDENTIAL
        )
        op_client.save()
        op_access_token = AccessToken(
            user=self.user,
            client=op_client,
            expires=datetime.datetime.now() + datetime.timedelta(days=10),
            token=self.oauth_token
        )
        op_access_token.save()
