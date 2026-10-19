from django.urls import path

from . import views

app_name = "tienda"

urlpatterns = [
    path("", views.tienda, name="tienda"),
    path("pedido/<int:pedido_id>/entregado/", views.pedido_entregado, name="pedido_entregado"),
    path("pedidos/", views.pedidos_admin, name="pedidos_admin"),
    path("pedido/<int:pedido_id>/", views.pedido_admin_detalle, name="pedido_admin_detalle"),
    path("pedido/nuevo-admin/", views.pedido_nuevo_admin, name="pedido_nuevo_admin"),
    path("mis-pedidos/", views.mis_pedidos, name="mis_pedidos"),
]
