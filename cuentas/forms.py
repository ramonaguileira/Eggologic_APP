from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from .models import Cliente, Usuario


class RegistroClienteForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150)
    email = forms.EmailField(label="Email")
    telefono = forms.CharField(label="Teléfono", max_length=40)
    direccion = forms.CharField(label="Dirección de entrega", max_length=200)

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ["first_name", "email"]

    @transaction.atomic
    def save(self):
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.CLIENTE
        usuario.username = usuario.email
        usuario.save()
        Cliente.objects.create(
            usuario=usuario,
            telefono=self.cleaned_data["telefono"],
            direccion=self.cleaned_data["direccion"],
        )
        return usuario


class LoginForm(AuthenticationForm):
    """Formulario de login que usa email en lugar de username."""
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))
    password = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput)

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def get_user(self):
        return self.user_cache
