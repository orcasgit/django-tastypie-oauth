django-tastypie-oauth
=====================

Providing OAuth services for Tastypie APIs

Dependencies
============
This library works with two different OAuth providers, you must install one of them:
- django-oauth-toolkit: https://github.com/evonove/django-oauth-toolkit
- django-oauth2-provider: https://github.com/caffeinehit/django-oauth2-provider

Set up one of these libraries before continuing

Usage
=====

Add `tastypie_oauth` to `INSTALLED_APPS` in Django.
Specify `OAUTH_ACCESS_TOKEN_MODEL` in the Django settings. At this time it can be `'oauth2_provider.models.AccessToken'` for django-oauth-toolkit and `'provider.oauth2.models.AccessToken'` for django-oauth2-provider.
When you create your Tastypie resources, use `OAuth20Authentication` like so:

```python
# mysite/polls/api.py
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from polls.models import Poll, Choice
from tastypie import fields
from tastypie_oauth.authentication import OAuth20Authentication

class ChoiceResource(ModelResource):
    class Meta:
        queryset = Choice.objects.all()
        resource_name = 'choice'
        authorization = DjangoAuthorization()
        authentication = OAuth20Authentication()

class PollResource(ModelResource):
    choices = fields.ToManyField(ChoiceResource, 'choice_set', full=True)
    class Meta:
        queryset = Poll.objects.all()
        resource_name = 'poll'
        authorization = DjangoAuthorization()
        authentication = OAuth20Authentication()
```
