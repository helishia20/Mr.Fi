"""
Mr Fi 🐸 — assets.py
Image loading with transparent background removal for decorations.
"""
import os
import pygame
from config import IMG_DIR, FOOD_CATALOGUE, DECORATION_CATALOGUE


def load_img(filename, fallback_color=(120, 200, 140)):
    path = os.path.join(IMG_DIR, filename)
    if os.path.exists(path):
        try:
            return pygame.image.load(path).convert_alpha()
        except Exception:
            pass
    surf = pygame.Surface((128, 128), pygame.SRCALPHA)
    surf.fill(fallback_color + (255,))
    return surf


def remove_white_bg(surface, threshold=40):
    """
    پس‌زمینه سفید/روشن رو شفاف میکنه.
    threshold: هر پیکسلی که R,G,B همه بالای 255-threshold باشن شفاف میشه.
    """
    surf = surface.convert_alpha()
    w, h = surf.get_size()
    for x in range(w):
        for y in range(h):
            r, g, b, a = surf.get_at((x, y))
            if r > 255 - threshold and g > 255 - threshold and b > 255 - threshold:
                surf.set_at((x, y), (r, g, b, 0))
    return surf


def remove_white_bg_fast(surface, threshold=40):
    """
    نسخه سریع‌تر با numpy (اگه نصب باشه).
    """
    try:
        import numpy as np
        surf = surface.convert_alpha()
        arr  = pygame.surfarray.pixels_alpha(surf)
        rgb  = pygame.surfarray.array3d(surf)
        # پیکسل‌هایی که R,G,B همه بالای threshold هستن
        mask = (rgb[:,:,0] > 255 - threshold) & \
               (rgb[:,:,1] > 255 - threshold) & \
               (rgb[:,:,2] > 255 - threshold)
        arr[mask] = 0
        del arr
        return surf
    except ImportError:
        return remove_white_bg(surface, threshold)


def scale_to_height(img, target_h):
    w, h = img.get_size()
    if h == 0: return img
    scale = target_h / h
    return pygame.transform.smoothscale(img, (max(1, int(w * scale)), max(1, int(h * scale))))


def scale_to_fit(img, max_w, max_h):
    w, h = img.get_size()
    if w == 0 or h == 0: return img
    ratio = min(max_w / w, max_h / h)
    return pygame.transform.smoothscale(img, (max(1, int(w * ratio)), max(1, int(h * ratio))))


class Assets:
    def __init__(self):
        self.sprites = {
            "idle":     load_img("idle.png"),
            "happy":    load_img("happy.png"),
            "sad":      load_img("crying.png"),
            "stressed": load_img("stressed.png"),
            "sleeping": load_img("sleeping.png"),
            "enjoyed":  load_img("enjoyed.png"),
            "crying":   load_img("crying.png"),
        }
        self.icons = {
            "hunger":     load_img("hunger.png"),
            "energy":     load_img("energy.png"),
            "coin":       load_img("coin.png"),
            "happy_icon": load_img("happy_icon.png"),
        }
        self.food_imgs = {
            key: load_img(img_file)
            for key, _n, _p, _v, img_file in FOOD_CATALOGUE
        }
        # دکوراسیون‌ها با پس‌زمینه شفاف
        self.deco_imgs = {}
        for deco_id, _n, _p, img_file in DECORATION_CATALOGUE:
            raw = load_img(img_file)
            # پس‌زمینه سفید/روشن رو حذف کن
            self.deco_imgs[deco_id] = remove_white_bg_fast(raw, threshold=45)

        self.bedroom_bg = load_img("bg_bedroom.jpg")
