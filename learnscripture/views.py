from django.shortcuts import render

def learn(request):
    return render(request, 'learnscripture/learn.html')

