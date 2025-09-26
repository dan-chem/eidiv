# dienst/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dienst_liste, name="dienst_liste"),
    path("neu", views.dienst_neu, name="dienst_neu"),
    path("<int:pk>", views.dienst_detail, name="dienst_detail"),
    path("<int:pk>/pdf", views.dienst_pdf, name="dienst_pdf"),
    path("htmx/fahrzeug/add", views.htmx_add_fahrzeug, name="dienst_htmx_add_fahrzeug"),
    path("htmx/abroll/add", views.htmx_add_abroll, name="dienst_htmx_add_abroll"),  # neu
    path("htmx/anhaenger/add", views.htmx_add_anhaenger, name="dienst_htmx_add_anhaenger"),
    path("htmx/teilnahme/add", views.htmx_add_teilnahme, name="dienst_htmx_add_teilnahme"),
]
