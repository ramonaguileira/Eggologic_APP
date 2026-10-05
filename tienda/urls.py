from django.urls import path

from . import views

app_name = "tienda"

urlpatterns = [
    path("", views.tienda, name="tienda"),
    path("mis-pedidos/", views.mis_pedidos, name="mis_pedidos"),
]
