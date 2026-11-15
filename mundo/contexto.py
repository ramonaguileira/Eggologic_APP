from django.conf import settings


def eggo_world(request):
    """Para que el menú muestre los enlaces de Eggo World solo cuando está prendido."""
    return {"eggo_world_activo": settings.EGGO_WORLD_ACTIVO}
