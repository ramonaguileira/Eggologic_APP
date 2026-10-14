from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from .models import Cliente, Usuario


class RegistroClienteForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150)
    email = forms.EmailField(label="Email")

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ["first_name", "email"]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email
    @transaction.atomic
    def save(self):
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.CLIENTE
        usuario.username = usuario.email
        usuario.save()
        Cliente.objects.create(
            usuario=usuario,
        )
        return usuario


class FirstDeliveryForm(forms.Form):
    """Formulario para recolectar datos de entrega en el primer pedido."""
    telefono = forms.CharField(label="Teléfono", max_length=40)
    direccion = forms.CharField(label="Dirección de entrega", max_length=200)


class LoginForm(AuthenticationForm):
    """Formulario de login que acepta email o username."""
    username = forms.CharField(label="Email o Usuario", widget=forms.TextInput(attrs={"autofocus": True}))
    password = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput)

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            # Try to authenticate with the provided username (which could be email or actual username)
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                # If authentication fails, check if the input looks like an email
                # and try to find the user by email, then authenticate with their actual username
                import re
                email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
                if email_pattern.match(username):
                    try:
                        # Find user by email
                        usuario = Usuario.objects.get(email__iexact=username)
                        # Authenticate with the user's username field
                        self.user_cache = authenticate(
                            self.request, username=usuario.username, password=password
                        )
                    except Usuario.DoesNotExist:
                        pass

                if self.user_cache is None:
                    raise self.get_invalid_login_error()
                else:
                    self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def get_user(self):
        return self.user_cache
