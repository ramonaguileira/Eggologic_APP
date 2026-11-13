from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("mundo/", views.chacra, name="chacra"),
    path("api/v1/estado/", views.estado, name="estado"),
    path("api/v1/entrar/google/", views.entrar_con_google, name="entrar_con_google"),
    path("api/v1/salir/", views.salir, name="salir"),
    path("api/v1/perfil/", views.guardar_perfil, name="guardar_perfil"),
    path("api/v1/gallinas/adoptar/", views.adoptar, name="adoptar"),
    path("api/v1/gallinas/<int:gallina_id>/nombre/", views.renombrar, name="renombrar"),
    path("api/v1/larvas/dar/", views.dar_larvas, name="dar_larvas"),
    path("api/v1/pedidos/", views.pedir, name="pedir"),
    path("api/v1/huevos/pedir/", views.pedir_huevos, name="pedir_huevos"),
    path("api/v1/recargas/", views.recargar, name="recargar"),
    path("api/v1/levantes/", views.pedir_levante, name="pedir_levante"),
    path("api/v1/pagos/aviso/", views.aviso_de_mercado_pago, name="aviso_de_mercado_pago"),
]
