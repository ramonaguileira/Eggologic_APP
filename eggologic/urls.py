from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from cuentas import views as cuentas_views

urlpatterns = [
    path("", cuentas_views.inicio, name="inicio"),
    path("ingresar/", auth_views.LoginView.as_view(), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("registrarse/", cuentas_views.registrarse, name="registrarse"),
    path("captura/", include("captura.urls")),
    path("tienda/", include("tienda.urls")),
    path("impacto/", include("impacto.urls")),
    path("registro/", include("guardian.urls")),
    path("admin/", admin.site.urls),
]
