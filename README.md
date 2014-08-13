django-tastypie-oauth
=====================

[![Build Status](https://travis-ci.org/orcasgit/django-tastypie-oauth.svg?branch=master)](https://travis-ci.org/orcasgit/django-tastypie-oauth) [![Coverage Status](https://coveralls.io/repos/orcasgit/django-tastypie-oauth/badge.png?branch=master)](https://coveralls.io/r/orcasgit/django-tastypie-oauth?branch=master) [![Requirements Status](https://requires.io/github/orcasgit/django-tastypie-oauth/requirements.png?branch=master)](https://requires.io/github/orcasgit/django-tastypie-oauth/requirements/?branch=master)

Providing OAuth services for Tastypie APIs

Dependencies
============
This library works with two different OAuth providers, you must install one of them:
- django-oauth-toolkit: https://github.com/evonove/django-oauth-toolkit
- django-oauth2-provider: https://github.com/caffeinehit/django-oauth2-provider

Set up one of these libraries before continuing

Usage
=====

1. Add `tastypie_oauth` to `INSTALLED_APPS` in Django.
2. Specify `OAUTH_ACCESS_TOKEN_MODEL` in the Django settings. At this time it can be `'oauth2_provider.models.AccessToken'` for django-oauth-toolkit and `'provider.oauth2.models.AccessToken'` for django-oauth2-provider.
3. When you create your Tastypie resources, use `OAuth20Authentication` like so:

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
4. After authorizing the user and gaining an access token, you can use the API almost as before with just one minor change. You must add a `oauth_consumer_key` GET or POST parameter with the access token as the value, or put the access token in "Authorization" header.
