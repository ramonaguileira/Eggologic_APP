from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from cuentas import views as cuentas_views
from cuentas.forms import LoginForm
from tienda.views import pedidos_admin

urlpatterns = [
    path("", cuentas_views.inicio, name="inicio"),
    path("ingresar/", auth_views.LoginView.as_view(form_class=LoginForm), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("registrarse/", cuentas_views.registrarse, name="registrarse"),
    path("captura/", include("captura.urls")),
    path("tienda/", include("tienda.urls")),
    path("impacto/", include("impacto.urls")),
    path("registro/", include("guardian.urls")),
    path("admin/", admin.site.urls),

    path("primera-entrega/", cuentas_views.primera_entrega, name="primera_entrega"),
    # Password recovery URLs
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        email_template_name="registration/password_reset_email.html",
        success_url="/password-reset/done/",
    ), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html",
    ), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/password_reset_confirm.html",
        success_url="/password-reset/complete/",
    ), name="password_reset_confirm"),
    path("password-reset/complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html",
    ), name="password_reset_complete"),
]
