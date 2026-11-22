"""
Script para procesar las 10 imágenes reales de la carpeta Desktop/imagenes:
1. Quita el fondo dejando transparencia limpia (PNG) sin alterar al personaje.
2. Guarda las versiones sin fondo con su nombre original en Desktop/imagenes/*.png.
3. Crea las capas de animación (base sin fondo, boca_*, ojos_*) en frontend/public/pacientes/capas/.
4. Mapea tanto los nombres originales como paciente_01..10 para máxima compatibilidad.
"""

import os
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from collections import deque

SRC_DIR = r"c:\Users\miran\Desktop\imagenes"
PUBLIC_PACIENTES = "frontend/public/pacientes"
CAPAS_DIR = os.path.join(PUBLIC_PACIENTES, "capas")
PUBLIC_ROOT = "frontend/public"

os.makedirs(SRC_DIR, exist_ok=True)
os.makedirs(PUBLIC_PACIENTES, exist_ok=True)
os.makedirs(CAPAS_DIR, exist_ok=True)
os.makedirs(PUBLIC_ROOT, exist_ok=True)

OUTLINE_COLOR = (30, 22, 20, 255)

# Coordenadas faciales medidas para cada una de las 10 imágenes reales
CONFIGS = [
    {
        "filename": "salvadoran_teen_16_1795334120976.jpg",
        "alias": "paciente_01",
        "left_eye": (442, 397),
        "right_eye": (628, 397),
        "eye_r": 36,
        "mouth": (535, 635),
        "mouth_w": 52,
        "skin": (223, 150, 104, 255),
    },
    {
        "filename": "salvadoran_teen_girl_16_1795334795183.jpg",
        "alias": "paciente_02",
        "left_eye": (410, 395),
        "right_eye": (615, 395),
        "eye_r": 36,
        "mouth": (512, 650),
        "mouth_w": 50,
        "skin": (227, 153, 104, 255),
    },
    {
        "filename": "salvadoran_man_32_1795334120225.jpg",
        "alias": "paciente_03",
        "left_eye": (419, 395),
        "right_eye": (580, 380),
        "eye_r": 35,
        "mouth": (500, 620),
        "mouth_w": 55,
        "skin": (223, 161, 86, 255),
    },
    {
        "filename": "salvadoran_woman_32_1795334794354.jpg",
        "alias": "paciente_04",
        "left_eye": (409, 400),
        "right_eye": (608, 421),
        "eye_r": 36,
        "mouth": (512, 655),
        "mouth_w": 52,
        "skin": (228, 158, 102, 255),
    },
    {
        "filename": "salvadoran_man_37_1795334119916.jpg",
        "alias": "paciente_05",
        "left_eye": (420, 390),
        "right_eye": (605, 390),
        "eye_r": 35,
        "mouth": (510, 615),
        "mouth_w": 56,
        "skin": (207, 135, 88, 255),
    },
    {
        "filename": "salvadoran_woman_37_1795334794902.jpg",
        "alias": "paciente_06",
        "left_eye": (415, 390),
        "right_eye": (610, 390),
        "eye_r": 36,
        "mouth": (512, 650),
        "mouth_w": 52,
        "skin": (218, 150, 101, 255),
    },
    {
        "filename": "salvadoran_elder_60s_1795334118502.jpg",
        "alias": "paciente_07",
        "left_eye": (447, 431),
        "right_eye": (620, 411),
        "eye_r": 32,
        "mouth": (535, 595),
        "mouth_w": 54,
        "skin": (212, 139, 94, 255),
    },
    {
        "filename": "salvadoran_elder_woman_60s_1795334795305.jpg",
        "alias": "paciente_08",
        "left_eye": (420, 410),
        "right_eye": (610, 405),
        "eye_r": 34,
        "mouth": (515, 620),
        "mouth_w": 52,
        "skin": (213, 141, 95, 255),
    },
    {
        "filename": "salvadoran_elder_70s_1795334119565.jpg",
        "alias": "paciente_09",
        "left_eye": (445, 443),
        "right_eye": (604, 443),
        "eye_r": 32,
        "mouth": (525, 595),
        "mouth_w": 52,
        "skin": (194, 117, 73, 255),
    },
    {
        "filename": "salvadoran_elder_woman_70s_1795334794730.jpg",
        "alias": "paciente_10",
        "left_eye": (455, 452),
        "right_eye": (576, 444),
        "eye_r": 32,
        "mouth": (520, 610),
        "mouth_w": 50,
        "skin": (207, 136, 90, 255),
    },
]

def remove_background(im):
    arr = np.array(im, dtype=np.float32)
    H, W, _ = arr.shape

    border_pixels = np.vstack([arr[0, :], arr[-1, :], arr[:, 0], arr[:, -1]])
    bg_med = np.median(border_pixels, axis=0)

    dist = np.linalg.norm(arr - bg_med, axis=2)
    brightness = arr.mean(axis=2)

    # El fondo es crema claro (dist < 42 de la mediana de bordes y no contorno oscuro)
    is_bg_candidate = (dist < 42.0) & (brightness > 95.0)

    bg_mask = np.zeros((H, W), dtype=bool)
    q = deque()

    for x in range(W):
        if is_bg_candidate[0, x]: q.append((0, x)); bg_mask[0, x] = True
        if is_bg_candidate[H-1, x]: q.append((H-1, x)); bg_mask[H-1, x] = True
    for y in range(H):
        if is_bg_candidate[y, 0]: q.append((y, 0)); bg_mask[y, 0] = True
        if is_bg_candidate[y, W-1]: q.append((y, W-1)); bg_mask[y, W-1] = True

    while q:
        y, x = q.popleft()
        for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W:
                if not bg_mask[ny, nx] and is_bg_candidate[ny, nx]:
                    bg_mask[ny, nx] = True
                    q.append((ny, nx))

    alpha = np.where(bg_mask, 0, 255).astype(np.uint8)
    alpha_im = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(radius=0.7))

    res = Image.new("RGBA", (W, H))
    res.paste(im, (0, 0))
    res.putalpha(alpha_im)
    return res

def generate_mouth_layers(W, H, mouth_pos, mw, skin_color):
    """Genera las variantes de boca para sincronización con audio."""
    cx, cy = mouth_pos
    patch_w = mw + 18
    patch_h = 36

    # 1. boca_cerrada: transparente (muestra la boca original del personaje)
    b_cerrada = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # 2. boca_entreabierta: labios ligeramente separados mostrando dientes
    b_entre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_e = ImageDraw.Draw(b_entre)
    # Parche de piel difuminado sobre la boca original
    d_e.ellipse([cx - patch_w, cy - patch_h, cx + patch_w, cy + patch_h], fill=skin_color)
    # Apertura elíptica con dientes
    d_e.ellipse([cx - mw + 10, cy - 14, cx + mw - 10, cy + 14], fill=(255, 248, 238, 255), outline=OUTLINE_COLOR, width=6)
    d_e.line([(cx - mw + 14, cy), (cx + mw - 14, cy)], fill=(130, 45, 50, 255), width=3)

    # 3. boca_abierta: apertura al hablar mostrando cavidad, dientes y lengua
    b_abierta = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_a = ImageDraw.Draw(b_abierta)
    d_a.ellipse([cx - patch_w, cy - patch_h - 10, cx + patch_w, cy + patch_h + 16], fill=skin_color)
    mh = 26
    # Interior oscuro
    d_a.chord([cx - mw, cy - mh, cx + mw, cy + mh], start=0, end=180, fill=(90, 20, 28, 255), outline=OUTLINE_COLOR, width=7)
    # Dientes superiores
    d_a.rectangle([cx - int(mw * 0.7), cy - 2, cx + int(mw * 0.7), cy + 8], fill=(255, 250, 240, 255))
    # Lengua rosada
    d_a.ellipse([cx - int(mw * 0.5), cy + 8, cx + int(mw * 0.5), cy + mh], fill=(228, 116, 136, 255))
    # Contorno
    d_a.arc([cx - mw, cy - mh, cx + mw, cy + mh], start=0, end=180, fill=OUTLINE_COLOR, width=7)
    d_a.line([(cx - mw, cy), (cx + mw, cy)], fill=OUTLINE_COLOR, width=7)

    # 4. boca_o: redonda para fonemas /o/, /u/
    b_o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_o = ImageDraw.Draw(b_o)
    d_o.ellipse([cx - patch_w, cy - patch_h - 10, cx + patch_w, cy + patch_h + 16], fill=skin_color)
    ow = int(mw * 0.6)
    oh = 28
    d_o.ellipse([cx - ow, cy - 14, cx + ow, cy + oh], fill=(85, 20, 28, 255), outline=OUTLINE_COLOR, width=7)
    d_o.ellipse([cx - int(ow * 0.6), cy + 6, cx + int(ow * 0.6), cy + oh - 4], fill=(228, 116, 136, 255))

    # 5. boca_dolor: mueca sutil de molestia
    b_dolor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_d = ImageDraw.Draw(b_dolor)
    d_d.ellipse([cx - patch_w, cy - patch_h, cx + patch_w, cy + patch_h], fill=skin_color)
    points = [
        (cx - mw, cy + 4),
        (cx - int(mw * 0.3), cy - 3),
        (cx, cy - 2),
        (cx + int(mw * 0.3), cy + 1),
        (cx + mw, cy + 6),
    ]
    d_d.line(points, fill=OUTLINE_COLOR, width=7, joint="curve")

    return {
        "boca_cerrada.png": b_cerrada,
        "boca_entreabierta.png": b_entre,
        "boca_abierta.png": b_abierta,
        "boca_o.png": b_o,
        "boca_dolor.png": b_dolor,
    }

def generate_eye_layers(W, H, left_eye, right_eye, er, skin_color):
    """Genera las capas de ojos abiertos (transparente) y ojos cerrados (parpadeo)."""
    # 1. ojos.png: transparente (muestra los ojos originales abiertos)
    ojos_open = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # 2. ojos_cerrados.png: parche de párpado con arco de ojo cerrado
    ojos_closed = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_c = ImageDraw.Draw(ojos_closed)
    for (cx, cy) in (left_eye, right_eye):
        # Parche de piel sobre el ojo abierto
        d_c.ellipse([cx - er - 8, cy - er - 8, cx + er + 8, cy + er + 8], fill=skin_color)
        # Línea de párpado cerrado
        pts = [
            (cx - er, cy + 4),
            (cx - er // 2, cy - 10),
            (cx, cy - 12),
            (cx + er // 2, cy - 10),
            (cx + er, cy + 4),
        ]
        d_c.line(pts, fill=OUTLINE_COLOR, width=8, joint="curve")

    # 3. ojos_dolor.png: cejas fruncidas sutiles
    ojos_dolor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_d = ImageDraw.Draw(ojos_dolor)
    lx, ly = left_eye
    rx, ry = right_eye
    # Cejas inclinadas hacia el entrecejo
    d_d.line([(lx - er, ly - er - 6), (lx, ly - er), (lx + er, ly - er + 10)], fill=OUTLINE_COLOR, width=8, joint="curve")
    d_d.line([(rx - er, ry - er + 10), (rx, ry - er), (rx + er, ry - er - 6)], fill=OUTLINE_COLOR, width=8, joint="curve")

    return {
        "ojos.png": ojos_open,
        "ojos_cerrados.png": ojos_closed,
        "ojos_dolor.png": ojos_dolor,
    }

def process_all():
    print("Iniciando procesamiento de las 10 imágenes de Desktop/imagenes...")
    for idx, cfg in enumerate(CONFIGS):
        fn = cfg["filename"]
        alias = cfg["alias"]
        src_path = os.path.join(SRC_DIR, fn)

        if not os.path.exists(src_path):
            print(f"Advertencia: {src_path} no existe, omitiendo.")
            continue

        base_name = os.path.splitext(fn)[0]
        im = Image.open(src_path)
        W, H = im.size

        # 1. Quitar fondo dejando PNG transparente sin modificar colores ni tamaño
        im_trans = remove_background(im)

        # 2. Guardar en Desktop/imagenes con su nombre original en .png
        dest_desktop_png = os.path.join(SRC_DIR, f"{base_name}.png")
        im_trans.save(dest_desktop_png, "PNG")
        print(f"Guardado sin fondo en Desktop: {dest_desktop_png}")

        # 3. Guardar en frontend/public/pacientes/ con ambos nombres (original y alias)
        dest_pub_orig = os.path.join(PUBLIC_PACIENTES, f"{base_name}.png")
        dest_pub_alias = os.path.join(PUBLIC_PACIENTES, f"{alias}.png")
        dest_root_alias = os.path.join(PUBLIC_ROOT, f"{alias}.png")

        im_trans.save(dest_pub_orig, "PNG")
        im_trans.save(dest_pub_alias, "PNG")
        im_trans.save(dest_root_alias, "PNG")

        # Versión dolor consolidada
        im_trans.save(os.path.join(PUBLIC_PACIENTES, f"{alias}_dolor.png"), "PNG")
        im_trans.save(os.path.join(PUBLIC_ROOT, f"{alias}_dolor.png"), "PNG")

        # 4. Generar capas de animación para alias y nombre original
        for folder_id in (alias, base_name):
            capas_folder = os.path.join(CAPAS_DIR, folder_id)
            os.makedirs(capas_folder, exist_ok=True)

            # Capa base
            im_trans.save(os.path.join(capas_folder, "base.png"), "PNG")

            # Capas de boca
            mouth_layers = generate_mouth_layers(W, H, cfg["mouth"], cfg["mouth_w"], cfg["skin"])
            for m_name, m_img in mouth_layers.items():
                m_img.save(os.path.join(capas_folder, m_name), "PNG")

            # Capas de ojos
            eye_layers = generate_eye_layers(W, H, cfg["left_eye"], cfg["right_eye"], cfg["eye_r"], cfg["skin"])
            for e_name, e_img in eye_layers.items():
                e_img.save(os.path.join(capas_folder, e_name), "PNG")

        print(f"[{idx+1}/10] Procesado exitosamente {fn} -> {alias}")

    print("¡Procesamiento completo de las 10 imágenes finalizado con éxito!")

if __name__ == "__main__":
    process_all()
