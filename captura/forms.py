from django import forms
from django.utils import timezone

from cuentas.models import Restaurante

from .models import Bulto, Granja, Lote, RegistroGranja, Retiro

# Los navegadores esperan estos formatos en los campos de fecha nativos.
CAMPO_FECHA = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
CAMPO_TEXTO = forms.Textarea(attrs={"rows": 2})


# En el celular, "capture" abre directo la cámara trasera.
CAMPO_FOTO = forms.FileInput(attrs={"accept": "image/*", "capture": "environment"})


class BultoForm(forms.ModelForm):
    """Un cajón más del retiro: su peso y su foto."""

    class Meta:
        model = Bulto
        fields = ["kg", "foto"]
        widgets = {"foto": CAMPO_FOTO}


class RetiroChoferForm(forms.ModelForm):
    """Lo que carga el chofer al empezar un retiro: el restaurante y el primer bulto. La fecha y
    la ubicación se toman solas."""

    kg = Bulto._meta.get_field("kg").formfield()
    foto = Bulto._meta.get_field("foto").formfield(widget=CAMPO_FOTO)

    class Meta:
        model = Retiro
        fields = ["restaurante", "latitud", "longitud", "precision_m"]
        widgets = {
            "latitud": forms.HiddenInput,
            "longitud": forms.HiddenInput,
            "precision_m": forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["restaurante"].queryset = Restaurante.objects.filter(activo=True)

    def guardar(self, usuario):
        """Un solo retiro por restaurante y por día: si ya hay uno de hoy sin clasificar, el bulto
        se suma a ese."""
        retiro = (
            Retiro.objects.filter(
                restaurante=self.cleaned_data["restaurante"],
                fecha__date=timezone.localdate(),
                kg_impropios=None,
                bultos__isnull=False,
            )
            .distinct()
            .first()
        )
        if retiro is None:
            retiro = self.save(commit=False)
            retiro.registrado_por = usuario
            retiro.kg_levantados = 0
        retiro.en_carga = True
        retiro.save()
        Bulto.objects.create(retiro=retiro, kg=self.cleaned_data["kg"], foto=self.cleaned_data["foto"])
        retiro.sumar_bultos()
        return retiro


class RetiroClasificacionForm(forms.ModelForm):
    """Lo que se completa en la planta al clasificar el residuo."""

    class Meta:
        model = Retiro
        fields = [
            "kg_impropios",
            "kg_restos_vegetales",
            "kg_residuos_plato",
            "kg_no_ingresa",
            "no_ingresa_estimado",
            "observaciones",
        ]
        widgets = {"observaciones": CAMPO_TEXTO}
        help_texts = {
            "kg_impropios": "Si la clasificación suma menos que lo levantado, la diferencia se suma acá "
            "como estimación.",
            "kg_no_ingresa": "Opcional: lo que el restaurante tiró a la basura común desde el último "
            "retiro. Lo pide CarboSur para la línea de base.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ["kg_impropios", "kg_restos_vegetales", "kg_residuos_plato"]:
            self.fields[campo].required = True

    def save(self):
        retiro = super().save(commit=False)
        retiro.cargar_diferencia_a_impropios()
        retiro.save()
        return retiro


class LoteForm(forms.ModelForm):
    """La carga de larvas de la semana."""

    class Meta:
        model = Lote
        fields = ["fecha_inicio", "g_neonatos", "bandejas", "observaciones"]
        widgets = {"fecha_inicio": CAMPO_FECHA, "observaciones": CAMPO_TEXTO}
        help_texts = {"g_neonatos": "Si esta semana no llegaron, poné 0."}


class RegistroGranjaForm(forms.ModelForm):
    class Meta:
        model = RegistroGranja
        fields = ["granja", "desde", "fecha", "huevos", "observaciones"]
        widgets = {"desde": CAMPO_FECHA, "fecha": CAMPO_FECHA, "observaciones": CAMPO_TEXTO}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["granja"].queryset = Granja.objects.filter(activa=True)
        self.fields["granja"].required = True
        self.fields["desde"].required = True
