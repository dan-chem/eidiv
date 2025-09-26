# einsatz/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("neu", views.einsatz_neu, name="einsatz_neu"),
    path("<int:pk>", views.einsatz_detail, name="einsatz_detail"),
    path("htmx/loeschwasser/add", views.htmx_add_loeschwasser, name="htmx_add_loeschwasser"),
    path("htmx/einsatzmittel/add", views.htmx_add_einsatzmittel, name="htmx_add_einsatzmittel"),
]
