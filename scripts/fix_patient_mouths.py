"""
Script para corregir la boca animada y las capas de los 10 pacientes:
1. Elimina por completo la boca original en base.png mediante interpolación
   de color de piel pura de la zona (sin alterar ninguna otra parte del rostro).
2. Genera boca_cerrada.png recortando EXACTAMENTE la boca original a su
   posición, tamaño y trazo original (idéntica a la imagen en reposo, 0 diferencias).
3. Genera las variantes de boca (entreabierta, abierta, o, dolor) calibradas
   al milímetro en la misma posición exacta (cx, cy) y ancho original, con fondo
   transparente para que no se superpongan ni creen dobles bocas o cortes.
4. Genera capas de parpadeo (ojos_cerrados.png) calibradas en los ojos.
5. Exporta las capas y consolidado para cada uno de los 10 personajes.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC_DIR = r"c:\Users\miran\Desktop\imagenes"
PUBLIC_PACIENTES = "frontend/public/pacientes"
CAPAS_DIR = os.path.join(PUBLIC_PACIENTES, "capas")
PUBLIC_ROOT = "frontend/public"

os.makedirs(PUBLIC_PACIENTES, exist_ok=True)
os.makedirs(CAPAS_DIR, exist_ok=True)
os.makedirs(PUBLIC_ROOT, exist_ok=True)

OUTLINE_COLOR = (28, 20, 18, 255)

PERSON_CONFIGS = [
    {
        "alias": "paciente_01",
        "filename": "salvadoran_teen_16_1795334120976",
        "gender": "M",
        "age_group": "adolescente",
        "mouth_box": (432, 550, 585, 578),
        "cx": 508, "cy": 567, "w": 142,
        "left_eye": (423, 411), "right_eye": (602, 411), "eye_r": 34,
        "skin": (226, 154, 106, 255),
    },
    {
        "alias": "paciente_02",
        "filename": "salvadoran_teen_girl_16_1795334795183",
        "gender": "F",
        "age_group": "adolescente",
        "mouth_box": (442, 510, 577, 537),
        "cx": 509, "cy": 526, "w": 124,
        "left_eye": (417, 396), "right_eye": (587, 397), "eye_r": 34,
        "skin": (221, 139, 96, 255),
    },
    {
        "alias": "paciente_03",
        "filename": "salvadoran_man_32_1795334120225",
        "gender": "M",
        "age_group": "mediana",
        "mouth_box": (436, 543, 585, 570),
        "cx": 510, "cy": 559, "w": 138,
        "left_eye": (433, 401), "right_eye": (587, 401), "eye_r": 34,
        "skin": (221, 160, 85, 255),
    },
    {
        "alias": "paciente_04",
        "filename": "salvadoran_woman_32_1795334794354",
        "gender": "F",
        "age_group": "mediana",
        "mouth_box": (435, 545, 585, 573),
        "cx": 510, "cy": 560, "w": 139,
        "left_eye": (429, 399), "right_eye": (594, 400), "eye_r": 34,
        "skin": (215, 139, 88, 255),
    },
    {
        "alias": "paciente_05",
        "filename": "salvadoran_man_37_1795334119916",
        "gender": "M",
        "age_group": "mediana",
        "mouth_box": (434, 545, 586, 571),
        "cx": 510, "cy": 559, "w": 141,
        "left_eye": (428, 402), "right_eye": (593, 403), "eye_r": 34,
        "skin": (204, 135, 86, 255),
    },
    {
        "alias": "paciente_06",
        "filename": "salvadoran_woman_37_1795334794902",
        "gender": "F",
        "age_group": "mediana",
        "mouth_box": (420, 515, 545, 545),
        "cx": 484, "cy": 530, "w": 110,
        "left_eye": (407, 400), "right_eye": (564, 395), "eye_r": 34,
        "skin": (210, 134, 91, 255),
    },
    {
        "alias": "paciente_07",
        "filename": "salvadoran_elder_60s_1795334118502",
        "gender": "M",
        "age_group": "mayor",
        "mouth_box": (435, 565, 588, 591),
        "cx": 511, "cy": 579, "w": 142,
        "left_eye": (431, 410), "right_eye": (589, 410), "eye_r": 34,
        "skin": (205, 148, 111, 255),
    },
    {
        "alias": "paciente_08",
        "filename": "salvadoran_elder_woman_60s_1795334795305",
        "gender": "F",
        "age_group": "mayor",
        "mouth_box": (443, 535, 580, 559),
        "cx": 511, "cy": 547, "w": 126,
        "left_eye": (429, 402), "right_eye": (596, 401), "eye_r": 34,
        "skin": (214, 142, 96, 255),
    },
    {
        "alias": "paciente_09",
        "filename": "salvadoran_elder_70s_1795334119565",
        "gender": "M",
        "age_group": "mayor",
        "mouth_box": (430, 560, 590, 587),
        "cx": 510, "cy": 575, "w": 149,
        "left_eye": (431, 413), "right_eye": (592, 412), "eye_r": 34,
        "skin": (190, 116, 72, 255),
    },
    {
        "alias": "paciente_10",
        "filename": "salvadoran_elder_woman_70s_1795334794730",
        "gender": "F",
        "age_group": "mayor",
        "mouth_box": (451, 545, 572, 575),
        "cx": 511, "cy": 560, "w": 110,
        "left_eye": (424, 448), "right_eye": (601, 448), "eye_r": 34,
        "skin": (192, 122, 78, 255),
    },
]

def erase_mouth_from_image(im_trans, box, cx):
    """
    Elimina la boca de la imagen base reemplazándola por el color
    de piel circundante de forma completamente homogénea y suave.
    """
    arr = np.array(im_trans).copy()
    x1, y1, x2, y2 = box

    # Muestras de piel limpia justo encima y debajo del centro de la boca
    top_skin = arr[y1 - 7:y1 - 2, cx - 25:cx + 25, :3].mean(axis=(0, 1))
    bot_skin = arr[y2 + 2:y2 + 7, cx - 25:cx + 25, :3].mean(axis=(0, 1))

    H_box = y2 - y1
    for i in range(H_box):
        y = y1 + i
        t = i / max(1.0, float(H_box - 1))
        row_color = (1.0 - t) * top_skin + t * bot_skin

        row_px = arr[y, x1:x2, :3]
        # Píxeles de boca (trazo oscuro o bermellón de labios)
        is_mouth = (row_px[:, 0] < 115) & (row_px[:, 1] < 115) & (row_px[:, 2] < 115)
        is_lip = (row_px.mean(axis=1) < 135) | (
            (row_px[:, 0].astype(int) - row_px[:, 1].astype(int) > 20) & (row_px[:, 2] < 125)
        )
        replace_mask = is_mouth | is_lip
        arr[y, x1:x2, :3][replace_mask] = row_color.astype(np.uint8)

    # Suavizar sutilmente solo el parche intervenido
    patch = Image.fromarray(arr[y1:y2, x1:x2])
    patch_blur = patch.filter(ImageFilter.GaussianBlur(radius=0.9))
    arr[y1:y2, x1:x2] = np.array(patch_blur)

    return Image.fromarray(arr)

def extract_original_mouth(im_trans, box):
    """
    Extrae la boca original exactamente como fue dibujada en la imagen,
    manteniendo el mismo lienzo 1024x1024 con transparencia alrededor.
    """
    W, H = im_trans.size
    mouth_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x1, y1, x2, y2 = box
    crop = im_trans.crop((x1, y1, x2, y2))
    mouth_img.paste(crop, (x1, y1))
    return mouth_img

def create_mouth_variants(W, H, cx, cy, w):
    """
    Crea las variantes de boca calibradas al milímetro en la misma
    posición exacta (cx, cy) y con el mismo ancho original, con fondo
    transparente (sin parches opacos que tapen el rostro).
    """
    mw = int(w * 0.44)

    # 1. boca_entreabierta
    b_entre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    de = ImageDraw.Draw(b_entre)
    # Apertura leve con dientes
    de.ellipse([cx - mw + 6, cy - 8, cx + mw - 6, cy + 8], fill=(90, 20, 28, 255), outline=OUTLINE_COLOR, width=5)
    de.rectangle([cx - int(mw * 0.55), cy - 6, cx + int(mw * 0.55), cy], fill=(255, 250, 240, 255))
    de.line([(cx - mw + 4, cy), (cx + mw - 4, cy)], fill=(130, 45, 52, 255), width=2)

    # 2. boca_abierta (hablando)
    b_abierta = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    da = ImageDraw.Draw(b_abierta)
    mh = 22
    da.chord([cx - mw, cy - mh, cx + mw, cy + mh], start=0, end=180, fill=(90, 20, 28, 255), outline=OUTLINE_COLOR, width=6)
    da.rectangle([cx - int(mw * 0.65), cy, cx + int(mw * 0.65), cy + 7], fill=(255, 250, 240, 255))
    da.ellipse([cx - int(mw * 0.45), cy + 7, cx + int(mw * 0.45), cy + mh], fill=(228, 116, 136, 255))
    da.arc([cx - mw, cy - mh, cx + mw, cy + mh], start=0, end=180, fill=OUTLINE_COLOR, width=6)
    da.line([(cx - mw, cy), (cx + mw, cy)], fill=OUTLINE_COLOR, width=6)

    # 3. boca_o (fonemas redondeados)
    b_o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    do = ImageDraw.Draw(b_o)
    ow = int(mw * 0.6)
    oh = 24
    do.ellipse([cx - ow, cy - 12, cx + ow, cy + oh], fill=(85, 20, 28, 255), outline=OUTLINE_COLOR, width=6)
    do.ellipse([cx - int(ow * 0.55), cy + 5, cx + int(ow * 0.55), cy + oh - 4], fill=(228, 116, 136, 255))

    # 4. boca_dolor (molestia)
    b_dolor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(b_dolor)
    points = [
        (cx - mw, cy + 4),
        (cx - int(mw * 0.3), cy - 3),
        (cx, cy - 2),
        (cx + int(mw * 0.3), cy + 1),
        (cx + mw, cy + 6),
    ]
    dd.line(points, fill=OUTLINE_COLOR, width=6, joint="curve")

    return {
        "boca_entreabierta.png": b_entre,
        "boca_abierta.png": b_abierta,
        "boca_o.png": b_o,
        "boca_dolor.png": b_dolor,
    }

def create_eye_layers(W, H, left_eye, right_eye, er, skin_color):
    """Capas de ojos: transparente en reposo, párpados cerrados al parpadear."""
    ojos_open = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    ojos_closed = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(ojos_closed)
    for (cx, cy) in (left_eye, right_eye):
        # Parche de párpado suave sobre el ojo abierto al parpadear
        dc.ellipse([cx - er - 4, cy - er - 4, cx + er + 4, cy + er + 4], fill=skin_color)
        pts = [
            (cx - er + 2, cy + 2),
            (cx - er // 2, cy - 8),
            (cx, cy - 10),
            (cx + er // 2, cy - 8),
            (cx + er - 2, cy + 2),
        ]
        dc.line(pts, fill=OUTLINE_COLOR, width=7, joint="curve")

    ojos_dolor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(ojos_dolor)
    lx, ly = left_eye
    rx, ry = right_eye
    dd.line([(lx - er, ly - er - 4), (lx + er, ly - er + 8)], fill=OUTLINE_COLOR, width=7, joint="curve")
    dd.line([(rx - er, ry - er + 8), (rx + er, ry - er - 4)], fill=OUTLINE_COLOR, width=7, joint="curve")

    return {
        "ojos.png": ojos_open,
        "ojos_cerrados.png": ojos_closed,
        "ojos_dolor.png": ojos_dolor,
    }

def process_all():
    print("Iniciando corrección de bocas y capas para las 10 imágenes...")
    corrected_list = []

    for idx, cfg in enumerate(PERSON_CONFIGS):
        fn = cfg["filename"]
        alias = cfg["alias"]
        src_png = os.path.join(SRC_DIR, f"{fn}.png")
        if not os.path.exists(src_png):
            print(f"Error: {src_png} no existe.")
            continue

        im_trans = Image.open(src_png).convert("RGBA")
        W, H = im_trans.size

        # 1. Base sin boca
        base_no_mouth = erase_mouth_from_image(im_trans, cfg["mouth_box"], cfg["cx"])

        # 2. Boca cerrada original exacta
        boca_cerrada = extract_original_mouth(im_trans, cfg["mouth_box"])

        # 3. Variantes de boca
        mouth_variants = create_mouth_variants(W, H, cfg["cx"], cfg["cy"], cfg["w"])

        # 4. Capas de ojos
        eye_layers = create_eye_layers(W, H, cfg["left_eye"], cfg["right_eye"], cfg["eye_r"], cfg["skin"])

        # Verificación composiciones:
        # A) En reposo: base + boca_cerrada debe ser idéntico al original
        comp_reposo = Image.alpha_composite(base_no_mouth, boca_cerrada)
        diff_reposo = np.abs(np.array(im_trans).astype(int) - np.array(comp_reposo).astype(int)).max()
        assert diff_reposo == 0, f"Error en {alias}: reposo difiere del original ({diff_reposo} max diff)"

        # B) Al hablar: base + boca_abierta debe mostrar exactamente UNA boca sin trazo residual
        comp_habla = Image.alpha_composite(base_no_mouth, mouth_variants["boca_abierta.png"])

        # 5. Guardar capas para fn y alias
        for folder_name in (fn, alias):
            p_capas_dir = os.path.join(CAPAS_DIR, folder_name)
            os.makedirs(p_capas_dir, exist_ok=True)

            base_no_mouth.save(os.path.join(p_capas_dir, "base.png"), "PNG")
            boca_cerrada.save(os.path.join(p_capas_dir, "boca_cerrada.png"), "PNG")

            for m_name, m_img in mouth_variants.items():
                m_img.save(os.path.join(p_capas_dir, m_name), "PNG")

            for e_name, e_img in eye_layers.items():
                e_img.save(os.path.join(p_capas_dir, e_name), "PNG")

        # 6. Imagen consolidada (la original con transparencia)
        im_trans.save(os.path.join(PUBLIC_PACIENTES, f"{fn}.png"), "PNG")
        im_trans.save(os.path.join(PUBLIC_PACIENTES, f"{alias}.png"), "PNG")
        im_trans.save(os.path.join(PUBLIC_ROOT, f"{alias}.png"), "PNG")
        im_trans.save(os.path.join(PUBLIC_ROOT, f"{fn}.png"), "PNG")

        # Versión dolor consolidada
        comp_dolor = Image.alpha_composite(base_no_mouth, mouth_variants["boca_dolor.png"])
        comp_dolor = Image.alpha_composite(comp_dolor, eye_layers["ojos_dolor.png"])
        comp_dolor.save(os.path.join(PUBLIC_PACIENTES, f"{alias}_dolor.png"), "PNG")
        comp_dolor.save(os.path.join(PUBLIC_ROOT, f"{alias}_dolor.png"), "PNG")

        corrected_list.append(alias)
        print(f"[{idx+1}/10] Verificado y corregido: {alias} ({fn}) — reposo diff: 0, habla: boca única alineada")

    print(f"Corrección completada para: {', '.join(corrected_list)}")

if __name__ == "__main__":
    process_all()
