"""
widgets.py: Reusable UI — Button, HUD bars, toast.
"""
import math, time
import pygame
from config import PANEL, PANEL_DARK, INK, INK_LIGHT, MUTED, MUTED_LIGHT, ACCENT, WHITE, DARK_BACKGROUNDS
from assets import scale_to_height, scale_to_fit
from audio  import beep


# ── Helpers ────────────────────────────────────────────────────────────────────

def is_dark_bg(state: dict) -> bool:
    return state.get("active_background", "bg_main") in DARK_BACKGROUNDS

def panel_col(dark: bool):
    return PANEL_DARK if dark else PANEL

def ink_col(dark: bool):
    return INK_LIGHT if dark else INK

def muted_col(dark: bool):
    return MUTED_LIGHT if dark else MUTED


# ── Button ─────────────────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect, label, cb,
                 color=None, text_color=None, icon=None, dark=False):
        self.rect       = pygame.Rect(rect)
        self.label      = label
        self.cb         = cb
        self._color     = color
        self._text_color = text_color
        self.icon       = icon
        self.hover      = False
        self.dark       = dark

    def _colors(self):
        col  = self._color  or (PANEL_DARK if self.dark else PANEL)
        tcol = self._text_color or (INK_LIGHT if self.dark else INK)
        return col, tcol

    def draw(self, surf, font, dark=None):
        if dark is not None:
            self.dark = dark
        col, tcol = self._colors()
        c = tuple(min(255, x + 20) for x in col) if self.hover else col
        # semi-transparent panel
        s = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        r = pygame.Rect(0, 0, self.rect.w, self.rect.h)
        pygame.draw.rect(s, c + (210,), r, border_radius=12)
        pygame.draw.rect(s, tcol + (180,), r, 2, border_radius=12)
        surf.blit(s, self.rect.topleft)

        if self.icon:
            ic = scale_to_height(self.icon, self.rect.h - 12)
            surf.blit(ic, (self.rect.x + 8, self.rect.y + 6))
            tx = self.rect.x + 8 + ic.get_width() + 6
        else:
            tx = self.rect.x + 14

        t = font.render(self.label, True, tcol)
        surf.blit(t, (tx, self.rect.centery - t.get_height() // 2))

    def handle(self, ev):
        if ev.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                beep(660, 60, 0.25)
                self.cb()


# ── Toast ──────────────────────────────────────────────────────────────────────

def draw_toast(surf, font_b, text, win_w, win_h):
    ts = font_b.render(text, True, INK)
    r  = ts.get_rect(center=(win_w // 2, win_h - 35))
    bg = r.inflate(24, 12)
    s  = pygame.Surface((bg.w, bg.h), pygame.SRCALPHA)
    pygame.draw.rect(s, (255, 252, 220, 230), (0, 0, bg.w, bg.h), border_radius=10)
    pygame.draw.rect(s, INK + (200,),         (0, 0, bg.w, bg.h), 2, border_radius=10)
    surf.blit(s, bg.topleft)
    surf.blit(ts, r)


# ── HUD stat bars ──────────────────────────────────────────────────────────────

def _draw_pill_icon(surf, cx, cy, size, color, symbol, font):
    """Draw a glowing circle icon with a symbol."""
    # outer glow
    glow = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
    pygame.draw.circle(glow, color + (40,), (size * 3 // 2, size * 3 // 2), size * 3 // 2)
    surf.blit(glow, (cx - size * 3 // 2, cy - size * 3 // 2))
    # main circle
    pygame.draw.circle(surf, color,       (cx, cy), size)
    pygame.draw.circle(surf, WHITE,       (cx, cy), size, 2)
    # symbol
    t = font.render(symbol, True, WHITE)
    surf.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))


def draw_hud(surf, fonts, state, icons, x, y, dark=False):
    """
    Draw the rich HUD: coin row + three stat bars with pill icons.
    """
    txt_col  = INK_LIGHT if dark else INK
    mut_col  = MUTED_LIGHT if dark else MUTED
    font_s   = fonts["small"]
    font_n   = fonts["normal"]
    bar_w    = 150
    icon_r   = 14          # pill radius

    BARS = [
        ("Hunger", "hunger",    state["hunger"],    (230, 100, 80),  "🍖", icons.get("hunger")),
        ("Happy",  "happiness", state["happiness"], (90,  200, 120), "💚", icons.get("happy_icon")),
        ("Energy", "energy",    state["energy"],    (80,  160, 230), "⚡", icons.get("energy")),
    ]

    for i, (lbl, key, val, col, sym, icon) in enumerate(BARS):
        yy = y + i * 30

        # ── pill icon ──
        if icon:
            scaled = scale_to_height(icon, icon_r * 2)
            surf.blit(scaled, (x - icon_r * 2 - 6, yy - icon_r + 2))
        else:
            _draw_pill_icon(surf, x - icon_r - 4, yy + 4, icon_r, col, sym[0], font_s)

        # ── label ──
        surf.blit(font_s.render(lbl, True, txt_col), (x, yy))

        # ── bar track ──
        bar_x = x + 58
        bar_h = 13
        # track with slight transparency
        track = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(track, (180, 180, 180, 120), (0, 0, bar_w, bar_h), border_radius=6)
        surf.blit(track, (bar_x, yy + 2))

        # fill
        fill_w = max(0, int(bar_w * val / 100))
        if fill_w:
            # gradient-like: lighter left, darker right
            fill = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
            for px in range(fill_w):
                ratio  = px / max(fill_w, 1)
                r = int(col[0] * (0.9 + 0.1 * (1 - ratio)))
                g = int(col[1] * (0.9 + 0.1 * (1 - ratio)))
                b = int(col[2] * (0.9 + 0.1 * (1 - ratio)))
                pygame.draw.line(fill, (r, g, b, 230), (px, 0), (px, bar_h))
            pygame.draw.rect(fill, (255, 255, 255, 60), (0, 0, fill_w, bar_h // 3), border_radius=6)
            surf.blit(fill, (bar_x, yy + 2))

        # border
        pygame.draw.rect(surf, txt_col, (bar_x, yy + 2, bar_w, bar_h), 1, border_radius=6)

        # value text
        surf.blit(font_s.render(f"{int(val)}%", True, mut_col),
                  (bar_x + bar_w + 6, yy + 1))


def draw_coin_row(surf, fonts, state, coin_icon, x, y, dark=False):
    """Compact coin + level pill."""
    txt_col = INK_LIGHT if dark else INK
    mut_col = MUTED_LIGHT if dark else MUTED

    pill_w = 200
    s = pygame.Surface((pill_w, 40), pygame.SRCALPHA)
    bg = PANEL_DARK + (200,) if dark else (255, 248, 215, 210)
    pygame.draw.rect(s, bg, (0, 0, pill_w, 40), border_radius=10)
    pygame.draw.rect(s, txt_col + (100,), (0, 0, pill_w, 40), 1, border_radius=10)
    surf.blit(s, (x, y))

    # coin icon
    ix = x + 7
    if coin_icon:
        ci = scale_to_height(coin_icon, 24)
        surf.blit(ci, (ix, y + 8))
        ix += ci.get_width() + 5
    else:
        pygame.draw.circle(surf, (240, 200, 60), (ix + 10, y + 20), 10)
        ix += 24

    # coins / cap
    surf.blit(fonts["bold_sm"].render(
        f"{state['coins']} / {state['wallet_cap']}", True, txt_col),
        (ix, y + 9))

    # level badge — right edge of pill
    lv_x = x + pill_w - 20
    pygame.draw.circle(surf, ACCENT, (lv_x, y + 20), 16)
    lv_t = fonts["bold_sm"].render(str(state["level"]), True, WHITE)
    surf.blit(lv_t, (lv_x - lv_t.get_width() // 2, y + 20 - lv_t.get_height() // 2))
