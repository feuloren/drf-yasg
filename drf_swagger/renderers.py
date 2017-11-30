from django.shortcuts import render, resolve_url
from rest_framework.renderers import BaseRenderer
from rest_framework.utils import json

from .app_settings import swagger_settings, redoc_settings
from .codec import OpenAPICodecJson, VALIDATORS, OpenAPICodecYaml


class _SpecRenderer(BaseRenderer):
    charset = None
    validators = ['flex', 'ssv']
    codec_class = None

    @classmethod
    def with_validators(cls, validators):
        assert all(vld in VALIDATORS for vld in validators), "allowed validators are" + ", ".join(VALIDATORS)
        return type(cls.__name__, (cls,), {'validators': validators})

    def render(self, data, media_type=None, renderer_context=None):
        assert self.codec_class, "must override codec_class"
        codec = self.codec_class(self.validators)
        return codec.encode(data)


class OpenAPIRenderer(_SpecRenderer):
    media_type = 'application/openapi+json'
    format = 'openapi'
    codec_class = OpenAPICodecJson


class SwaggerJSONRenderer(_SpecRenderer):
    media_type = 'application/json'
    format = '.json'
    codec_class = OpenAPICodecJson


class SwaggerYAMLRenderer(_SpecRenderer):
    media_type = 'application/yaml'
    format = '.yaml'
    codec_class = OpenAPICodecYaml


class _UIRenderer(BaseRenderer):
    media_type = 'text/html'
    charset = 'utf-8'
    template = ''

    def render(self, data, accepted_media_type=None, renderer_context=None):
        self.set_context(renderer_context, data)
        return render(
            renderer_context['request'],
            self.template,
            renderer_context
        )

    def set_context(self, renderer_context, data):
        renderer_context['title'] = data.title
        renderer_context['version'] = data.version
        renderer_context['swagger_settings'] = json.dumps(self.get_swagger_ui_settings())
        renderer_context['redoc_settings'] = json.dumps(self.get_redoc_settings())
        renderer_context['USE_SESSION_AUTH'] = swagger_settings.USE_SESSION_AUTH
        renderer_context.update(self.get_auth_urls())

    def get_auth_urls(self):
        urls = {}
        if swagger_settings.LOGIN_URL is not None:
            urls['LOGIN_URL'] = resolve_url(swagger_settings.LOGIN_URL)
        if swagger_settings.LOGOUT_URL is not None:
            urls['LOGOUT_URL'] = resolve_url(swagger_settings.LOGOUT_URL)

        return urls

    def get_swagger_ui_settings(self):
        data = {
            'operationsSorter': swagger_settings.OPERATIONS_SORTER,
            'tagsSorter': swagger_settings.TAGS_SORTER,
            'docExpansion': swagger_settings.DOC_EXPANSION,
            'deepLinking': swagger_settings.DEEP_LINKING,
            'showExtensions': swagger_settings.SHOW_EXTENSIONS,
            'defaultModelRendering': swagger_settings.DEFAULT_MODEL_RENDERING,
            'defaultModelExpandDepth': swagger_settings.DEFAULT_MODEL_DEPTH,
        }
        data = {k: v for k, v in data.items() if v is not None}
        if swagger_settings.VALIDATOR_URL != '':
            data['validatorUrl'] = swagger_settings.VALIDATOR_URL

        return data

    def get_redoc_settings(self):
        data = {
            'lazyRendering': redoc_settings.LAZY_RENDERING,
            'hideHostname': redoc_settings.HIDE_HOSTNAME,
            'expandResponses': redoc_settings.EXPAND_RESPONSES,
            'pathInMiddle': redoc_settings.PATH_IN_MIDDLE,
        }

        return data


class SwaggerUIRenderer(_UIRenderer):
    template = 'drf-swagger/swagger-ui.html'
    format = 'swagger'


class ReDocRenderer(_UIRenderer):
    template = 'drf-swagger/redoc.html'
    format = 'redoc'