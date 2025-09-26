from django.shortcuts import render
from django.http import JsonResponse
from .models import Mitglied

def index(request):
    return render(request, 'index.html')

def api_mitglied_agt(request, pk: int):
    try:
        m = Mitglied.objects.get(pk=pk)
        return JsonResponse({"agt": bool(m.agt)})
    except Mitglied.DoesNotExist:
        return JsonResponse({"agt": False})