from django.shortcuts import render

def ingenieria_inicio(request):
    return render(
        request,
        "ingenieria/inicio.html"
    )