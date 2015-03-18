from tastypie import fields
from tastypie.api import Api
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.resources import ModelResource
from tastypie_oauth.authentication import OAuth20Authentication, OAuth2Scoped0Authentication

from .models import Poll, Choice


class ChoiceResource(ModelResource):
    poll = fields.ToOneField("polls.api.PollResource", "poll", full=False)
    class Meta:
        queryset = Choice.objects.all()
        resource_name = 'choice'
        authorization = Authorization()
        authentication = OAuth2Scoped0Authentication(
                            post=("read write",),
                            get=("read",),
                            put=("read","write")
                        )


class PollResource(ModelResource):
    choices = fields.ToManyField(ChoiceResource, 'choice_set', full=True)
    class Meta:
        queryset = Poll.objects.all()
        resource_name = 'poll'
        authorization = DjangoAuthorization()
        authentication = OAuth20Authentication()


api = Api(api_name='v1')
api.register(ChoiceResource())
api.register(PollResource())
