from django.shortcuts import render

def logistica_home(request):

    return render(
        request,
        "logistica/index.html"
    )