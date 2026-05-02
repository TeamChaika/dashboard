import hashlib
import hmac
import subprocess

from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from core.types import HttpRequest
from core.decorators import http_methods
from env import github_webhook_secret, gitea_webhook_secret


@http_methods(['POST'])
@csrf_exempt
def github_webhook(request: HttpRequest):
    client_signature = request.META['HTTP_X_SIGNATURE']
    signature = hmac.new(
        github_webhook_secret,
        request.body,
        hashlib.sha1
    )
    expected_signature = 'sha1=' + signature.hexdigest()
    if not hmac.compare_digest(client_signature, expected_signature):
        return HttpResponseForbidden('Invalid signature header')

    subprocess.run(['./scripts/redeploy.sh'])

    return HttpResponse(status=200)


@http_methods(['POST'])
@csrf_exempt
def gitea_webhook(request: HttpRequest):
    if request.META['CONTENT_TYPE'].lower() != 'application/json':
        return HttpResponse(status=400)
    client_signature = request.META['HTTP_X_GITEA_SIGNATURE']
    signature = hmac.new(
        gitea_webhook_secret,
        request.body,
        hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(client_signature, signature):
        return HttpResponseForbidden('Invalid signature header')

    subprocess.run(['./scripts/redeploy.sh'])

    return HttpResponse(status=200)
