from django.urls import path

from . import views

app_name = "guardian"

urlpatterns = [
    path("reportes/", views.reportes, name="reportes"),
    path("reportes/enviar/", views.enviar_al_registro, name="enviar_al_registro"),
]
