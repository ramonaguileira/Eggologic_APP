from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from cuentas.models import Restaurante, Usuario

from .forms import LoteForm, RegistroGranjaForm
from .models import Archivo, Lote, RegistroGranja, Retiro


class DatosDePrueba(TestCase):
    def setUp(self):
        self.operador = Usuario.objects.create_user(
            username="operador", password="clave-de-prueba-123", rol=Usuario.Rol.OPERADOR
        )
        self.restaurante = Restaurante.objects.create(nombre="La Huerta", codigo="R-001")

    def crear_retiro(self, kg_levantados="50", clasificacion=None, **extra):
        """clasificacion = (impropios, vegetales, plato) o None si todavía no se clasificó."""
        impropios, vegetales, plato = clasificacion or (None, None, None)
        return Retiro.objects.create(
            restaurante=self.restaurante,
            registrado_por=self.operador,
            kg_levantados=Decimal(kg_levantados),
            kg_impropios=impropios,
            kg_restos_vegetales=vegetales,
            kg_residuos_plato=plato,
            **extra,
        )


class RetiroTests(DatosDePrueba):
    def test_kg_organicos_suma_vegetales_y_plato(self):
        retiro = self.crear_retiro("50", (Decimal("2"), Decimal("30"), Decimal("18")))
        self.assertTrue(retiro.clasificado)
        self.assertEqual(retiro.kg_organicos, Decimal("48"))

    def test_sin_clasificar_no_tiene_kg_organicos(self):
        retiro = self.crear_retiro("50")
        self.assertFalse(retiro.clasificado)
        self.assertIsNone(retiro.kg_organicos)

    def test_clasificacion_incompleta_es_invalida(self):
        retiro = self.crear_retiro("50")
        retiro.kg_impropios = Decimal("2")
        with self.assertRaises(ValidationError):
            retiro.full_clean()

    def test_clasificacion_no_puede_superar_lo_levantado(self):
        retiro = self.crear_retiro("50")
        retiro.kg_impropios, retiro.kg_restos_vegetales, retiro.kg_residuos_plato = (
            Decimal("5"), Decimal("30"), Decimal("20"),
        )
        with self.assertRaises(ValidationError):
            retiro.full_clean()


class LoteTests(DatosDePrueba):
    def test_rendimiento_es_kg_de_larva_cada_100_kg_de_residuo(self):
        lote = Lote.objects.create(
            registrado_por=self.operador, bandejas=7, g_neonatos=Decimal("10"),
            fecha_cosecha=date.today(), kg_larvas=Decimal("15"), kg_frass=Decimal("40"),
        )
        self.crear_retiro("45", (Decimal("5"), Decimal("25"), Decimal("15")), lote=lote)
        self.crear_retiro("62", (Decimal("2"), Decimal("40"), Decimal("20")), lote=lote)
        self.assertEqual(lote.kg_residuo, Decimal("100"))
        self.assertEqual(lote.rendimiento, Decimal("15"))

    def test_cosecha_incompleta_es_invalida(self):
        lote = Lote(registrado_por=self.operador, bandejas=3, g_neonatos=Decimal("5"), kg_larvas=Decimal("4"))
        with self.assertRaises(ValidationError):
            lote.full_clean()

    def test_cosecha_no_puede_ser_anterior_al_inicio(self):
        lote = Lote(
            registrado_por=self.operador, bandejas=3, g_neonatos=Decimal("5"),
            fecha_inicio=date(2026, 10, 10), fecha_cosecha=date(2026, 10, 1),
            kg_larvas=Decimal("4"), kg_frass=Decimal("9"),
        )
        with self.assertRaises(ValidationError):
            lote.full_clean()


class LoteFormTests(DatosDePrueba):
    def datos(self, retiros):
        return {
            "fecha_inicio": "2026-10-05",
            "bandejas": "4",
            "g_neonatos": "8",
            "retiros": [r.pk for r in retiros],
        }

    def test_solo_ofrece_retiros_clasificados_y_libres(self):
        libre = self.crear_retiro("40", (Decimal("1"), Decimal("20"), Decimal("19")))
        sin_clasificar = self.crear_retiro("30")
        otro_lote = Lote.objects.create(registrado_por=self.operador, bandejas=1, g_neonatos=Decimal("2"))
        ocupado = self.crear_retiro("20", (Decimal("0"), Decimal("10"), Decimal("10")), lote=otro_lote)

        ofrecidos = set(LoteForm().fields["retiros"].queryset)

        self.assertIn(libre, ofrecidos)
        self.assertNotIn(sin_clasificar, ofrecidos)
        self.assertNotIn(ocupado, ofrecidos)

    def test_guardar_asigna_y_libera_retiros(self):
        primero = self.crear_retiro("40", (Decimal("1"), Decimal("20"), Decimal("19")))
        segundo = self.crear_retiro("30", (Decimal("1"), Decimal("15"), Decimal("14")))

        form = LoteForm(self.datos([primero, segundo]), instance=Lote(registrado_por=self.operador))
        self.assertTrue(form.is_valid(), form.errors)
        lote = form.save()
        self.assertEqual(set(lote.retiros.all()), {primero, segundo})

        form = LoteForm(self.datos([primero]), instance=lote)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        segundo.refresh_from_db()
        self.assertIsNone(segundo.lote)


class RegistroGranjaTests(DatosDePrueba):
    def test_un_solo_registro_por_dia(self):
        RegistroGranja.objects.create(
            registrado_por=self.operador, fecha=date(2026, 10, 5), huevos=180, kg_larvas=Decimal("3")
        )
        form = RegistroGranjaForm(
            {"fecha": "2026-10-05", "huevos": "175", "kg_larvas": "2.5"},
            instance=RegistroGranja(registrado_por=self.operador),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("fecha", form.errors)


class VistasTests(DatosDePrueba):
    def foto(self):
        return SimpleUploadedFile("tacho.jpg", b"\xff\xd8\xff contenido de prueba", content_type="image/jpeg")

    def test_chofer_carga_retiro_con_foto_y_ubicacion(self):
        self.client.force_login(self.operador)
        respuesta = self.client.post(
            reverse("captura:retiro_nuevo"),
            {
                "restaurante": self.restaurante.pk,
                "kg_levantados": "42.5",
                "foto": self.foto(),
                "latitud": "-34.909700",
                "longitud": "-54.865300",
                "precision_m": "12",
            },
        )
        self.assertRedirects(respuesta, reverse("captura:retiros"))
        retiro = Retiro.objects.get()
        self.assertEqual(retiro.kg_levantados, Decimal("42.5"))
        self.assertEqual(retiro.registrado_por, self.operador)
        self.assertEqual(retiro.latitud, Decimal("-34.909700"))
        self.assertTrue(retiro.foto.name.endswith(".jpg"))
        self.assertFalse(retiro.clasificado)

    def test_retiro_sin_foto_no_se_guarda(self):
        self.client.force_login(self.operador)
        respuesta = self.client.post(
            reverse("captura:retiro_nuevo"), {"restaurante": self.restaurante.pk, "kg_levantados": "20"}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Retiro.objects.exists())

    def test_retiro_sin_ubicacion_se_guarda_igual(self):
        self.client.force_login(self.operador)
        self.client.post(
            reverse("captura:retiro_nuevo"),
            {"restaurante": self.restaurante.pk, "kg_levantados": "20", "foto": self.foto()},
        )
        self.assertIsNone(Retiro.objects.get().latitud)

    def test_planta_clasifica_un_retiro(self):
        retiro = self.crear_retiro("50")
        self.client.force_login(self.operador)
        respuesta = self.client.post(
            reverse("captura:retiro_clasificar", args=[retiro.pk]),
            {"kg_impropios": "2", "kg_restos_vegetales": "30", "kg_residuos_plato": "18"},
        )
        self.assertRedirects(respuesta, reverse("captura:retiros"))
        retiro.refresh_from_db()
        self.assertEqual(retiro.kg_organicos, Decimal("48"))

    def test_clasificacion_imposible_no_se_guarda(self):
        retiro = self.crear_retiro("10")
        self.client.force_login(self.operador)
        respuesta = self.client.post(
            reverse("captura:retiro_clasificar", args=[retiro.pk]),
            {"kg_impropios": "1", "kg_restos_vegetales": "8", "kg_residuos_plato": "5"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "La clasificación suma más kg que lo levantado.")
        retiro.refresh_from_db()
        self.assertFalse(retiro.clasificado)

    def test_la_foto_solo_la_ve_quien_accede_a_los_datos(self):
        retiro = self.crear_retiro("50", foto=self.foto())
        cliente = Usuario.objects.create_user(
            username="cliente", password="clave-de-prueba-123", rol=Usuario.Rol.CLIENTE
        )
        url = reverse("captura:retiro_foto", args=[retiro.pk])

        self.client.force_login(cliente)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_login(self.operador)
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(b"".join(respuesta.streaming_content), b"\xff\xd8\xff contenido de prueba")
        # En Render gratis no hay disco: la foto vive en la base.
        self.assertTrue(Archivo.objects.filter(nombre=retiro.foto.name).exists())

    def test_carbosur_exporta_retiros_para_excel(self):
        self.crear_retiro("42.5", (Decimal("1.5"), Decimal("25"), Decimal("16")))
        carbosur = Usuario.objects.create_user(
            username="carbosur", password="clave-de-prueba-123", rol=Usuario.Rol.CARBOSUR
        )
        self.client.force_login(carbosur)

        respuesta = self.client.get(reverse("captura:exportar_retiros"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "text/csv; charset=utf-8")
        lineas = respuesta.content.decode("utf-8-sig").splitlines()
        self.assertTrue(lineas[0].startswith("retiro;fecha;restaurante_codigo"))
        self.assertIn(";R-001;La Huerta;42,50;1,50;25,00;16,00;", lineas[1])

    def test_panel_muestra_totales(self):
        self.crear_retiro("50", (Decimal("5"), Decimal("30"), Decimal("15")))
        self.client.force_login(self.operador)
        respuesta = self.client.get(reverse("captura:panel"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["retiros"]["organicos"], Decimal("45"))
        self.assertEqual(respuesta.context["retiros"]["pct_impropios"], Decimal("10"))


class InformeVistaTests(DatosDePrueba):
    def test_carbosur_ve_el_informe_con_codigo_y_nombre(self):
        self.crear_retiro("50", (Decimal("2"), Decimal("30"), Decimal("18")))
        carbosur = Usuario.objects.create_user(username="carbosur", password="clave-de-prueba-123", rol=Usuario.Rol.CARBOSUR)
        self.client.force_login(carbosur)
        respuesta = self.client.get(reverse("captura:informe"))
        self.assertContains(respuesta, "R-001 · La Huerta")

    def test_un_cliente_no_entra(self):
        cliente = Usuario.objects.create_user(username="cliente", password="clave-de-prueba-123", rol=Usuario.Rol.CLIENTE)
        self.client.force_login(cliente)
        self.assertEqual(self.client.get(reverse("captura:informe")).status_code, 403)
