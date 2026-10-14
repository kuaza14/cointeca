from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def logistica_home(request):

    return render(
        request,
        "logistica/index.html"
    )
