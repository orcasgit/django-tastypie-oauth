import logging
import json
import six

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from tastypie.authentication import Authentication
from tastypie.http import HttpUnauthorized

"""
This is a simple OAuth 2.0 authentication model for tastypie

Dependencies (one of these):
- django-oauth-toolkit: https://github.com/evonove/django-oauth-toolkit
- django-oauth2-provider: https://github.com/caffeinehit/django-oauth2-provider
"""

log = logging.getLogger('tastypie_oauth')


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
        values in the "Authorization" header, as a GET request parameter,
        or in a POST body.
        """
        log.info("OAuth20Authentication")
        try:
            key = request.GET.get('oauth_consumer_key')
            if not key:
                for header in ['Authorization', 'HTTP_AUTHORIZATION']:
                    auth_header_value = request.META.get(header)
                    if auth_header_value:
                        key = auth_header_value.split(' ', 1)[1]
                        break
            if not key and request.method == 'POST':
                if request.META.get('CONTENT_TYPE') == 'application/json':
                    decoded_body = request.body.decode('utf8')
                    key = json.loads(decoded_body)['oauth_consumer_key']
            if not key:
                log.info('OAuth20Authentication. No consumer_key found.')
                return None
            """
            If verify_access_token() does not pass, it will raise an error
            """
            token = self.verify_access_token(key, request, **kwargs)

            # If OAuth authentication is successful, set the request user to
            # the token user for authorization
            request.user = token.user

            # If OAuth authentication is successful, set oauth_consumer_key on
            # request in case we need it later
            request.META['oauth_consumer_key'] = key
            return True
        except KeyError:
            log.exception("Error in OAuth20Authentication.")
            request.user = AnonymousUser()
            return False
        except Exception:
            log.exception("Error in OAuth20Authentication.")
            return False

    def verify_access_token(self, key, request, **kwargs):
        # Import the AccessToken model
        model = settings.OAUTH_ACCESS_TOKEN_MODEL
        try:
            model_parts = model.split('.')
            module_path = '.'.join(model_parts[:-1])
            module = __import__(module_path, globals(), locals(), ['AccessToken'])
            AccessToken = getattr(module, model_parts[-1])
        except ImportError:
            raise OAuthError("Error importing AccessToken model: %s" % model)

        # Check if key is in AccessToken key
        try:
            token = AccessToken.objects.get(token=key)

            # Check if token has expired
            if token.expires < timezone.now():
                raise OAuthError('AccessToken has expired.')
        except AccessToken.DoesNotExist:
            raise OAuthError("AccessToken not found at all.")

        log.info('Valid access')
        return token

class OAuth2ScopedAuthentication(OAuth20Authentication):
    def __init__(self, realm="API", post=None, get=None, patch=None, put=None, delete=None, use_default=True, **kwargs):
        """
            https://tools.ietf.org/html/rfc6749
            get, post, patch and put is desired to be a scope or a list of scopes or None
            if get is None, it will default to post
            if delete is None, it will default to post
            if both patch and put are None, they are all default to post
            if one of patch or put is None, the two will default to the one that is not None

            You can turn this overriding behavior off entirely by specifying use_default=False, but then remember that None means no scope requirement
            is specified for that http method

            the list of scopes should have a logic "or" between them
            e.g. get=("a b","c") for oauth2-toolkit means "GET method requires scope 'a b'('a' and 'b') or scope 'c' "
                 get=(a|b,c) is the corresponding form for oauth2-provider, where a,b,c should be some constants you defined in your settings
                 Note: for oauth2-toolkit, you have to provide a space seperated string of combination of scopes
            you can also specify only one scope(instead of a list), and that scope will the only scope that has permission to the according method
        """
        super(OAuth2ScopedAuthentication, self).__init__(realm)
        self.POST = post
        if use_default:
            self.GET = get or post
            self.DELETE = delete or post
            if not patch and not put:
                self.PATCH = self.PUT = post
            elif not patch or not put:
                self.PATCH = self.PUT = (put or patch)
            else:
                self.PATCH = patch
                self.PUT = put
        else:
            self.GET = get
            self.PUT = put
            self.PATCH = patch
            self.DELETE = delete

    def verify_access_token(self, key, request, **kwargs):
        token = super(OAuth2ScopedAuthentication, self).verify_access_token(key, request, **kwargs)
        if not self.check_scope(token, request):
            raise OAuthError("AccessToken does not meet scope requirement")
        # TODO: Return the actual scope granted if it is different
        return token

    def check_scope(self, token, request):
        http_method = request.method
        if not hasattr(self, http_method):
            raise OAuthError("HTTP method is not recognized")
        required_scopes = getattr(self, http_method)
        # a None scope means always allowed
        if required_scopes is None:
            return True
        model = settings.OAUTH_ACCESS_TOKEN_MODEL
        if model.startswith("provider"):  # oauth2-provider
            from provider.scope import check
            check_method = lambda scope: check(scope, token.scope)
        elif model.startswith("oauth2_provider"):  # oauth toolkit
            check_method = lambda scope: token.allow_scopes(scope.split())
        else:
            raise Exception("oauth provider is not found")
        """
        The required scope is either a string(oauth2 toolkit),
        int(oauth2-provider) or an iterable. If string or int, check if it is
        allowed for our access token otherwise, iterate through the
        required_scopes to see which scopes are allowed
        """
        # for non iterable types
        if isinstance(required_scopes, six.string_types) or \
                isinstance(required_scopes, six.integer_types):
            return [required_scopes] if check_method(required_scopes) else []
        allowed_scopes = []
        try:
            for scope in required_scopes:
                if check_method(scope):
                    allowed_scopes.append(scope)
        except:
            raise Exception('Invalid required scope values')
        else:
            return allowed_scopes
