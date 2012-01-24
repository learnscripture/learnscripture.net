from django.shortcuts import render

from .decorators import require_identity

@require_identity
def learn(request):
    return render(request, 'learnscripture/learn.html')

