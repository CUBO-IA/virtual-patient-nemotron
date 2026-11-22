"""
Generador de las 10 ilustraciones de pacientes salvadoreños
y capas para animación sincronizada con audio (Web Audio API).
Estilo: Caricatura 2D plana, cartoon moderno, contornos gruesos oscuros,
paleta cálida, proporciones de busto a 736x736.
"""

import os
import math
from PIL import Image, ImageDraw

OUTPUT_DIR = "frontend/public/pacientes"
CAPAS_DIR = os.path.join(OUTPUT_DIR, "capas")
PUBLIC_DIR = "frontend/public"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CAPAS_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

# Renderizamos al doble (1472x1472) y reducimos con LANCZOS a 736x736 para antialiasing perfecto
SCALE = 2
WIDTH = 736 * SCALE
HEIGHT = 736 * SCALE
OUTLINE_COLOR = (30, 22, 20, 255)  # Contorno grueso oscuro
OUTLINE_W = 7 * SCALE

# 10 Perfiles salvadoreños (5 M, 5 F) con rasgos, ropa y accesorios acordes a casos clínicos
PATIENTS = [
    {
        "id": "paciente_01",
        "nombre": "Kevin",
        "sexo": "M",
        "edad": 22,
        "skin": (218, 158, 108, 255),
        "skin_shadow": (195, 136, 88, 255),
        "hair_color": (34, 25, 22, 255),
        "hair_type": "wavy_short",
        "clothes_color": (78, 107, 74, 255),   # Verde olivo
        "collar_color": (56, 78, 53, 255),
        "accesorio": "mascarilla_cuello",       # Mascarilla médica en el cuello (fiebre/dengue)
        "facial_hair": None,
        "glasses": False,
        "earrings": None,
    },
    {
        "id": "paciente_02",
        "nombre": "Valeria",
        "sexo": "F",
        "edad": 24,
        "skin": (228, 168, 122, 255),
        "skin_shadow": (205, 146, 102, 255),
        "hair_color": (45, 28, 22, 255),
        "hair_type": "long_wavy",
        "clothes_color": (214, 92, 68, 255),   # Terracota / coral
        "collar_color": (185, 75, 54, 255),
        "accesorio": "pulsera_medica",
        "facial_hair": None,
        "glasses": False,
        "earrings": "gold_hoops",
    },
    {
        "id": "paciente_03",
        "nombre": "Mauricio",
        "sexo": "M",
        "edad": 46,
        "skin": (198, 134, 86, 255),
        "skin_shadow": (175, 116, 70, 255),
        "hair_color": (32, 24, 22, 255),
        "hair_type": "short_temples_grey",
        "clothes_color": (43, 62, 106, 255),   # Polo azul marino
        "collar_color": (30, 44, 76, 255),
        "accesorio": "polo_buttons",
        "facial_hair": "mustache",             # Bigote salvadoreño
        "glasses": False,
        "earrings": None,
    },
    {
        "id": "paciente_04",
        "nombre": "Rebeca",
        "sexo": "F",
        "edad": 43,
        "skin": (216, 154, 108, 255),
        "skin_shadow": (192, 132, 88, 255),
        "hair_color": (40, 24, 19, 255),
        "hair_type": "updo_bun",
        "clothes_color": (124, 45, 68, 255),   # Blusa vino tinto
        "collar_color": (100, 34, 52, 255),
        "accesorio": None,
        "facial_hair": None,
        "glasses": False,
        "earrings": "pearl_studs",
    },
    {
        "id": "paciente_05",
        "nombre": "Don Chepe",
        "sexo": "M",
        "edad": 68,
        "skin": (194, 130, 83, 255),
        "skin_shadow": (170, 110, 68, 255),
        "hair_color": (220, 224, 230, 255),    # Cabello canoso blanco
        "hair_type": "receding_white",
        "clothes_color": (212, 196, 168, 255), # Guayabera lino beige
        "collar_color": (186, 170, 142, 255),
        "accesorio": "guayabera_lines",
        "facial_hair": None,
        "glasses": True,                       # Lentes clásicos
        "earrings": None,
    },
    {
        "id": "paciente_06",
        "nombre": "Doña Tina",
        "sexo": "F",
        "edad": 71,
        "skin": (222, 164, 120, 255),
        "skin_shadow": (198, 142, 100, 255),
        "hair_color": (230, 232, 238, 255),    # Cabello blanco plateado
        "hair_type": "grandma_bun",
        "clothes_color": (142, 126, 172, 255), # Cárdigan lila
        "collar_color": (118, 102, 148, 255),
        "accesorio": None,
        "facial_hair": None,
        "glasses": True,                       # Lentes redondos
        "earrings": "pearl_studs",
    },
    {
        "id": "paciente_07",
        "nombre": "Rodrigo",
        "sexo": "M",
        "edad": 31,
        "skin": (206, 142, 94, 255),
        "skin_shadow": (182, 122, 76, 255),
        "hair_color": (28, 20, 18, 255),
        "hair_type": "textured_fade",
        "clothes_color": (217, 130, 43, 255),  # Camisa mostaza / ocre
        "collar_color": (185, 108, 32, 255),
        "accesorio": None,
        "facial_hair": "stubble_chin",
        "glasses": False,
        "earrings": None,
    },
    {
        "id": "paciente_08",
        "nombre": "Marlene",
        "sexo": "F",
        "edad": 27,
        "skin": (229, 169, 125, 255),
        "skin_shadow": (205, 147, 105, 255),
        "hair_color": (30, 21, 19, 255),
        "hair_type": "medium_bob",
        "clothes_color": (224, 122, 139, 255), # Rosa maternal
        "collar_color": (196, 98, 114, 255),
        "accesorio": "pulsera_hospital",        # Pulsera maternidad
        "facial_hair": None,
        "glasses": False,
        "earrings": "gold_hoops",
    },
    {
        "id": "paciente_09",
        "nombre": "Mateo",
        "sexo": "M",
        "edad": 14,
        "skin": (213, 150, 102, 255),
        "skin_shadow": (190, 130, 84, 255),
        "hair_color": (26, 20, 18, 255),
        "hair_type": "messy_teen",
        "clothes_color": (197, 48, 48, 255),   # Sudadera roja
        "collar_color": (240, 240, 245, 255),
        "accesorio": "hoodie_strings",
        "facial_hair": None,
        "glasses": False,
        "earrings": None,
    },
    {
        "id": "paciente_10",
        "nombre": "Sofía",
        "sexo": "F",
        "edad": 13,
        "skin": (226, 168, 124, 255),
        "skin_shadow": (202, 146, 104, 255),
        "hair_color": (32, 22, 18, 255),
        "hair_type": "pigtails_ribbon",
        "clothes_color": (56, 189, 248, 255),  # Camiseta celeste
        "collar_color": (251, 191, 36, 255),
        "accesorio": "ribbons_yellow",
        "facial_hair": None,
        "glasses": False,
        "earrings": None,
    },
]

def draw_thick_line(draw, points, fill, width):
    """Dibuja línea antialiased con terminaciones redondeadas."""
    draw.line(points, fill=fill, width=width, joint="curve")

def draw_eye_open(draw, cx, cy, rx, ry, reflect_side="right"):
    # Esclerótica crema
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(255, 249, 237, 255), outline=OUTLINE_COLOR, width=OUTLINE_W)
    # Pupila negra grande
    prx = int(rx * 0.72)
    pry = int(ry * 0.76)
    draw.ellipse([cx - prx, cy - pry + int(2 * SCALE), cx + prx, cy + pry + int(2 * SCALE)], fill=(28, 20, 18, 255))
    # Reflejo blanco redondo
    rf_r = int(rx * 0.24)
    rf_x = cx + int(rx * 0.22) if reflect_side == "right" else cx - int(rx * 0.22)
    rf_y = cy - int(ry * 0.25)
    draw.ellipse([rf_x - rf_r, rf_y - rf_r, rf_x + rf_r, rf_y + rf_r], fill=(255, 255, 255, 255))
    # Segundo reflejo pequeño
    rf_r2 = int(rf_r * 0.5)
    rf_x2 = cx - int(rx * 0.2) if reflect_side == "right" else cx + int(rx * 0.2)
    rf_y2 = cy + int(ry * 0.22)
    draw.ellipse([rf_x2 - rf_r2, rf_y2 - rf_r2, rf_x2 + rf_r2, rf_y2 + rf_r2], fill=(255, 255, 255, 210))

def draw_eye_closed(draw, cx, cy, rx):
    """Ojo cerrado para parpadeo: arco alegre con pestañita."""
    points = [
        (cx - rx, cy + int(4 * SCALE)),
        (cx - int(rx * 0.5), cy - int(10 * SCALE)),
        (cx, cy - int(12 * SCALE)),
        (cx + int(rx * 0.5), cy - int(10 * SCALE)),
        (cx + rx, cy + int(4 * SCALE)),
    ]
    draw.line(points, fill=OUTLINE_COLOR, width=OUTLINE_W + int(2 * SCALE), joint="curve")

def draw_eye_dolor(draw, cx, cy, rx, ry, reflect_side="right"):
    """Ojo entrecerrado con ceja fruncida de molestia."""
    # Ojo más apretado
    draw_eye_open(draw, cx, cy, rx, int(ry * 0.75), reflect_side)

def draw_mouth_cerrada(draw, cx, cy, mw):
    points = [
        (cx - mw, cy - int(3 * SCALE)),
        (cx - int(mw * 0.4), cy + int(6 * SCALE)),
        (cx, cy + int(7 * SCALE)),
        (cx + int(mw * 0.4), cy + int(6 * SCALE)),
        (cx + mw, cy - int(2 * SCALE)),
    ]
    draw.line(points, fill=OUTLINE_COLOR, width=OUTLINE_W, joint="curve")
    # Hoyuelos sutiles
    draw.line([(cx - mw - int(2 * SCALE), cy - int(6 * SCALE)), (cx - mw + int(2 * SCALE), cy)], fill=OUTLINE_COLOR, width=OUTLINE_W - int(2*SCALE))
    draw.line([(cx + mw + int(2 * SCALE), cy - int(6 * SCALE)), (cx + mw - int(2 * SCALE), cy)], fill=OUTLINE_COLOR, width=OUTLINE_W - int(2*SCALE))

def draw_mouth_entreabierta(draw, cx, cy, mw):
    # Labios ligeramente abiertos mostrando dientes
    mh = int(14 * SCALE)
    draw.ellipse([cx - mw, cy - mh, cx + mw, cy + mh], fill=(255, 249, 237, 255), outline=OUTLINE_COLOR, width=OUTLINE_W)
    draw.line([(cx - mw + int(4 * SCALE), cy), (cx + mw - int(4 * SCALE), cy)], fill=(120, 40, 45, 255), width=int(3 * SCALE))

def draw_mouth_abierta(draw, cx, cy, mw):
    # Boca abierta al hablar: interior oscuro, dientes arriba, lengua abajo
    mh = int(26 * SCALE)
    # Fondo boca
    draw.chord([cx - mw, cy - mh, cx + mw, cy + mh], start=0, end=180, fill=(90, 20, 25, 255), outline=OUTLINE_COLOR, width=OUTLINE_W)
    # Dientes superiores
    draw.rectangle([cx - int(mw * 0.7), cy - int(2 * SCALE), cx + int(mw * 0.7), cy + int(8 * SCALE)], fill=(255, 250, 240, 255))
    # Lengua
    draw.ellipse([cx - int(mw * 0.5), cy + int(8 * SCALE), cx + int(mw * 0.5), cy + mh], fill=(226, 115, 135, 255))
    # Borde exterior
    draw.arc([cx - mw, cy - mh, cx + mw, cy + mh], start=0, end=180, fill=OUTLINE_COLOR, width=OUTLINE_W)
    draw.line([(cx - mw, cy), (cx + mw, cy)], fill=OUTLINE_COLOR, width=OUTLINE_W)

def draw_mouth_o(draw, cx, cy, mw):
    # Boca redonda en 'O'
    ow = int(mw * 0.65)
    oh = int(28 * SCALE)
    draw.ellipse([cx - ow, cy - int(12 * SCALE), cx + ow, cy + oh], fill=(85, 20, 25, 255), outline=OUTLINE_COLOR, width=OUTLINE_W)
    draw.ellipse([cx - int(ow * 0.6), cy + int(6 * SCALE), cx + int(ow * 0.6), cy + oh - int(4 * SCALE)], fill=(226, 115, 135, 255))

def draw_mouth_dolor(draw, cx, cy, mw):
    # Boca con gesto sutil de molestia / tirantez
    points = [
        (cx - mw, cy + int(4 * SCALE)),
        (cx - int(mw * 0.3), cy - int(3 * SCALE)),
        (cx, cy - int(2 * SCALE)),
        (cx + int(mw * 0.3), cy + int(1 * SCALE)),
        (cx + mw, cy + int(6 * SCALE)),
    ]
    draw.line(points, fill=OUTLINE_COLOR, width=OUTLINE_W, joint="curve")


def render_patient(p):
    pid = p["id"]
    p_capas_dir = os.path.join(CAPAS_DIR, pid)
    os.makedirs(p_capas_dir, exist_ok=True)

    # Medidas antropométricas ajustadas por edad y sexo
    is_kid = p["edad"] < 16
    is_elder = p["edad"] > 60
    head_cy = int(320 * SCALE) if not is_kid else int(340 * SCALE)
    head_cx = WIDTH // 2
    head_rx = int(145 * SCALE) if not is_kid else int(155 * SCALE)
    head_ry = int(170 * SCALE) if not is_kid else int(160 * SCALE)
    eye_y = head_cy - int(10 * SCALE)
    eye_dist = int(72 * SCALE)
    eye_rx = int(28 * SCALE) if not is_elder else int(24 * SCALE)
    eye_ry = int(34 * SCALE) if not is_elder else int(28 * SCALE)
    nose_y = head_cy + int(45 * SCALE)
    mouth_y = head_cy + int(95 * SCALE)
    mouth_w = int(38 * SCALE)

    # ----------------------------------------------------
    # 1. CAPA BASE: Torso, Ropa, Cuello, Cabeza, Orejas, Rubor, Pelo Trasero y Accesorios
    # ----------------------------------------------------
    img_base = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_base = ImageDraw.Draw(img_base)

    # Pelo trasero si es largo o moño
    if p["hair_type"] in ("long_wavy", "medium_bob", "pigtails_ribbon", "updo_bun", "grandma_bun"):
        hc = p["hair_color"]
        if p["hair_type"] == "long_wavy":
            draw_base.ellipse([head_cx - head_rx - int(35 * SCALE), head_cy - int(50 * SCALE), head_cx + head_rx + int(35 * SCALE), head_cy + int(240 * SCALE)], fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
        elif p["hair_type"] == "updo_bun":
            # Moño alto ordenado
            draw_base.ellipse([head_cx - int(70 * SCALE), head_cy - head_ry - int(60 * SCALE), head_cx + int(70 * SCALE), head_cy - head_ry + int(40 * SCALE)], fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
        elif p["hair_type"] == "grandma_bun":
            # Moño abuela plateado
            draw_base.ellipse([head_cx - int(65 * SCALE), head_cy - head_ry - int(50 * SCALE), head_cx + int(65 * SCALE), head_cy - head_ry + int(35 * SCALE)], fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
        elif p["hair_type"] == "pigtails_ribbon":
            # Coletas a los lados
            draw_base.ellipse([head_cx - head_rx - int(50 * SCALE), head_cy + int(20 * SCALE), head_cx - head_rx + int(10 * SCALE), head_cy + int(140 * SCALE)], fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
            draw_base.ellipse([head_cx + head_rx - int(10 * SCALE), head_cy + int(20 * SCALE), head_cx + head_rx + int(50 * SCALE), head_cy + int(140 * SCALE)], fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
            # Lazos amarillos
            draw_base.rectangle([head_cx - head_rx - int(25 * SCALE), head_cy + int(30 * SCALE), head_cx - head_rx + int(5 * SCALE), head_cy + int(50 * SCALE)], fill=(251, 191, 36, 255), outline=OUTLINE_COLOR, width=int(4 * SCALE))
            draw_base.rectangle([head_cx + head_rx - int(5 * SCALE), head_cy + int(30 * SCALE), head_cx + head_rx + int(25 * SCALE), head_cy + int(50 * SCALE)], fill=(251, 191, 36, 255), outline=OUTLINE_COLOR, width=int(4 * SCALE))

    # Torso y hombros
    sh_top = head_cy + int(130 * SCALE)
    draw_base.polygon([
        (int(80 * SCALE), HEIGHT),
        (int(110 * SCALE), sh_top + int(120 * SCALE)),
        (head_cx - int(100 * SCALE), sh_top),
        (head_cx + int(100 * SCALE), sh_top),
        (WIDTH - int(110 * SCALE), sh_top + int(120 * SCALE)),
        (WIDTH - int(80 * SCALE), HEIGHT),
    ], fill=p["clothes_color"], outline=OUTLINE_COLOR)

    # Cuello
    neck_w = int(58 * SCALE) if not is_kid else int(50 * SCALE)
    draw_base.rectangle([head_cx - neck_w, head_cy + int(80 * SCALE), head_cx + neck_w, sh_top + int(40 * SCALE)], fill=p["skin"], outline=OUTLINE_COLOR, width=OUTLINE_W)
    # Sombra del cuello bajo la barbilla
    draw_base.chord([head_cx - neck_w, head_cy + int(70 * SCALE), head_cx + neck_w, head_cy + int(140 * SCALE)], start=0, end=180, fill=p["skin_shadow"])

    # Cuello de ropa
    draw_base.chord([head_cx - int(75 * SCALE), sh_top - int(30 * SCALE), head_cx + int(75 * SCALE), sh_top + int(60 * SCALE)], start=0, end=180, fill=p["collar_color"], outline=OUTLINE_COLOR, width=OUTLINE_W)

    # Detalles de ropa / accesorios en torso
    if p["accesorio"] == "mascarilla_cuello":
        # Mascarilla quirúrgica celeste bajada al cuello
        draw_base.rounded_rectangle([head_cx - int(65 * SCALE), sh_top - int(15 * SCALE), head_cx + int(65 * SCALE), sh_top + int(45 * SCALE)], radius=int(14 * SCALE), fill=(165, 216, 230, 255), outline=OUTLINE_COLOR, width=OUTLINE_W)
        draw_base.line([(head_cx - int(60 * SCALE), sh_top + int(15 * SCALE)), (head_cx + int(60 * SCALE), sh_top + int(15 * SCALE))], fill=(130, 190, 210, 255), width=int(3 * SCALE))
    elif p["accesorio"] == "pulsera_medica" or p["accesorio"] == "pulsera_hospital":
        band_col = (56, 189, 248, 255) if p["accesorio"] == "pulsera_medica" else (255, 255, 255, 255)
        draw_base.rounded_rectangle([int(125 * SCALE), HEIGHT - int(80 * SCALE), int(175 * SCALE), HEIGHT - int(35 * SCALE)], radius=int(8 * SCALE), fill=band_col, outline=OUTLINE_COLOR, width=OUTLINE_W)
        if p["accesorio"] == "pulsera_hospital":
            draw_base.line([(int(130 * SCALE), HEIGHT - int(60 * SCALE)), (int(170 * SCALE), HEIGHT - int(60 * SCALE))], fill=(244, 114, 182, 255), width=int(5 * SCALE))
    elif p["accesorio"] == "polo_buttons":
        # Botones de la camisa polo
        draw_base.ellipse([head_cx - int(6 * SCALE), sh_top + int(70 * SCALE), head_cx + int(6 * SCALE), sh_top + int(82 * SCALE)], fill=(230, 230, 235, 255), outline=OUTLINE_COLOR, width=int(2 * SCALE))
        draw_base.ellipse([head_cx - int(6 * SCALE), sh_top + int(105 * SCALE), head_cx + int(6 * SCALE), sh_top + int(117 * SCALE)], fill=(230, 230, 235, 255), outline=OUTLINE_COLOR, width=int(2 * SCALE))
    elif p["accesorio"] == "guayabera_lines":
        # Alforzas de guayabera
        for offset in (-int(45 * SCALE), -int(35 * SCALE), int(35 * SCALE), int(45 * SCALE)):
            draw_base.line([(head_cx + offset, sh_top + int(50 * SCALE)), (head_cx + offset, HEIGHT)], fill=OUTLINE_COLOR, width=int(3 * SCALE))

    # Orejas
    ear_w = int(32 * SCALE)
    ear_h = int(48 * SCALE)
    ear_y = head_cy - int(10 * SCALE)
    # Oreja izquierda
    draw_base.ellipse([head_cx - head_rx - ear_w + int(8 * SCALE), ear_y - ear_h, head_cx - head_rx + int(16 * SCALE), ear_y + ear_h], fill=p["skin"], outline=OUTLINE_COLOR, width=OUTLINE_W)
    draw_base.arc([head_cx - head_rx - int(14 * SCALE), ear_y - int(20 * SCALE), head_cx - head_rx + int(4 * SCALE), ear_y + int(20 * SCALE)], start=70, end=290, fill=OUTLINE_COLOR, width=int(4 * SCALE))
    # Oreja derecha
    draw_base.ellipse([head_cx + head_rx - int(16 * SCALE), ear_y - ear_h, head_cx + head_rx + ear_w - int(8 * SCALE), ear_y + ear_h], fill=p["skin"], outline=OUTLINE_COLOR, width=OUTLINE_W)
    draw_base.arc([head_cx + head_rx - int(4 * SCALE), ear_y - int(20 * SCALE), head_cx + head_rx + int(14 * SCALE), ear_y + int(20 * SCALE)], start=-110, end=110, fill=OUTLINE_COLOR, width=int(4 * SCALE))

    # Aretes
    if p["earrings"] == "gold_hoops":
        draw_base.ellipse([head_cx - head_rx - int(12 * SCALE), ear_y + int(36 * SCALE), head_cx - head_rx + int(4 * SCALE), ear_y + int(58 * SCALE)], outline=(234, 179, 8, 255), width=int(5 * SCALE))
        draw_base.ellipse([head_cx + head_rx - int(4 * SCALE), ear_y + int(36 * SCALE), head_cx + head_rx + int(12 * SCALE), ear_y + int(58 * SCALE)], outline=(234, 179, 8, 255), width=int(5 * SCALE))
    elif p["earrings"] == "pearl_studs":
        draw_base.ellipse([head_cx - head_rx - int(4 * SCALE), ear_y + int(32 * SCALE), head_cx - head_rx + int(8 * SCALE), ear_y + int(44 * SCALE)], fill=(248, 250, 252, 255), outline=OUTLINE_COLOR, width=int(2 * SCALE))
        draw_base.ellipse([head_cx + head_rx - int(8 * SCALE), ear_y + int(32 * SCALE), head_cx + head_rx + int(4 * SCALE), ear_y + int(44 * SCALE)], fill=(248, 250, 252, 255), outline=OUTLINE_COLOR, width=int(2 * SCALE))

    # Cabeza (rostro)
    draw_base.ellipse([head_cx - head_rx, head_cy - head_ry, head_cx + head_rx, head_cy + head_ry], fill=p["skin"], outline=OUTLINE_COLOR, width=OUTLINE_W)

    # Mejillas con rubor rosado en trazos cortos (especificado en el prompt)
    blush_color = (248, 113, 113, 130)
    blush_y = head_cy + int(42 * SCALE)
    # Mejilla izq
    draw_base.line([(head_cx - int(92 * SCALE), blush_y), (head_cx - int(72 * SCALE), blush_y - int(6 * SCALE))], fill=blush_color, width=int(5 * SCALE))
    draw_base.line([(head_cx - int(88 * SCALE), blush_y + int(10 * SCALE)), (head_cx - int(68 * SCALE), blush_y + int(4 * SCALE))], fill=blush_color, width=int(5 * SCALE))
    # Mejilla der
    draw_base.line([(head_cx + int(72 * SCALE), blush_y - int(6 * SCALE)), (head_cx + int(92 * SCALE), blush_y)], fill=blush_color, width=int(5 * SCALE))
    draw_base.line([(head_cx + int(68 * SCALE), blush_y + int(4 * SCALE)), (head_cx + int(88 * SCALE), blush_y + int(10 * SCALE))], fill=blush_color, width=int(5 * SCALE))

    # Nariz: curva pequeña
    draw_base.arc([head_cx - int(14 * SCALE), nose_y - int(18 * SCALE), head_cx + int(14 * SCALE), nose_y + int(8 * SCALE)], start=20, end=200, fill=OUTLINE_COLOR, width=OUTLINE_W - int(1 * SCALE))

    # Barba / bigote si corresponde
    if p["facial_hair"] == "mustache":
        # Bigote recortado bajo la nariz
        draw_base.polygon([
            (head_cx - int(38 * SCALE), mouth_y - int(14 * SCALE)),
            (head_cx - int(18 * SCALE), mouth_y - int(24 * SCALE)),
            (head_cx, mouth_y - int(18 * SCALE)),
            (head_cx + int(18 * SCALE), mouth_y - int(24 * SCALE)),
            (head_cx + int(38 * SCALE), mouth_y - int(14 * SCALE)),
            (head_cx, mouth_y - int(8 * SCALE)),
        ], fill=(32, 24, 22, 255), outline=OUTLINE_COLOR)
    elif p["facial_hair"] == "stubble_chin":
        # Sombra sutil de barba de candado
        draw_base.chord([head_cx - int(45 * SCALE), mouth_y + int(24 * SCALE), head_cx + int(45 * SCALE), head_cy + head_ry - int(10 * SCALE)], start=0, end=180, fill=(45, 30, 25, 90))

    # Cabello frontal según el estilo
    hc = p["hair_color"]
    if p["hair_type"] == "wavy_short":
        # Mechones ondulados juveniles
        draw_base.chord([head_cx - head_rx - int(15 * SCALE), head_cy - head_ry - int(25 * SCALE), head_cx + head_rx + int(15 * SCALE), head_cy - int(30 * SCALE)], start=160, end=380, fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
        draw_base.polygon([
            (head_cx - int(70 * SCALE), head_cy - head_ry + int(45 * SCALE)),
            (head_cx - int(30 * SCALE), head_cy - int(70 * SCALE)),
            (head_cx + int(20 * SCALE), head_cy - head_ry + int(55 * SCALE)),
            (head_cx + int(60 * SCALE), head_cy - int(75 * SCALE)),
            (head_cx + head_rx, head_cy - int(85 * SCALE)),
            (head_cx + head_rx + int(10 * SCALE), head_cy - head_ry - int(20 * SCALE)),
            (head_cx - head_rx - int(10 * SCALE), head_cy - head_ry - int(20 * SCALE)),
        ], fill=hc, outline=OUTLINE_COLOR)
    elif p["hair_type"] == "long_wavy":
        # Flequillo suave femenino
        draw_base.chord([head_cx - head_rx - int(10 * SCALE), head_cy - head_ry - int(20 * SCALE), head_cx + head_rx + int(10 * SCALE), head_cy - int(40 * SCALE)], start=170, end=370, fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
        draw_base.polygon([
            (head_cx - int(90 * SCALE), head_cy - head_ry + int(70 * SCALE)),
            (head_cx - int(20 * SCALE), head_cy - int(80 * SCALE)),
            (head_cx + int(40 * SCALE), head_cy - head_ry + int(60 * SCALE)),
            (head_cx + head_rx, head_cy - int(60 * SCALE)),
            (head_cx + head_rx, head_cy - head_ry),
            (head_cx - head_rx, head_cy - head_ry),
        ], fill=hc, outline=OUTLINE_COLOR)
    elif p["hair_type"] == "short_temples_grey":
        # Pelo recortado con entradas suaves
        draw_base.chord([head_cx - head_rx - int(5 * SCALE), head_cy - head_ry - int(15 * SCALE), head_cx + head_rx + int(5 * SCALE), head_cy - int(60 * SCALE)], start=175, end=365, fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
    elif p["hair_type"] == "updo_bun":
        draw_base.chord([head_cx - head_rx - int(8 * SCALE), head_cy - head_ry - int(15 * SCALE), head_cx + head_rx + int(8 * SCALE), head_cy - int(50 * SCALE)], start=175, end=365, fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
    elif p["hair_type"] == "receding_white":
        # Calvicie frontal incipiente, pelo canoso lateral
        draw_base.arc([head_cx - head_rx - int(10 * SCALE), head_cy - head_ry, head_cx - head_rx + int(40 * SCALE), head_cy], start=90, end=270, fill=hc, width=int(22 * SCALE))
        draw_base.arc([head_cx + head_rx - int(40 * SCALE), head_cy - head_ry, head_cx + head_rx + int(10 * SCALE), head_cy], start=-90, end=90, fill=hc, width=int(22 * SCALE))
    elif p["hair_type"] == "grandma_bun":
        # Canas peinadas suaves
        draw_base.chord([head_cx - head_rx - int(8 * SCALE), head_cy - head_ry - int(15 * SCALE), head_cx + head_rx + int(8 * SCALE), head_cy - int(50 * SCALE)], start=175, end=365, fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
    elif p["hair_type"] == "textured_fade":
        # Corte moderno degradado
        draw_base.chord([head_cx - head_rx, head_cy - head_ry - int(25 * SCALE), head_cx + head_rx, head_cy - int(60 * SCALE)], start=170, end=370, fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
    elif p["hair_type"] == "medium_bob":
        draw_base.chord([head_cx - head_rx - int(10 * SCALE), head_cy - head_ry - int(20 * SCALE), head_cx + head_rx + int(10 * SCALE), head_cy - int(45 * SCALE)], start=170, end=370, fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
    elif p["hair_type"] == "messy_teen":
        draw_base.chord([head_cx - head_rx - int(12 * SCALE), head_cy - head_ry - int(30 * SCALE), head_cx + head_rx + int(12 * SCALE), head_cy - int(45 * SCALE)], start=160, end=380, fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)
    elif p["hair_type"] == "pigtails_ribbon":
        draw_base.chord([head_cx - head_rx - int(8 * SCALE), head_cy - head_ry - int(20 * SCALE), head_cx + head_rx + int(8 * SCALE), head_cy - int(45 * SCALE)], start=170, end=370, fill=hc, outline=OUTLINE_COLOR, width=OUTLINE_W)

    # Gafas si tiene
    if p["glasses"]:
        gw = int(48 * SCALE)
        gh = int(38 * SCALE)
        # Lente izq
        draw_base.rounded_rectangle([head_cx - eye_dist - gw, eye_y - gh, head_cx - eye_dist + gw, eye_y + gh], radius=int(18 * SCALE), outline=(40, 45, 55, 255), width=int(6 * SCALE))
        # Lente der
        draw_base.rounded_rectangle([head_cx + eye_dist - gw, eye_y - gh, head_cx + eye_dist + gw, eye_y + gh], radius=int(18 * SCALE), outline=(40, 45, 55, 255), width=int(6 * SCALE))
        # Puente
        draw_base.line([(head_cx - eye_dist + gw, eye_y - int(6 * SCALE)), (head_cx + eye_dist - gw, eye_y - int(6 * SCALE))], fill=(40, 45, 55, 255), width=int(6 * SCALE))

    # Guardar CAPA BASE
    img_base.save(os.path.join(p_capas_dir, "base.png"))

    # ----------------------------------------------------
    # 2. CAPAS DE OJOS (ojos.png, ojos_cerrados.png, ojos_dolor.png)
    # ----------------------------------------------------
    # Ojos normales
    img_ojos = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d_ojos = ImageDraw.Draw(img_ojos)
    draw_eye_open(d_ojos, head_cx - eye_dist, eye_y, eye_rx, eye_ry, "right")
    draw_eye_open(d_ojos, head_cx + eye_dist, eye_y, eye_rx, eye_ry, "right")
    # Cejas normales
    brow_y = eye_y - eye_ry - int(16 * SCALE)
    d_ojos.line([(head_cx - eye_dist - eye_rx, brow_y + int(4 * SCALE)), (head_cx - eye_dist, brow_y - int(4 * SCALE)), (head_cx - eye_dist + eye_rx, brow_y)], fill=OUTLINE_COLOR, width=OUTLINE_W, joint="curve")
    d_ojos.line([(head_cx + eye_dist - eye_rx, brow_y), (head_cx + eye_dist, brow_y - int(4 * SCALE)), (head_cx + eye_dist + eye_rx, brow_y + int(4 * SCALE))], fill=OUTLINE_COLOR, width=OUTLINE_W, joint="curve")
    img_ojos.save(os.path.join(p_capas_dir, "ojos.png"))

    # Ojos cerrados (Parpadeo)
    img_ojos_cerrados = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d_ojos_c = ImageDraw.Draw(img_ojos_cerrados)
    draw_eye_closed(d_ojos_c, head_cx - eye_dist, eye_y, eye_rx)
    draw_eye_closed(d_ojos_c, head_cx + eye_dist, eye_y, eye_rx)
    # Mismas cejas
    d_ojos_c.line([(head_cx - eye_dist - eye_rx, brow_y + int(4 * SCALE)), (head_cx - eye_dist, brow_y - int(4 * SCALE)), (head_cx - eye_dist + eye_rx, brow_y)], fill=OUTLINE_COLOR, width=OUTLINE_W, joint="curve")
    d_ojos_c.line([(head_cx + eye_dist - eye_rx, brow_y), (head_cx + eye_dist, brow_y - int(4 * SCALE)), (head_cx + eye_dist + eye_rx, brow_y + int(4 * SCALE))], fill=OUTLINE_COLOR, width=OUTLINE_W, joint="curve")
    img_ojos_cerrados.save(os.path.join(p_capas_dir, "ojos_cerrados.png"))

    # Ojos con dolor (cejas fruncidas sutiles)
    img_ojos_dolor = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d_ojos_d = ImageDraw.Draw(img_ojos_dolor)
    draw_eye_dolor(d_ojos_d, head_cx - eye_dist, eye_y, eye_rx, eye_ry, "right")
    draw_eye_dolor(d_ojos_d, head_cx + eye_dist, eye_y, eye_rx, eye_ry, "right")
    # Cejas inclinadas hacia abajo en el entrecejo
    d_ojos_d.line([(head_cx - eye_dist - eye_rx, brow_y - int(6 * SCALE)), (head_cx - eye_dist, brow_y), (head_cx - eye_dist + eye_rx, brow_y + int(10 * SCALE))], fill=OUTLINE_COLOR, width=OUTLINE_W, joint="curve")
    d_ojos_d.line([(head_cx + eye_dist - eye_rx, brow_y + int(10 * SCALE)), (head_cx + eye_dist, brow_y), (head_cx + eye_dist + eye_rx, brow_y - int(6 * SCALE))], fill=OUTLINE_COLOR, width=OUTLINE_W, joint="curve")
    img_ojos_dolor.save(os.path.join(p_capas_dir, "ojos_dolor.png"))

    # ----------------------------------------------------
    # 3. CAPAS DE BOCA (cerrada, entreabierta, abierta, o, dolor)
    # ----------------------------------------------------
    mouth_types = [
        ("boca_cerrada.png", draw_mouth_cerrada),
        ("boca_entreabierta.png", draw_mouth_entreabierta),
        ("boca_abierta.png", draw_mouth_abierta),
        ("boca_o.png", draw_mouth_o),
        ("boca_dolor.png", draw_mouth_dolor),
    ]
    for filename, fn in mouth_types:
        img_b = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        d_b = ImageDraw.Draw(img_b)
        fn(d_b, head_cx, mouth_y, mouth_w)
        img_b.save(os.path.join(p_capas_dir, filename))

    # ----------------------------------------------------
    # 4. IMÁGENES CONSOLIDADAS (paciente_NN.png y paciente_NN_dolor.png) a 736x736
    # ----------------------------------------------------
    # Normal completa (Base + Ojos normales + Boca cerrada)
    comp_normal = Image.alpha_composite(img_base, img_ojos)
    img_boca_c = Image.open(os.path.join(p_capas_dir, "boca_cerrada.png"))
    comp_normal = Image.alpha_composite(comp_normal, img_boca_c)
    comp_normal_736 = comp_normal.resize((736, 736), Image.Resampling.LANCZOS)
    comp_normal_736.save(os.path.join(OUTPUT_DIR, f"{pid}.png"), "PNG")
    comp_normal_736.save(os.path.join(PUBLIC_DIR, f"{pid}.png"), "PNG")

    # Con dolor completa (Base + Ojos dolor + Boca dolor)
    comp_dolor = Image.alpha_composite(img_base, img_ojos_dolor)
    img_boca_d = Image.open(os.path.join(p_capas_dir, "boca_dolor.png"))
    comp_dolor = Image.alpha_composite(comp_dolor, img_boca_d)
    comp_dolor_736 = comp_dolor.resize((736, 736), Image.Resampling.LANCZOS)
    comp_dolor_736.save(os.path.join(OUTPUT_DIR, f"{pid}_dolor.png"), "PNG")
    comp_dolor_736.save(os.path.join(PUBLIC_DIR, f"{pid}_dolor.png"), "PNG")

    # También redimensionamos las capas a 736x736 para que el navegador las consuma ultrarrápidas
    for capa_f in os.listdir(p_capas_dir):
        capa_path = os.path.join(p_capas_dir, capa_f)
        layer_img = Image.open(capa_path).resize((736, 736), Image.Resampling.LANCZOS)
        layer_img.save(capa_path, "PNG")

    print(f"Generado con éxito: {pid} (5 capas + 2 imágenes consolidadas 736x736)")

def main():
    print("Iniciando generación de las 10 personas salvadoreñas...")
    for p in PATIENTS:
        render_patient(p)
    print("¡Generación completada para los 10 pacientes!")

if __name__ == "__main__":
    main()
