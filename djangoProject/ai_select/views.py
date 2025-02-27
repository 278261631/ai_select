from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import authenticate, login


def index_view(request):
    return render(request, 'index.html')
