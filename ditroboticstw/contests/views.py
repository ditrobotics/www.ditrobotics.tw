from django.shortcuts import render


def contests(request):
    return render(
        request,
        'contests/index.html'
    )
