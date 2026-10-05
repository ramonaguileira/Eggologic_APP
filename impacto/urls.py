from django.urls import path

from . import views

app_name = "impacto"

urlpatterns = [
    path("", views.mi_impacto, name="mi_impacto"),
]
