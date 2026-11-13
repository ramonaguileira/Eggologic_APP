"""Dibuja los sprites de Eggo World que no vinieron en el paquete de Claude Design.

Cada dibujo es una grilla de letras; cada letra es un color de la paleta (paleta.css).
Para cambiar un dibujo se edita la grilla y se corre:  python eggo-world/arte/dibujar.py
Necesita Pillow (pip install pillow). Los PNG que genera quedan guardados en el repo, así que
no hace falta correrlo para usar la app.
"""

from pathlib import Path

from PIL import Image

AQUI = Path(__file__).parent

PALETA = {
    "k": "#0c2a1f", "B": "#143f2c", "G": "#1d583b", "P": "#2f7d4c", "b": "#58a95c", "h": "#9ad37a",
    "W": "#ffffff", "c": "#f6f0dc", "p": "#d6cba6", "n": "#a89c78",
    "Y": "#ffdf6b", "y": "#f5b921", "a": "#d98414",
    "r": "#c8472f", "t": "#7a5230", "u": "#452c1b",
}


def imagen(grilla, cambios=None):
    filas = [fila for fila in grilla.strip("\n").split("\n")]
    ancho = len(filas[0])
    assert all(len(fila) == ancho for fila in filas), [len(fila) for fila in filas]
    dibujo = Image.new("RGBA", (ancho, len(filas)), (0, 0, 0, 0))
    for y, fila in enumerate(filas):
        for x, letra in enumerate(fila):
            letra = (cambios or {}).get(letra, letra)
            if letra != ".":
                color = PALETA[letra].lstrip("#")
                dibujo.putpixel((x, y), tuple(int(color[i : i + 2], 16) for i in (0, 2, 4)) + (255,))
    return dibujo


def tira(nombre, cuadros, cambios=None):
    """Guarda varios cuadros del mismo tamaño en fila, para animar con CSS."""
    dibujos = [imagen(cuadro, cambios) for cuadro in cuadros]
    ancho, alto = dibujos[0].size
    assert all(dibujo.size == (ancho, alto) for dibujo in dibujos), nombre
    hoja = Image.new("RGBA", (ancho * len(dibujos), alto), (0, 0, 0, 0))
    for numero, dibujo in enumerate(dibujos):
        hoja.paste(dibujo, (numero * ancho, 0))
    hoja.save(AQUI / f"{nombre}.png")


# --- Gallina: 6 cuadros de 16×16 -----------------------------------------------------------
# 0 quieta · 1 y 2 caminando · 3 picoteando · 4 echada · 5 dormida

CUERPO = """
.........kk.....
........krrkk...
........krrrrk..
.......kWWWWk...
.......kWWkWkk..
.k.....kWWWWyyk.
kWk....kWWWrrk..
kWWk..kWWWWrk...
kWWWkkWWWWWWk...
kcWWWWWWWWWWk...
.kcWWpppWWWck...
.kccWWpppWcck...
..kcccccccck....
...kkkkkkkk.....
"""
QUIETA = CUERPO + """.....a...a......
....aa..aa......
"""
PASO_1 = CUERPO + """......a.a.......
.....aa.aa......
"""
PASO_2 = CUERPO + """....a.....a.....
...aa.....aa....
"""
PICOTEA = """
................
................
................
.k..............
kWk.............
kWWk..kkkkk.....
kWWWkkWWWWWk....
kcWWWWWWWWWWkk..
.kcWWpppWWWWrrk.
.kccWWpppWWWWrk.
..kcccccccWWkWk.
...kkkkkkkkWWWyk
.....a...a.kWyk.
....aa..aa..kk..
................
................
"""
ECHADA = """
................
................
""" + CUERPO.strip("\n") + "\n"
DORMIDA = ECHADA.replace(".......kWWkWkk..", ".......kWWWWkk..").replace(
    ".k.....kWWWWyyk.", ".k.....kWnnWyyk."
)
GALLINA = [QUIETA, PASO_1, PASO_2, PICOTEA, ECHADA, DORMIDA]

tira("gallina-blanca", GALLINA)
tira("gallina-colorada", GALLINA, {"W": "a", "c": "t", "p": "t"})
# La "negra" es marrón oscuro: el verde oscuro se perdía sobre el pasto.
tira("gallina-negra", GALLINA, {"W": "u", "c": "u", "p": "t"})

# --- Balde de residuos: vacío y lleno ------------------------------------------------------

BALDE = """
...kkkkkkkkkk...
..kpccccccccnk..
..kkkkkkkkkkkk..
...kbPPPPPPBk...
...kbbPPPPPBk...
...kbbPPPPPBk...
...kbPPPPPPBk...
...kbPPPPPPBk...
....kbPPPPBk....
....kbPPPPBk....
....kPPPPPBk....
.....kkkkkk.....
"""
tira("balde", [
    "................\n................\n................\n................\n" + BALDE.strip("\n"),
    "................\n.....kk..kk.....\n....kbhkkark.kk.\n...ktabhbayrkyk.\n" + BALDE.strip("\n"),
])

# --- Bichos de la chacra -------------------------------------------------------------------

tira("pajarito", [
    """
...kk.......
..kaak......
..kaaak.kkk.
.kkttttktktk
ktttttttttyy
.kkcccccck..
...kkkkkk...
............
""",
    """
............
........kkk.
.kkkkkkktktk
ktttttttttyy
.kkaaaccck..
..kaaakkk...
...kkk......
............
""",
])

tira("caracol", [
    """
....kkkk....
...kaaaak.k.
..kataatakk.
..kaattaakk.
..kataatakck
.kkaaaaakcck
kcccccccccck
.kkkkkkkkkk.
""",
    """
............
....kkkk...k
...kaaaak.kk
..kataatakk.
..kaattaakck
.kkataatkcck
kcccccccccck
.kkkkkkkkkk.
""",
])

tira("bichito", [
    """
.k..k.
kkkkkk
krrkrk
krrrrk
k.kk.k
""",
    """
k....k
.kkkk.
krrkrk
krrrrk
.k..k.
""",
])

# --- Cosas de la chacra --------------------------------------------------------------------

tira("huevo", ["""
..kkk..
.kWcck.
kWcccpk
kWcccpk
kcccppk
kccpppk
.kpppk.
..kkk..
"""])

tira("comedero", ["""
..kkkkkkkkkkkk..
.kyaYyayYayyaYk.
kttttttttttttttk
.kuttttttttttuk.
..kkkkkkkkkkkk..
"""])

tira("bebedero", ["""
.kkkkkkkkkk.
kWWWccccccpk
knppppppppnk
.knnnnnnnnk.
..kkkkkkkk..
"""])

tira("arbol", ["""
.......kkkkkk.......
.....kkhhhhbbkk.....
....khhhhbbbbbbk....
...khhhbbbbbbbPPk...
..khhbbbbhhbbbPPPk..
..khbbbbhhbbbbPPPk..
.khbbbbbbbbbPPPPPPk.
.kbbbhhbbbbbPPPPPBk.
.kbbhhbbbbPPPPPPBBk.
.kbbbbbbbPPPPPPBBBk.
..kbbPPbbPPPPPBBBk..
..kPPPPPPPPPPBBBBk..
...kkPPPPPPBBBBkk...
.....kkkkttkkkk.....
........kttk........
........kttk........
........ktuk........
........ktuk........
.......kttuuk.......
......kkkkkkkk......
"""])

tira("mata", ["""
..b...b.
.bb..bP.
bPb.bPPb
"""])

tira("flor", ["""
.kyk.
kyWyk
.kyk.
..b..
.bb..
..b..
"""])

tira("nube", ["""
......WWWW..........
....WWWWWWWW..WWW...
..WWWWWWWWWWWWWWWW..
.WWWWWWWWWWWWWWWWWW.
WWWWWWWWWWWWWWWWWWWW
.pppppppppppppppppp.
"""])

tira("sol", ["""
...yyyyyy....
..yYYYYYYy...
.yYYaaaaYYy..
yYYaYYYYaYYy.
yYaYYaaYYaYy.
yYaYaYYaYaYy.
yYaYaYYYYaYy.
yYaYYaaaaYYy.
yYYaYYYYYYYy.
.yYYaaaaaYy..
..yYYYYYYy...
...yyyyyy....
"""])

tira("luna", ["""
...cccc..
..ccccpc.
.ccc..cpc
ccc....cc
ccc......
ccc......
ccc....cc
.ccc..cpc
..ccccpc.
...cccc..
"""])

tira("corazon", ["""
.kk.kk.
krrkrrk
krrrrrk
.krrrk.
..krk..
...k...
"""])

tira("insignia", ["""
...kkkkk...
..kyyyyyk..
.kyYYYYYak.
kyYYaaaYYak
kyYaYYYaYak
kyYaYaaYYak
kyYaYYYYYak
.kyYaaaaak.
..kyyyyak..
..krkkkrk..
.krrk.krrk.
.krk...krk.
"""])

# --- Ícono de la app: el huevo de los Eggos sobre el verde de la marca -----------------------

huevo = Image.open(AQUI / "eggo.png").convert("RGBA")
for lado in (192, 512):
    escala = lado // 40
    grande = huevo.resize((huevo.width * escala, huevo.height * escala), Image.NEAREST)
    icono = Image.new("RGBA", (lado, lado), "#1d583b")
    icono.paste(grande, ((lado - grande.width) // 2, (lado - grande.height) // 2), grande)
    icono.save(AQUI / f"icono-{lado}.png")

print("Listo: sprites en", AQUI)
