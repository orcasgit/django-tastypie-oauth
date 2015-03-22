from provider.constants import READ, WRITE, READ_WRITE
from tastypie import fields
from tastypie.api import Api
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.resources import ModelResource
from tastypie_oauth.authentication import (
    OAuth20Authentication,
    OAuth2ScopedAuthentication
)

from .models import Poll, Choice


class ToolkitScopedAuthentication(OAuth2ScopedAuthentication):
    def __init__(self):
        return super(ToolkitScopedAuthentication, self).__init__(
            post=("read write",),
            get=("read",),
            put=("read","write")
        )


class ProviderScopedAuthentication(OAuth2ScopedAuthentication):
    def __init__(self):
        return super(ProviderScopedAuthentication, self).__init__(
            post=(READ_WRITE,),
            get=(READ,),
            put=(READ,WRITE)
        )


class ChoiceResourceMeta:
    queryset = Choice.objects.all()
    authorization = Authorization()


class ChoiceResourceOAuthToolkit(ModelResource):
    poll = fields.ToOneField("polls.api.PollResourceOAuthToolkit", "poll", full=False)
    class Meta(ChoiceResourceMeta):
        resource_name = 'choice_toolkit'
        authentication = OAuth20Authentication()


class ChoiceResourceOAuth2Provider(ModelResource):
    poll = fields.ToOneField("polls.api.PollResourceOAuth2Provider", "poll", full=False)
    class Meta(ChoiceResourceMeta):
        resource_name = 'choice_provider'
        authentication = OAuth20Authentication()


class ScopedChoiceResourceOAuthToolkit(ModelResource):
    poll = fields.ToOneField("polls.api.ScopedPollResourceOAuthToolkit", "poll", full=False)
    class Meta(ChoiceResourceMeta):
        resource_name = 'scoped_choice_toolkit'
        authentication = ToolkitScopedAuthentication()


class ScopedChoiceResourceOAuth2Provider(ModelResource):
    poll = fields.ToOneField("polls.api.ScopedPollResourceOAuth2Provider", "poll", full=False)
    class Meta(ChoiceResourceMeta):
        resource_name = 'scoped_choice_provider'
        authentication = ProviderScopedAuthentication()


class PollResourceMeta:
    queryset = Poll.objects.all()
    authorization = DjangoAuthorization()


class PollResourceOAuthToolkit(ModelResource):
    choices = fields.ToManyField(ChoiceResourceOAuthToolkit, 'choice_set', full=True)
    class Meta(PollResourceMeta):
        resource_name = 'poll_toolkit'
        authentication = OAuth20Authentication()


class PollResourceOAuth2Provider(ModelResource):
    choices = fields.ToManyField(ChoiceResourceOAuth2Provider, 'choice_set', full=True)
    class Meta(PollResourceMeta):
        resource_name = 'poll_provider'
        authentication = OAuth20Authentication()


class ScopedPollResourceOAuthToolkit(ModelResource):
    choices = fields.ToManyField(ScopedChoiceResourceOAuthToolkit, 'choice_set', full=True)
    class Meta(PollResourceMeta):
        resource_name = 'scoped_poll_toolkit'
        authentication = ToolkitScopedAuthentication()


class ScopedPollResourceOAuth2Provider(ModelResource):
    choices = fields.ToManyField(ScopedChoiceResourceOAuth2Provider, 'choice_set', full=True)
    class Meta(PollResourceMeta):
        resource_name = 'scoped_poll_provider'
        authentication = ProviderScopedAuthentication()


api = Api(api_name='v1')
api.register(ChoiceResourceOAuthToolkit())
api.register(ChoiceResourceOAuth2Provider())
api.register(ScopedChoiceResourceOAuthToolkit())
api.register(ScopedChoiceResourceOAuth2Provider())
api.register(PollResourceOAuthToolkit())
api.register(PollResourceOAuth2Provider())
api.register(ScopedPollResourceOAuthToolkit())
api.register(ScopedPollResourceOAuth2Provider())
