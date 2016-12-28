import datetime
import six

from django import VERSION
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

try:
    from tastypie.test import ResourceTestCaseMixin
except ImportError:  # Fallback for tastypie<0.13
    from tastypie.test import ResourceTestCase as ResourceTestCaseMixin

from oauth2_provider.models import AccessToken, Application

from polls.models import Poll, Choice

from django.apps import apps


class PollAPITestCaseOAuthToolkit(ResourceTestCaseMixin, TestCase):
    def setUp(self):
        super(PollAPITestCaseOAuthToolkit, self).setUp()
        call_command('loaddata', 'polls_api_testdata.json', verbosity=0)
        self.client = Client()
        self.poll_1 = Poll.objects.get(pk=1)
        self.poll_2 = Poll.objects.get(pk=2)
        self.urls = {}
        kwargs = {'api_name': 'v1'}
        apis = [
            'choice_toolkit',
            'scoped_choice_toolkit',
            'poll_toolkit',
            'scoped_poll_toolkit',
        ]
        for api in apis:
            kwargs['resource_name'] = api
            self.urls[api] = reverse('api_dispatch_list', kwargs=kwargs)

        # Create a user.
        username = 'username'
        email = 'username@example.com'
        password = 'password'
        self.user = User.objects.create_user(username, email, password)
        self.scopes = ("read", "write", "read write")
        for scope in self.scopes:
            scope_attrbute_name = "token_" + scope.replace(" ", "_")
            setattr(self, scope_attrbute_name, "TOKEN" + scope)
        self.token = 'TOKEN'
        self.scoped_token = self.token_read_write

        ot_application = Application(
            user=self.user,
            redirect_uris='http://example.com',
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            name='Test Application'
        )
        ot_application.save()

        for scope in self.scopes + (None,):
            options = {
                'user': self.user,
                'application': ot_application,
                'expires': datetime.datetime.now() + datetime.timedelta(days=10),
                'token': self.token
            }
            if scope:
                scope_attrbute_name = "token_" + scope.replace(" ", "_")
                options.update({
                    'scope': scope,
                    'token': getattr(self, scope_attrbute_name)
                })
            ot_access_token = AccessToken(**options)
            ot_access_token.save()
        self.choice_url = self.urls['choice_toolkit']
        self.poll_url = self.urls['poll_toolkit']
        self.scoped_choice_url = self.urls['scoped_choice_toolkit']
        self.scoped_poll_url = self.urls['scoped_poll_toolkit']

    def test_regular_authorization(self):
        resp = self.api_client.get('%s?oauth_consumer_key=%s' % (
            self.choice_url, self.token))
        self.assertHttpOK(resp)

        resp = self.api_client.get(
            self.choice_url, authentication='OAuth ' + self.token)
        self.assertHttpOK(resp)

        resp = self.api_client.get(
            self.choice_url, Authorization='OAuth ' + self.token)
        self.assertHttpOK(resp)

        data = {
            'poll': self.poll_url + '1/',
            'choice': 'Maybe'
        }
        resp = self.api_client.post(self.choice_url, data=data,
                                    authentication='OAuth ' + self.token)
        self.assertHttpCreated(resp)

        resp = self.api_client.post(self.choice_url, data=data,
                                    Authorization='OAuth ' + self.token)
        self.assertHttpCreated(resp)

        data['oauth_consumer_key'] = self.token
        resp = self.api_client.post(self.choice_url, data=data)
        self.assertHttpCreated(resp)

    def test_unauthorized(self):
        resp = self.api_client.get(self.choice_url, format='json')
        self.assertHttpUnauthorized(resp)

        data = {
            'poll': self.poll_url + '1/',
            'choice': 'Maybe'
        }
        resp = self.api_client.post(self.choice_url, data=data)
        self.assertHttpUnauthorized(resp)

    def test_get_choices(self):
        resp = self.api_client.get('%s?oauth_consumer_key=%s' % (
            self.choice_url, self.token), format='json')
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

    def test_scope_authorizations(self):
        #choice requires a read token, we should decline a token only with write
        resp = self.api_client.get('%s?oauth_consumer_key=%s' % (
            self.scoped_choice_url, self.token_write), format='json')
        self.assertHttpUnauthorized(resp)

        #a read should pass
        resp = self.api_client.get('%s?oauth_consumer_key=%s' % (
            self.scoped_choice_url, self.token_read), format='json')
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

        #a read+write should pass
        resp = self.api_client.get('%s?oauth_consumer_key=%s' % (
            self.scoped_choice_url, self.token_read_write), format='json')
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

        #only read+write should pass for post
        post_data = {
            "choice": "I don't know",
            "poll": '%s1/' % self.scoped_poll_url
        }
        resp = self.api_client.post('%s?oauth_consumer_key=%s' % (
            self.scoped_choice_url, self.token_read), format='json', data=post_data)
        self.assertHttpUnauthorized(resp)
        resp = self.api_client.post('%s?oauth_consumer_key=%s' % (
            self.scoped_choice_url, self.token_write), format='json', data=post_data)
        self.assertHttpUnauthorized(resp)
        resp = self.api_client.post('%s?oauth_consumer_key=%s' % (
            self.scoped_choice_url, self.token_read_write), format='json', data=post_data)
        self.assertHttpCreated(resp)
