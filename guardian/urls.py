from django.urls import path

from . import views

app_name = "guardian"

urlpatterns = [
    path("reportes/", views.reportes, name="reportes"),
]
