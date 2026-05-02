from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, \
    permission_classes

from core.iiko import iiko_api
from core.types import HttpRequest


@login_required(login_url='/login')
def index(request):
    return render(request, 'index.html')


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_iiko_api_key(request: HttpRequest):
    return Response(iiko_api._get_api_key())
