from django.urls import path

from . import views

app_name = "captura"

urlpatterns = [
    path("", views.panel, name="panel"),
    path("retiros/", views.retiros, name="retiros"),
    path("retiros/nuevo/", views.retiro_nuevo, name="retiro_nuevo"),
    path("retiros/<int:pk>/clasificar/", views.retiro_clasificar, name="retiro_clasificar"),
    path("retiros/<int:pk>/foto/", views.retiro_foto, name="retiro_foto"),
    path("lotes/", views.lotes, name="lotes"),
    path("lotes/nuevo/", views.lote_nuevo, name="lote_nuevo"),
    path("lotes/<int:pk>/", views.lote_editar, name="lote_editar"),
    path("granja/", views.granja, name="granja"),
    path("granja/nuevo/", views.granja_nuevo, name="granja_nuevo"),
    path("granja/<int:pk>/", views.granja_editar, name="granja_editar"),
    path("exportar/retiros.csv", views.exportar_retiros, name="exportar_retiros"),
    path("exportar/lotes.csv", views.exportar_lotes, name="exportar_lotes"),
    path("exportar/granja.csv", views.exportar_granja, name="exportar_granja"),
]
