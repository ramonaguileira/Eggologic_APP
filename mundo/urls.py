from django.urls import path

from . import views

app_name = "mundo"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("recargas/<int:recarga_id>/", views.recarga_resolver, name="recarga_resolver"),
    path("pedidos/<int:pedido_id>/entrega/", views.pedido_entrega, name="pedido_entrega"),
    path("levantes/", views.levantes, name="levantes"),
    path("levantes/<int:levante_id>/retirar/", views.levante_retirar, name="levante_retirar"),
    path("exportar/movimientos.csv", views.exportar_movimientos, name="exportar_movimientos"),
    path("exportar/gallinas.csv", views.exportar_gallinas, name="exportar_gallinas"),
    path("exportar/levantes.csv", views.exportar_levantes, name="exportar_levantes"),
]
