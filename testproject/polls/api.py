from tastypie import fields
from tastypie.api import Api
from tastypie.authorization import Authorization
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


class ChoiceResourceOAuthToolkit(ModelResource):
    poll = fields.ToOneField("polls.api.PollResourceOAuthToolkit", "poll", full=False)
    class Meta:
        resource_name = 'choice_toolkit'
        queryset = Choice.objects.all()
        authorization = Authorization()
        authentication = OAuth20Authentication()


class ScopedChoiceResourceOAuthToolkit(ModelResource):
    poll = fields.ToOneField("polls.api.ScopedPollResourceOAuthToolkit", "poll", full=False)
    class Meta:
        resource_name = 'scoped_choice_toolkit'
        queryset = Choice.objects.all()
        authorization = Authorization()
        authentication = ToolkitScopedAuthentication()


class PollResourceOAuthToolkit(ModelResource):
    choices = fields.ToManyField(ChoiceResourceOAuthToolkit, 'choice_set', full=True)
    class Meta:
        resource_name = 'poll_toolkit'
        queryset = Poll.objects.all()
        authorization = Authorization()
        authentication = OAuth20Authentication()


class ScopedPollResourceOAuthToolkit(ModelResource):
    choices = fields.ToManyField(ScopedChoiceResourceOAuthToolkit, 'choice_set', full=True)
    class Meta:
        resource_name = 'scoped_poll_toolkit'
        queryset = Poll.objects.all()
        authorization = Authorization()
        authentication = ToolkitScopedAuthentication()


api = Api(api_name='v1')
api.register(ChoiceResourceOAuthToolkit())
api.register(ScopedChoiceResourceOAuthToolkit())
api.register(PollResourceOAuthToolkit())
api.register(ScopedPollResourceOAuthToolkit())
