from django import forms
from django.db.models import Q

from cuentas.models import Restaurante

from .models import Lote, RegistroGranja, Retiro

# Los navegadores esperan estos formatos en los campos de fecha nativos.
CAMPO_FECHA = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
CAMPO_FECHA_HORA = forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")
CAMPO_TEXTO = forms.Textarea(attrs={"rows": 2})


class RetiroForm(forms.ModelForm):
    class Meta:
        model = Retiro
        fields = [
            "restaurante",
            "fecha",
            "kg_levantados",
            "kg_impropios",
            "kg_restos_vegetales",
            "kg_residuos_plato",
            "kg_no_ingresa",
            "no_ingresa_estimado",
            "observaciones",
        ]
        widgets = {"fecha": CAMPO_FECHA_HORA, "observaciones": CAMPO_TEXTO}
        help_texts = {
            "kg_impropios": "Clasificación: si todavía no se hizo, dejá estos tres campos vacíos "
            "y completalos en la planta.",
            "kg_no_ingresa": "Opcional: lo que el restaurante tiró a la basura común desde el último "
            "retiro. Lo pide CarboSur para la línea de base.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo restaurantes activos, salvo el que ya tenga el retiro que se está editando.
        self.fields["restaurante"].queryset = Restaurante.objects.filter(
            Q(activo=True) | Q(pk=self.instance.restaurante_id)
        )


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
