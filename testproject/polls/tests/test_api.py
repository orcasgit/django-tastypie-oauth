import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from oauth2_provider.models import Application, AccessToken
from tastypie.test import ResourceTestCase

from polls.models import Poll, Choice


class PollAPITestCase(ResourceTestCase):
    fixtures = ['polls_api_testdata.json']

    def setUp(self):
        super(PollAPITestCase, self).setUp()
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

        self.post_data = {
            "choice": "I don't know",
            "poll": '/api/v1/poll/1/'
        }

        # Prepare OAuth Toolkit Access
        ot_application = Application(
            user=self.user,
            redirect_uris='http://example.com',
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            name='Test Application'
        )
        ot_application.save()

        scopes = ("read","write","read write")
        for scope in scopes:
            scope_attrbute_name = "ot_token_"+scope.replace(" ","_")
            setattr(self, scope_attrbute_name, "TOKEN"+scope)
            ot_access_token = AccessToken(
                user=self.user,
                application=ot_application,
                expires=datetime.datetime.now() + datetime.timedelta(days=10),
                scope=scope,
                token=getattr(self,scope_attrbute_name)
            )
            ot_access_token.save()
        self.ot_token = self.ot_token_read_write

    def test_unauthorized(self):
        resp = self.api_client.get(self.urls['choice'], format='json')
        self.assertHttpUnauthorized(resp)

    def test_get_choices(self):
        resp = self.api_client.get('%s?oauth_consumer_key=%s' % (
            self.urls['choice'], self.ot_token), format='json')
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

    def test_scope_authorizations(self):
        #choice requires a read token, we should decline a token only with write
        resp = self.api_client.get('%s?oauth_consumer_key=%s' % (
            self.urls['choice'], self.ot_token_write), format='json')
        self.assertHttpUnauthorized(resp)

        #a read should pass
        resp = self.api_client.get('%s?oauth_consumer_key=%s' % (
            self.urls['choice'], self.ot_token_read), format='json')
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

        #a read+write should pass
        resp = self.api_client.get('%s?oauth_consumer_key=%s' % (
            self.urls['choice'], self.ot_token_read_write), format='json')
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

        #only read+write should pass for post
        resp = self.api_client.post('%s?oauth_consumer_key=%s' % (
            self.urls['choice'], self.ot_token_write), format='json', data=self.post_data)
        self.assertHttpUnauthorized(resp)
        resp = self.api_client.post('%s?oauth_consumer_key=%s' % (
            self.urls['choice'], self.ot_token_write), format='json', data=self.post_data)
        self.assertHttpUnauthorized(resp)
        resp = self.api_client.post('%s?oauth_consumer_key=%s' % (
            self.urls['choice'], self.ot_token_read_write), format='json', data=self.post_data)
        self.assertHttpCreated(resp)





