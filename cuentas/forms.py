from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import Cliente, Usuario


class RegistroClienteForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150)
    email = forms.EmailField(label="Email")
    telefono = forms.CharField(label="Teléfono", max_length=40)
    direccion = forms.CharField(label="Dirección de entrega", max_length=200)

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ["username", "first_name", "email"]

    @transaction.atomic
    def save(self):
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.CLIENTE
        usuario.save()
        Cliente.objects.create(
            usuario=usuario,
            telefono=self.cleaned_data["telefono"],
            direccion=self.cleaned_data["direccion"],
        )
        return usuario
