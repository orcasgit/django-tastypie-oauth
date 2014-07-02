import logging

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from tastypie.authentication import Authentication


"""
This is a simple OAuth 2.0 authentication model for tastypie

Dependencies (one of these):
- django-oauth-toolkit: https://github.com/evonove/django-oauth-toolkit
- django-oauth2-provider: https://github.com/caffeinehit/django-oauth2-provider
"""

class OAuthError(RuntimeError):
    """Generic exception class."""
    def __init__(self, message='OAuth error occured.'):
        self.message = message


class OAuth20Authentication(Authentication):
    """
    OAuth authenticator.

    This Authentication method checks for a provided HTTP_AUTHORIZATION
    and looks up to see if this is a valid OAuth Access Token
    """
    def __init__(self, realm='API'):
        self.realm = realm

    def is_authenticated(self, request, **kwargs):
        """
        Verify 2-legged oauth request. Parameters accepted as
        values in "Authorization" header, or as a GET request
        or in a POST body.
        """
        logging.info("OAuth20Authentication")

        try:
            key = request.GET.get('oauth_consumer_key')
            if not key:
                key = request.POST.get('oauth_consumer_key')
            if not key:
                auth_header_value = request.META.get('HTTP_AUTHORIZATION')
                if auth_header_value:
                    key = auth_header_value.split(' ')[1]
            if not key:
                logging.error('OAuth20Authentication. No consumer_key found.')
                return None
            """
            If verify_access_token() does not pass, it will raise an error
            """
            token = verify_access_token(key)

            # If OAuth authentication is successful, set the request user to
            # the token user for authorization
            request.user = token.user

            # If OAuth authentication is successful, set oauth_consumer_key on
            # request in case we need it later
            request.META['oauth_consumer_key'] = key
            return True
        except KeyError, e:
            logging.exception("Error in OAuth20Authentication.")
            request.user = AnonymousUser()
            return False
        except Exception, e:
            logging.exception("Error in OAuth20Authentication.")
            return False
        return True

def verify_access_token(key):
    # Import the AccessToken model
    try:
        model = settings.OAUTH_ACCESS_TOKEN_MODEL
        model_parts = model.split('.')
        module_path = '.'.join(model_parts[:-1])
        module = __import__(module_path, globals(), locals(), ['AccessToken'])
        AccessToken = getattr(module, model_parts[-1])
    except:
        raise OAuthError("Error importing AccessToken model: %s" % model)

    # Check if key is in AccessToken key
    try:
        token = AccessToken.objects.get(token=key)

        # Check if token has expired
        if token.expires < timezone.now():
            raise OAuthError('AccessToken has expired.')
    except AccessToken.DoesNotExist, e:
        raise OAuthError("AccessToken not found at all.")

    logging.info('Valid access')
    return token
