from django import forms
from django.db.models import Q
from django.utils import timezone

from cuentas.models import Restaurante

from .models import Bulto, Lote, RegistroGranja, Retiro

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
    retiros = forms.ModelMultipleChoiceField(
        queryset=Retiro.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label="Retiros que entran al lote",
        help_text="Solo aparecen los retiros ya clasificados que no están en otro lote.",
    )

    class Meta:
        model = Lote
        fields = [
            "fecha_inicio",
            "bandejas",
            "g_neonatos",
            "fecha_cosecha",
            "kg_larvas",
            "kg_frass",
            "observaciones",
        ]
        widgets = {
            "fecha_inicio": CAMPO_FECHA,
            "fecha_cosecha": CAMPO_FECHA,
            "observaciones": CAMPO_TEXTO,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        libres_o_de_este_lote = Q(lote__isnull=True)
        if self.instance.pk:
            libres_o_de_este_lote |= Q(lote=self.instance)
            self.fields["retiros"].initial = self.instance.retiros.all()
        self.fields["retiros"].queryset = (
            Retiro.objects.filter(libres_o_de_este_lote)
            .exclude(kg_impropios=None)
            .exclude(kg_restos_vegetales=None)
            .exclude(kg_residuos_plato=None)
            .select_related("restaurante")
        )

    def save(self):
        # Los retiros apuntan al lote, así que primero hay que guardar el lote.
        lote = super().save()
        elegidos = self.cleaned_data["retiros"]
        lote.retiros.exclude(pk__in=elegidos).update(lote=None)
        elegidos.update(lote=lote)
        return lote


class RegistroGranjaForm(forms.ModelForm):
    class Meta:
        model = RegistroGranja
        fields = ["fecha", "huevos", "kg_larvas", "lote", "observaciones"]
        widgets = {"fecha": CAMPO_FECHA, "observaciones": CAMPO_TEXTO}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lote"].queryset = Lote.objects.filter(fecha_cosecha__isnull=False)
