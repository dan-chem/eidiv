# einsatz/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.einsatz_liste, name="einsatz_liste"),
    path("neu", views.einsatz_neu, name="einsatz_neu"),
    path("<int:pk>", views.einsatz_detail, name="einsatz_detail"),
    path("<int:pk>/pdf", views.einsatz_pdf, name="einsatz_pdf"),

    path("stichwort/<int:pk>/kategorie", views.stichwort_kategorie_api, name="einsatz_stichwort_kategorie"),
    path("stichwort/options", views.stichwort_options, name="einsatz_stichwort_options"),

    # HTMX add-row
    path("htmx/loeschwasser/add", views.htmx_add_loeschwasser, name="einsatz_htmx_add_loeschwasser"),
    path("htmx/einsatzmittel/add", views.htmx_add_einsatzmittel, name="einsatz_htmx_add_einsatzmittel"),
    path("htmx/fahrzeug/add", views.htmx_add_fahrzeug, name="einsatz_htmx_add_fahrzeug"),
    path("htmx/abroll/add", views.htmx_add_abroll, name="einsatz_htmx_add_abroll"),
    path("htmx/anhaenger/add", views.htmx_add_anhaenger, name="einsatz_htmx_add_anhaenger"),
    path("htmx/ofw/add", views.htmx_add_ortsfeuerwehr, name="einsatz_htmx_add_ofw"),
    path("htmx/zusatzstelle/add", views.htmx_add_zusatzstelle, name="einsatz_htmx_add_zusatzstelle"),
    path("htmx/teilnahme/add", views.htmx_add_teilnahme, name="einsatz_htmx_add_teilnahme"),
    
]
