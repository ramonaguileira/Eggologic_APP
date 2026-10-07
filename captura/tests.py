from datetime import date, datetime
from decimal import Decimal
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db.models import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

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


class AccesoPorRolTests(DatosDePrueba):
    """Cada persona de campo ve solo su tarea (pedido de Ramón, 06/10)."""

    def entra(self, rol, nombre_url, *args):
        usuario = Usuario.objects.create_user(username=f"u-{rol}", password="clave-de-prueba-123", rol=rol)
        self.client.force_login(usuario)
        return self.client.get(reverse(nombre_url, args=args)).status_code == 200

    def test_el_chofer_solo_carga_retiros(self):
        retiro = self.crear_retiro("50")
        self.assertTrue(self.entra(Usuario.Rol.CHOFER, "captura:retiro_nuevo"))
        for nombre_url, args in [
            ("captura:panel", []), ("captura:retiros", []), ("captura:lotes", []), ("captura:granja", []),
            ("captura:informe", []), ("captura:exportar_retiros", []), ("captura:retiro_clasificar", [retiro.pk]),
            ("captura:lote_nuevo", []), ("captura:granja_nuevo", []),
        ]:
            self.assertEqual(self.client.get(reverse(nombre_url, args=args)).status_code, 403, nombre_url)

    def test_el_chofer_vuelve_al_formulario_despues_de_guardar(self):
        chofer = Usuario.objects.create_user(username="chofer", password="clave-de-prueba-123", rol=Usuario.Rol.CHOFER)
        self.client.force_login(chofer)
        foto = SimpleUploadedFile("retiro.jpg", b"\xff\xd8\xff foto", content_type="image/jpeg")
        respuesta = self.client.post(
            reverse("captura:retiro_nuevo"), {"restaurante": self.restaurante.pk, "kg_levantados": "20", "foto": foto}
        )
        self.assertRedirects(respuesta, reverse("captura:retiro_nuevo"))

    def test_la_planta_clasifica_y_lleva_lotes_pero_no_la_granja(self):
        retiro = self.crear_retiro("50")
        self.assertTrue(self.entra(Usuario.Rol.PLANTA, "captura:retiro_clasificar", retiro.pk))
        for nombre_url in ["captura:retiros", "captura:lotes", "captura:lote_nuevo"]:
            self.assertEqual(self.client.get(reverse(nombre_url)).status_code, 200, nombre_url)
        for nombre_url in ["captura:granja", "captura:retiro_nuevo", "captura:panel", "captura:informe"]:
            self.assertEqual(self.client.get(reverse(nombre_url)).status_code, 403, nombre_url)

    def test_la_granja_solo_carga_la_granja(self):
        self.assertTrue(self.entra(Usuario.Rol.GRANJA, "captura:granja_nuevo"))
        self.assertEqual(self.client.get(reverse("captura:granja")).status_code, 200)
        for nombre_url in ["captura:retiros", "captura:lotes", "captura:retiro_nuevo", "captura:panel"]:
            self.assertEqual(self.client.get(reverse(nombre_url)).status_code, 403, nombre_url)


class FaseCeroTests(DatosDePrueba):
    """Ajustes de la Fase 0 del plan de datos: exportación filtrada, hora con zona, textos seguros
    para Excel, lotes protegidos e informe con período."""

    def setUp(self):
        super().setUp()
        self.otro = Restaurante.objects.create(nombre="Parrilla", codigo="R-002")
        carbosur = Usuario.objects.create_user(username="carbosur", password="clave-de-prueba-123", rol=Usuario.Rol.CARBOSUR)
        self.client.force_login(carbosur)

    def retiro_el(self, cuando, restaurante=None, **extra):
        """Un retiro en una fecha y hora de Montevideo (AAAA-MM-DD HH:MM)."""
        return Retiro.objects.create(
            restaurante=restaurante or self.restaurante,
            registrado_por=self.operador,
            fecha=timezone.make_aware(datetime.fromisoformat(cuando)),
            kg_levantados=Decimal("10"),
            **extra,
        )

    def exportar(self, nombre_url, **parametros):
        respuesta = self.client.get(reverse(nombre_url), parametros)
        self.assertEqual(respuesta.status_code, 200)
        return respuesta, respuesta.content.decode("utf-8-sig").splitlines()[1:]

    def lote(self, inicio, *retiros):
        lote = Lote.objects.create(registrado_por=self.operador, fecha_inicio=inicio, bandejas=1, g_neonatos=Decimal("1"))
        Retiro.objects.filter(pk__in=[r.pk for r in retiros]).update(lote=lote)
        return lote

    def test_el_informe_acepta_un_periodo(self):
        respuesta = self.client.get(reverse("captura:informe"), {"desde": "2026-09-01", "hasta": "2026-09-30"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["desde"], date(2026, 9, 1))
        self.assertContains(respuesta, "no verificado por un tercero")
        self.assertContains(respuesta, "?desde=2026-09-01&amp;hasta=2026-09-30")

    def test_exporta_retiros_por_periodo_y_restaurante(self):
        self.retiro_el("2026-08-31 23:00")
        ultimo_de_septiembre = self.retiro_el("2026-09-30 22:30")  # ya es 1 de octubre en UTC
        self.retiro_el("2026-09-15 11:00", restaurante=self.otro)
        self.retiro_el("2026-10-01 09:00")

        respuesta, filas = self.exportar("captura:exportar_retiros", desde="2026-09-01", hasta="2026-09-30", restaurante="R-001")

        self.assertEqual([fila.split(";")[0] for fila in filas], [str(ultimo_de_septiembre.pk)])
        self.assertIn(";2026-09-30 22:30-03:00;R-001;", filas[0])
        self.assertIn('filename="retiros_2026-09-01_2026-09-30_R-001.csv"', respuesta["Content-Disposition"])

    def test_sin_filtros_sale_todo_el_historial(self):
        self.retiro_el("2026-08-31 23:00")
        self.retiro_el("2026-09-15 11:00", restaurante=self.otro)
        respuesta, filas = self.exportar("captura:exportar_retiros")
        self.assertEqual(len(filas), 2)
        self.assertIn('filename="retiros.csv"', respuesta["Content-Disposition"])

    def test_el_codigo_del_restaurante_no_puede_inyectar_el_nombre_del_archivo(self):
        self.retiro_el("2026-09-15 11:00")
        respuesta, filas = self.exportar("captura:exportar_retiros", restaurante='R-001";x')
        self.assertIn('filename="retiros_R-001x.csv"', respuesta["Content-Disposition"])
        self.assertEqual(filas, [])

    def test_exporta_los_lotes_donde_entro_residuo_del_restaurante(self):
        con_r001 = self.lote(date(2026, 9, 2), self.retiro_el("2026-09-01 11:00"), self.retiro_el("2026-09-01 12:00", restaurante=self.otro))
        self.lote(date(2026, 9, 9), self.retiro_el("2026-09-08 11:00", restaurante=self.otro))
        _, filas = self.exportar("captura:exportar_lotes", restaurante="R-001")
        self.assertEqual([fila.split(";")[0] for fila in filas], [str(con_r001.pk)])

    def test_la_granja_se_filtra_solo_por_fecha(self):
        RegistroGranja.objects.create(registrado_por=self.operador, fecha=date(2026, 9, 5), huevos=100, kg_larvas=Decimal("2"))
        RegistroGranja.objects.create(registrado_por=self.operador, fecha=date(2026, 10, 5), huevos=90, kg_larvas=Decimal("2"))
        respuesta, filas = self.exportar("captura:exportar_granja", desde="2026-09-01", hasta="2026-09-30", restaurante="R-001")
        self.assertEqual(filas, ["2026-09-05;100;2,00;;"])
        self.assertIn('filename="granja_2026-09-01_2026-09-30.csv"', respuesta["Content-Disposition"])

    def test_un_texto_que_parece_formula_sale_escapado(self):
        self.retiro_el("2026-09-15 11:00", observaciones='=HYPERLINK("http://ejemplo.com")')
        _, filas = self.exportar("captura:exportar_retiros")
        self.assertTrue(filas[0].endswith(';"\'=HYPERLINK(""http://ejemplo.com"")"'), filas[0])

    def test_un_lote_con_retiros_o_granja_no_se_puede_borrar(self):
        con_retiro = self.lote(date(2026, 9, 2), self.retiro_el("2026-09-01 11:00"))
        con_granja = self.lote(date(2026, 9, 9))
        RegistroGranja.objects.create(registrado_por=self.operador, fecha=date(2026, 9, 20), huevos=100, kg_larvas=Decimal("2"), lote=con_granja)
        vacio = self.lote(date(2026, 9, 16))
        for lote in (con_retiro, con_granja):
            with self.assertRaises(ProtectedError):
                lote.delete()
        vacio.delete()
        self.assertEqual(Lote.objects.count(), 2)


class CargarDemoTests(TestCase):
    @override_settings(DEBUG=True)
    def test_crea_todos_los_usuarios_de_prueba(self):
        call_command("cargar_demo", password="clave-de-prueba-123", stdout=StringIO())
        usuarios = set(Usuario.objects.values_list("username", flat=True))
        self.assertLessEqual({"admin", "operador", "carbosur", "cliente", "restaurante"}, usuarios)
