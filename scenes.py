"""
Mr Fi 🐸 — v5
scenes.py
"""
import re, math, time, random
import pygame

from config  import (WIN_W, WIN_H, PANEL, PANEL_DARK, INK, INK_LIGHT,
                     MUTED, MUTED_LIGHT, ACCENT, ACCENT2, SKY, WHITE,
                     YELLOW_LIGHT, FOOD_CATALOGUE, FOOD_IMG_H,
                     BACKGROUND_CATALOGUE, DECORATION_CATALOGUE, DARK_BACKGROUNDS)
from assets  import scale_to_height, scale_to_fit
from widgets import Button, is_dark_bg, ink_col, muted_col, panel_col
from audio   import beep
import os
from config import IMG_DIR


# ── helpers ────────────────────────────────────────────────────────────────────

def _text_box(surf, font, text, rect, dark=False):
    bg  = (30, 30, 50, 200) if dark else (255, 255, 255, 220)
    bdr = INK_LIGHT if dark else INK
    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(s, bg,        (0, 0, rect.w, rect.h), border_radius=8)
    pygame.draw.rect(s, bdr+(160,),(0, 0, rect.w, rect.h), 2, border_radius=8)
    surf.blit(s, rect.topleft)
    surf.blit(font.render(text + "|", True, bdr), (rect.x + 8, rect.y + 8))

def _panel(surf, rect, dark=False, alpha=210):
    col = PANEL_DARK if dark else (255, 252, 240)
    s   = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(s, col + (alpha,), (0, 0, rect.w, rect.h), border_radius=16)
    pygame.draw.rect(s, (ink_col(dark)) + (120,), (0, 0, rect.w, rect.h), 2, border_radius=16)
    surf.blit(s, rect.topleft)

def _title(surf, font, text, x, y, dark=False):
    surf.blit(font.render(text, True, ink_col(dark)), (x, y))

def _load_img_raw(fname):
    path = os.path.join(IMG_DIR, fname)
    if os.path.exists(path):
        try:
            return pygame.image.load(path).convert_alpha()
        except Exception:
            pass
    s = pygame.Surface((100, 100), pygame.SRCALPHA)
    s.fill((150, 150, 150, 255))
    return s


# ── Food scene ─────────────────────────────────────────────────────────────────

class FoodScene:
    def draw(self, g):
        dark = is_dark_bg(g.state)
        surf = g.screen
        pr   = pygame.Rect(40, 100, WIN_W - 80, WIN_H - 200)
        _panel(surf, pr, dark)
        _title(surf, g.fonts["bold_sm"], "Food  —  drag onto Mr Fi to feed", 60, 112, dark)

        g.food_rects = []
        x, y = 60, 145
        CW, CH = 115, 150

        for key, name, _p, hunger_val, _img in FOOD_CATALOGUE:
            count = g.state["inventory"].get(key, 0)
            r     = pygame.Rect(x, y, CW, CH)

            # card
            card_col = (255, 245, 230, 200) if count > 0 else (200, 200, 200, 150)
            cs = pygame.Surface((CW, CH), pygame.SRCALPHA)
            pygame.draw.rect(cs, card_col, (0, 0, CW, CH), border_radius=12)
            pygame.draw.rect(cs, INK+(120,), (0, 0, CW, CH), 2, border_radius=12)
            surf.blit(cs, r.topleft)

            img = g.assets.food_imgs.get(key)
            if img:
                sc = scale_to_fit(img, CW - 10, FOOD_IMG_H)
                surf.blit(sc, (r.x + (CW - sc.get_width()) // 2, r.y + 5))

            n = g.fonts["small"].render(name, True, ink_col(dark))
            surf.blit(n, (r.x + (CW - n.get_width()) // 2, r.y + FOOD_IMG_H + 8))
            c = g.fonts["bold_sm"].render(f"x{count}", True, ACCENT if count else MUTED)
            surf.blit(c, (r.x + (CW - c.get_width()) // 2, r.y + FOOD_IMG_H + 26))

            g.food_rects.append((r, key, hunger_val))
            x += CW + 12

        # placed decorations on this panel
        _draw_placed_decos(surf, g)

        g.feed_rect = g._frog_at(WIN_W // 2 + 180, WIN_H // 2 + 30, 220)

        if g.drag_food:
            key, _ = g.drag_food
            mx, my = pygame.mouse.get_pos()
            img = g.assets.food_imgs.get(key)
            if img:
                di = scale_to_fit(img, 70, 70)
                surf.blit(di, (mx - 35, my - 35))

    def handle(self, g, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for r, key, val in getattr(g, "food_rects", []):
                if r.collidepoint(ev.pos) and g.state["inventory"].get(key, 0) > 0:
                    g.drag_food = (key, val)
                    break
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and g.drag_food:
            key, val = g.drag_food
            if hasattr(g, "feed_rect") and g.feed_rect.collidepoint(ev.pos):
                g.state["inventory"][key] = g.state["inventory"].get(key, 0) - 1
                g.state["hunger"]    = min(100, g.state["hunger"] + val)
                g.state["happiness"] = min(100, g.state["happiness"] + val // 2)
                g.set_mood("enjoyed", 2)
                g.show_toast(f"Yum! +{val} hunger 🐸")
                beep(880, 120, 0.3)
            g.drag_food = None


# ── Decoration drag helper ─────────────────────────────────────────────────────

def _draw_placed_decos(surf, g):
    """Delegated to g.deco_mgr.draw() — kept for backward compat."""
    if hasattr(g, "deco_mgr"):
        g.deco_mgr.draw(surf, g.state, g.assets.deco_imgs)


# ── Shop scene — THREE TABS ────────────────────────────────────────────────────

class ShopScene:
    TABS = ["Food ", "Backgrounds ", "Items "]

    def __init__(self):
        self.tab = 0

    def draw(self, g):
        dark = is_dark_bg(g.state)
        surf = g.screen
        pr   = pygame.Rect(40, 100, WIN_W - 80, WIN_H - 200)
        _panel(surf, pr, dark)
        _title(surf, g.fonts["bold_sm"], "Shop", 60, 110, dark)

        # tabs
        g._shop_tab_rects = []
        for i, tab in enumerate(self.TABS):
            tr = pygame.Rect(60 + i * 165, 130, 155, 30)
            active = (i == self.tab)
            tc = pygame.Surface((155, 30), pygame.SRCALPHA)
            bg = ACCENT + (220,) if active else (panel_col(dark) + (180,))
            pygame.draw.rect(tc, bg, (0, 0, 155, 30), border_radius=8)
            pygame.draw.rect(tc, INK+(100,), (0, 0, 155, 30), 1, border_radius=8)
            surf.blit(tc, tr.topleft)
            col = WHITE if active else ink_col(dark)
            t   = g.fonts["normal"].render(tab, True, col)
            surf.blit(t, (tr.x + (155 - t.get_width()) // 2, tr.y + 6))
            g._shop_tab_rects.append(tr)

        if self.tab == 0:
            self._draw_food(g, dark)
        elif self.tab == 1:
            self._draw_backgrounds(g, dark)
        else:
            self._draw_items(g, dark)

    # food tab (same as before)
    def _draw_food(self, g, dark):
        surf = g.screen
        g.shop_rects = []
        x, y = 60, 175
        CW, CH = 130, 175
        for key, name, price, _val, _img in FOOD_CATALOGUE:
            r   = pygame.Rect(x, y, CW, CH)
            can = g.state["coins"] >= price
            cs  = pygame.Surface((CW, CH), pygame.SRCALPHA)
            bg  = (255, 250, 235, 200) if can else (210, 210, 210, 150)
            pygame.draw.rect(cs, bg,      (0, 0, CW, CH), border_radius=14)
            pygame.draw.rect(cs, INK+(100,),(0, 0, CW, CH), 2, border_radius=14)
            surf.blit(cs, r.topleft)
            img = g.assets.food_imgs.get(key)
            if img:
                sc = scale_to_fit(img, CW - 10, FOOD_IMG_H + 10)
                surf.blit(sc, (r.x + (CW - sc.get_width()) // 2, r.y + 5))
            surf.blit(g.fonts["small"].render(name, True, ink_col(dark)),
                      (r.x + 4, r.y + FOOD_IMG_H + 16))
            # price
            ci = g.assets.icons.get("coin")
            py = r.y + FOOD_IMG_H + 36
            if ci:
                cis = scale_to_height(ci, 16)
                surf.blit(cis, (r.x + 8, py))
                surf.blit(g.fonts["small"].render(str(price), True, ACCENT if can else MUTED),
                          (r.x + 28, py + 1))
            g.shop_rects.append((r, key, price, "food"))
            x += CW + 14

        # wallet upgrade
        wy = y + CH + 14
        ur = pygame.Rect(60, wy, 420, 46)
        us = pygame.Surface((420, 46), pygame.SRCALPHA)
        pygame.draw.rect(us, (220, 240, 255, 200), (0, 0, 420, 46), border_radius=10)
        pygame.draw.rect(us, INK+(80,), (0, 0, 420, 46), 1, border_radius=10)
        surf.blit(us, ur.topleft)
        surf.blit(g.fonts["normal"].render("Upgrade wallet  (+400 cap)  —  60 coins", True, ink_col(dark)),
                  (ur.x + 14, ur.y + 14))
        g.shop_wallet = ur

    # background tab
    def _draw_backgrounds(self, g, dark):
        surf = g.screen
        g.shop_bg_rects = []
        x, y = 60, 175
        CW, CH = 200, 155

        for bg_id, name, price, img_file, _ in BACKGROUND_CATALOGUE:
            owned  = bg_id in g.state["owned_backgrounds"]
            active = g.state["active_background"] == bg_id
            r      = pygame.Rect(x, y, CW, CH)

            # thumbnail
            try:
                thumb = pygame.image.load(os.path.join(IMG_DIR, img_file)).convert()
                thumb = pygame.transform.scale(thumb, (CW, CH))
            except Exception:
                thumb = pygame.Surface((CW, CH)); thumb.fill((80, 80, 80))
            surf.blit(thumb, r.topleft)

            # border
            bc = ACCENT if active else ((200, 200, 50) if owned else INK)
            pygame.draw.rect(surf, bc, r, 3, border_radius=8)

            # label bar
            lb = pygame.Surface((CW, 36), pygame.SRCALPHA)
            pygame.draw.rect(lb, (0, 0, 0, 150), (0, 0, CW, 36), border_radius=8)
            surf.blit(lb, (r.x, r.y + CH - 36))
            surf.blit(g.fonts["small"].render(name, True, WHITE), (r.x + 6, r.y + CH - 30))

            # badge
            if active:
                badge = "✓ Active"
                bc2   = ACCENT
            elif owned:
                badge = "Use"
                bc2   = (200, 200, 50)
            else:
                badge = f"🪙 {price}"
                bc2   = ACCENT2
            bt = g.fonts["small"].render(badge, True, WHITE)
            bs = pygame.Surface((bt.get_width() + 16, 22), pygame.SRCALPHA)
            pygame.draw.rect(bs, bc2 + (220,), (0, 0, bs.get_width(), 22), border_radius=8)
            surf.blit(bs, (r.x + CW - bs.get_width() - 6, r.y + 6))
            surf.blit(bt, (r.x + CW - bs.get_width() - 6 + 8, r.y + 8))

            g.shop_bg_rects.append((r, bg_id, price, owned, img_file))
            x += CW + 14
            if x + CW > WIN_W - 50:
                x = 60; y += CH + 14

    # items / decorations tab
    def _draw_items(self, g, dark):
        surf = g.screen
        g.shop_deco_rects = []
        g.item_repo_rects = []
        x, y = 60, 172
        CW, CH = 160, 185

        _title(surf, g.fonts["bold_sm"], "Items — buy and place on your scene", 60, 142, dark)

        # For-sale decorations — ITEMS WHITHOUT BACKGROUND
        for deco_id, name, price, img_file in DECORATION_CATALOGUE:
            owned = deco_id in g.state["owned_decorations"]
            can   = g.state["coins"] >= price
            r     = pygame.Rect(x, y, CW, CH)

            #JUST A TINY BORDER AROUND ITEM
            border_col = ACCENT + (200,) if owned else ((180,180,180,120) if not can else INK+(60,))
            bs = pygame.Surface((CW, CH), pygame.SRCALPHA)
            pygame.draw.rect(bs, border_col, (0, 0, CW, CH), 2, border_radius=14)
            surf.blit(bs, r.topleft)

            # DELETING BACKGROUND FOR ITEMS
            img = g.assets.deco_imgs.get(deco_id)
            if img:
                sc = scale_to_fit(img, CW - 10, 130)
                surf.blit(sc, (r.x + (CW - sc.get_width()) // 2, r.y + 4))

            # NAME AND PRICE
            nt = g.fonts["small"].render(name, True, ink_col(dark))
            surf.blit(nt, (r.x + (CW - nt.get_width()) // 2, r.y + 140))

            badge    = "✓ Owned" if owned else f"🪙 {price}"
            badge_col = ACCENT if owned else (MUTED if not can else ACCENT2)
            bt = g.fonts["small"].render(badge, True, badge_col)
            surf.blit(bt, (r.x + (CW - bt.get_width()) // 2, r.y + 158))

            # BUY BUTTON IT ITS NOT OWNED
            if not owned:
                btn_r = pygame.Rect(r.x + 10, r.y + CH - 28, CW - 20, 24)
                btn_s = pygame.Surface((CW - 20, 24), pygame.SRCALPHA)
                btn_bg = ACCENT + (180,) if can else (150,150,150,120)
                pygame.draw.rect(btn_s, btn_bg, (0, 0, CW-20, 24), border_radius=8)
                surf.blit(btn_s, btn_r.topleft)
                bt2 = g.fonts["small"].render("Buy" if can else "Need more coins", True, WHITE)
                surf.blit(bt2, (btn_r.x + (btn_r.w - bt2.get_width())//2, btn_r.y + 4))

            g.shop_deco_rects.append((r, deco_id, price, owned))
            x += CW + 18

        # ── Repository section ─────────────────────────────────────────────
        ry = y + CH + 24
        surf.blit(g.fonts["bold_sm"].render(
            "Your Items  —  drag to main scene  |  right-click to remove",
            True, ink_col(dark)), (60, ry - 26))

        owned_decos = g.state.get("owned_decorations", [])
        if not owned_decos:
            surf.blit(g.fonts["normal"].render(
                "No items yet — buy one above!", True, MUTED), (60, ry + 10))
        else:
            for i, deco_id in enumerate(owned_decos):
                rr = pygame.Rect(60 + i * 110, ry, 100, 100)
                # BACKGROUND
                rs = pygame.Surface((100, 100), pygame.SRCALPHA)
                # IS IT IN THE SCENE?
                is_placed = any(d["id"] == deco_id
                                for d in g.state.get("placed_decorations", []))
                bdr = ACCENT + (200,) if is_placed else (160,160,160,100)
                pygame.draw.rect(rs, bdr, (0, 0, 100, 100), 2, border_radius=10)
                surf.blit(rs, rr.topleft)

                img = g.assets.deco_imgs.get(deco_id)
                if img:
                    sc = scale_to_fit(img, 90, 90)
                    surf.blit(sc, (rr.x + (100 - sc.get_width())//2,
                                   rr.y + (100 - sc.get_height())//2))

                # PLACED
                if is_placed:
                    pt = g.fonts["small"].render("on scene ✓", True, ACCENT)
                    surf.blit(pt, (rr.x, rr.bottom + 2))

                g.item_repo_rects.append((rr, deco_id))

        # drag preview WITH SHADOW
        if g.drag_deco:
            mx, my = pygame.mouse.get_pos()
            img = g.assets.deco_imgs.get(g.drag_deco)
            if img:
                sc = scale_to_fit(img, 85, 85)
                # SHADOW
                shadow = pygame.Surface((sc.get_width()+6, sc.get_height()+6), pygame.SRCALPHA)
                shadow.fill((0, 0, 0, 60))
                surf.blit(shadow, (mx - sc.get_width()//2 + 3, my - sc.get_height()//2 + 3))
                surf.blit(sc, (mx - sc.get_width()//2, my - sc.get_height()//2))
                # GUIDE
                hint = g.fonts["small"].render("Drop on main scene!", True, ACCENT)
                surf.blit(hint, (mx - hint.get_width()//2, my - sc.get_height()//2 - 20))

    def handle(self, g, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            # tab switch
            for i, tr in enumerate(getattr(g, "_shop_tab_rects", [])):
                if tr.collidepoint(ev.pos):
                    self.tab = i; return

            if self.tab == 0:
                for r, key, price, kind in getattr(g, "shop_rects", []):
                    if r.collidepoint(ev.pos):
                        g.shop_buy_food(key, price); return
                if hasattr(g, "shop_wallet") and g.shop_wallet.collidepoint(ev.pos):
                    if g.state["coins"] >= 60:
                        g.state["coins"] -= 60
                        g.state["wallet_cap"] += 400
                        g.show_toast("Wallet upgraded! 💰")
                    else:
                        g.show_toast("Not enough coins")

            elif self.tab == 1:
                for r, bg_id, price, owned, _ in getattr(g, "shop_bg_rects", []):
                    if r.collidepoint(ev.pos):
                        if owned:
                            g.state["active_background"] = bg_id
                            g.show_toast(f"Background changed! 🌄")
                        elif g.state["coins"] >= price:
                            g.state["coins"] -= price
                            g.state["owned_backgrounds"].append(bg_id)
                            g.state["active_background"] = bg_id
                            g.show_toast(f"Background unlocked! 🎉")
                        else:
                            g.show_toast(f"Need {price} coins 💸")
                        return

            elif self.tab == 2:
                # buy deco
                for r, deco_id, price, owned in getattr(g, "shop_deco_rects", []):
                    if r.collidepoint(ev.pos) and not owned:
                        if g.state["coins"] >= price:
                            g.state["coins"] -= price
                            g.state["owned_decorations"].append(deco_id)
                            g.show_toast("Item bought! Place it in your scene 🌸")
                        else:
                            g.show_toast(f"Need {price} coins 💸")
                        return
                # start drag from repo
                for rr, deco_id in getattr(g, "item_repo_rects", []):
                    if rr.collidepoint(ev.pos):
                        g.drag_deco = deco_id; return

        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and g.drag_deco:
            # drop onto scene — save position
            mx, my = pygame.mouse.get_pos()
            placed = g.state.setdefault("placed_decorations", [])
            # remove existing placement of same deco then re-add
            placed[:] = [d for d in placed if d["id"] != g.drag_deco]
            placed.append({"id": g.drag_deco, "x": mx, "y": my})
            g.show_toast("Decoration placed! 🌸")
            g.drag_deco = None


# ── Mode 1 ─────────────────────────────────────────────────────────────────────

class Mode1Scene:
    def draw(self, g):
        dark = is_dark_bg(g.state)
        surf = g.screen
        pr = pygame.Rect(35, 98, WIN_W - 75, WIN_H - 195)
        _panel(surf, pr, dark)
        _title(surf, g.fonts["bold_sm"], "Talk to Mr Fi  —  DeepSeek AI 🤖", 55, 110, dark)

        # chat log
        y = 138
        for who, txt in g.m1_log[-11:]:
            is_thinking = (txt == "...")
            col = (150, 220, 150) if is_thinking else (ACCENT if who == "mrfi" else ink_col(dark))
            prefix = "Mr Fi: " if who == "mrfi" else "You: "
            display = (prefix + txt)[:88]
            surf.blit(g.fonts["normal"].render(display, True, col), (55, y))
            y += 23

        # thinking indicator — animated dots
        if g.m1_thinking:
            dots = "." * (int(time.time() * 3) % 4)
            t = g.fonts["small"].render(f"Mr Fi is thinking{dots}", True, (150, 220, 150))
            surf.blit(t, (55, y + 4))

        g._frog_at(WIN_W - 145, WIN_H - 195, 145)
        box = pygame.Rect(55, WIN_H - 152, WIN_W - 330, 36)
        placeholder = "" if g.m1_thinking else g.m1_input
        _text_box(surf, g.fonts["normal"], placeholder, box, dark)
        hint = "Waiting for AI..." if g.m1_thinking else "Enter to send  |  Powered by DeepSeek 🚀"
        surf.blit(g.fonts["small"].render(hint, True, muted_col(dark)), (55, WIN_H - 112))

    def handle(self, g, ev):
        if ev.type == pygame.KEYDOWN:
            if g.m1_thinking:
                return   # WAIT FOR ANSWER
            if ev.key == pygame.K_RETURN:
                g.m1_send()
            elif ev.key == pygame.K_BACKSPACE:
                g.m1_input = g.m1_input[:-1]
            elif ev.unicode and ev.unicode.isprintable() and len(g.m1_input) < 80:
                g.m1_input += ev.unicode


# ── Mode 2 — BERT Fill-Mask  +  Classic Puzzles ──────────────────────────────

class Mode2Scene:

    def draw(self, g):
        dark = is_dark_bg(g.state)
        surf = g.screen
        b = g.bert
        pr = pygame.Rect(35, 98, WIN_W - 75, WIN_H - 195)
        _panel(surf, pr, dark)

        # ── IN MAIN TAB ───────────────────────────────────────────────────────
        g._m2_tab_rects = []
        for i, (lbl, key) in enumerate([("Classic Puzzle 🎮", "classic"),
                                         ("BERT Fill-[MASK] 🤖", "bert")]):
            tr  = pygame.Rect(35 + i * 280, 98, 272, 32)
            ts  = pygame.Surface((272, 32), pygame.SRCALPHA)
            act = getattr(g, "_m2_tab", "classic") == key
            pygame.draw.rect(ts, (ACCENT if act else panel_col(dark)) + (220,),
                             (0,0,272,32), border_radius=9)
            surf.blit(ts, tr.topleft)
            tc = WHITE if act else ink_col(dark)
            t  = g.fonts["bold_sm"].render(lbl, True, tc)
            surf.blit(t, (tr.x + (272 - t.get_width())//2, tr.y + 5))
            g._m2_tab_rects.append((tr, key))

        tab = getattr(g, "_m2_tab", "classic")
        if tab == "classic":
            self._draw_classic(g, dark, surf, b)
        else:
            self._draw_bert(g, dark, surf, b)

    # ── Classic tab ───────────────────────────────────────────────────────────

    def _draw_classic(self, g, dark, surf, b):
        cs = b.classic_state
        _title(surf, g.fonts["bold_sm"], "Classic Puzzle", 55, 140, dark)

        surf.blit(g.fonts["small"].render(
            f"Score: {b.score}   Streak: {b.streak}🔥",
            True, ACCENT2), (WIN_W - 280, 140))

        if cs.get("kind") == "seq":
            seq_str = ", ".join(str(n) for n in cs["seq"]) + ",  ?"
            surf.blit(g.fonts["xlarge"].render(seq_str, True, ink_col(dark)), (55, 176))
            surf.blit(g.fonts["normal"].render(
                "What comes next? Type the number.",
                True, muted_col(dark)), (55, 222))
        else:
            surf.blit(g.fonts["xlarge"].render(
                cs.get("scrambled","").upper(), True, ink_col(dark)), (55, 176))
            surf.blit(g.fonts["normal"].render(
                "Unscramble the word above.",
                True, muted_col(dark)), (55, 222))

        # input
        _text_box(surf, g.fonts["normal"], cs.get("input",""),
                  pygame.Rect(55, 258, 320, 38), dark)

        # result
        if cs.get("result"):
            rc = (80,200,80) if "✅" in cs["result"] else (220,80,80)
            surf.blit(g.fonts["bold_sm"].render(cs["result"], True, rc), (55, 308))

        # buttons
        g._classic_btns = []
        for i, (lbl, act) in enumerate([("Check ✓","check"),
                                         ("New ⟶",  "new")]):
            br = pygame.Rect(55 + i*130, 348, 118, 38)
            bs = pygame.Surface((118,38), pygame.SRCALPHA)
            col = [(90,180,90),(90,140,210)][i]
            pygame.draw.rect(bs, col+(210,), (0,0,118,38), border_radius=9)
            surf.blit(bs, br.topleft)
            surf.blit(g.fonts["normal"].render(lbl, True, WHITE), (br.x+12, br.y+9))
            g._classic_btns.append((br, act))

        g._frog_at(WIN_W - 145, WIN_H - 195, 145)
        surf.blit(g.fonts["small"].render(
            "Enter = Check  |  No install needed ✅",
            True, muted_col(dark)), (55, WIN_H - 108))

    # ── BERT tab ─────────────────────────────────────────────────────────────

    def _draw_bert(self, g, dark, surf, b):
        # status
        if b.bert_error:
            sc = (220, 80, 80)
        elif b.bert_ready:
            sc = (80, 220, 80)
        else:
            sc = (220, 180, 60)
        st = ("✅ DistilBERT Ready" if b.bert_ready else
              f"⚠️  {b.bert_error}" if b.bert_error else
              f"⏳ {b.bert_progress}")
        surf.blit(g.fonts["small"].render(st, True, sc), (55, 140))
        surf.blit(g.fonts["small"].render(
            f"Score: {b.score}  Streak: {b.streak}🔥",
            True, ACCENT2), (WIN_W - 280, 140))

        # load button if its not loaded
        if not b.bert_ready and not b.bert_loading:
            lr = pygame.Rect(55, 168, 300, 44)
            ls = pygame.Surface((300,44), pygame.SRCALPHA)
            pygame.draw.rect(ls, ACCENT+(220,), (0,0,300,44), border_radius=10)
            surf.blit(ls, lr.topleft)
            surf.blit(g.fonts["bold_sm"].render(
                "▶  Load DistilBERT Model", True, WHITE), (lr.x+16, lr.y+10))
            g._bert_load_rect = lr
            surf.blit(g.fonts["small"].render(
                "First time: downloads ~250MB  |  pip install transformers torch",
                True, muted_col(dark)), (55, 222))
            surf.blit(g.fonts["small"].render(
                "After download, works offline!",
                True, muted_col(dark)), (55, 242))
            return

        if b.bert_loading:
            import math as _m
            dots = "." * (int(time.time()*3) % 4)
            surf.blit(g.fonts["xlarge"].render(
                f"Loading{dots}", True, ink_col(dark)), (55, 175))
            surf.blit(g.fonts["normal"].render(
                b.bert_progress, True, muted_col(dark)), (55, 215))
            return

        # puzzle type tabs
        g._bert_type_rects = []
        TYPE_LABELS = [("both","All 🔀"),("science","Science 🔬"),("fun","Fun 🎮")]
        for i, (tkey, tlbl) in enumerate(TYPE_LABELS):
            tr = pygame.Rect(55 + i*125, 160, 115, 24)
            ts = pygame.Surface((115,24), pygame.SRCALPHA)
            active = (b.puzzle_type == tkey)
            pygame.draw.rect(ts, (ACCENT if active else panel_col(dark))+(200,),
                             (0,0,115,24), border_radius=6)
            surf.blit(ts, tr.topleft)
            surf.blit(g.fonts["small"].render(tlbl, True,
                      WHITE if active else ink_col(dark)), (tr.x+8, tr.y+4))
            g._bert_type_rects.append((tr, tkey))

        #  [MASK] highlight
        if not b.current_sentence:
            b.new_bert_puzzle()

        parts = b.current_sentence.split("[MASK]")
        px, py = 55, 196
        surf.blit(g.fonts["bold_sm"].render(parts[0], True, ink_col(dark)), (px, py))
        w0 = g.fonts["bold_sm"].size(parts[0])[0]
        ms = pygame.Surface((88, 28), pygame.SRCALPHA)
        pygame.draw.rect(ms, (255,200,60,210), (0,0,88,28), border_radius=6)
        surf.blit(ms, (px+w0, py-2))
        surf.blit(g.fonts["bold_sm"].render("[MASK]", True, (70,35,0)),
                  (px+w0+4, py))
        if len(parts) > 1:
            surf.blit(g.fonts["bold_sm"].render(parts[1], True, ink_col(dark)),
                      (px+w0+90, py))

        # BERT predictions bar chart
        py2 = 234
        if b.predictions:
            surf.blit(g.fonts["small"].render("BERT predictions:", True, muted_col(dark)), (55, py2))
            for i, (word, score) in enumerate(b.predictions[:5]):
                bw  = max(4, int(150 * score / 100))
                brs = pygame.Surface((bw, 13), pygame.SRCALPHA)
                pygame.draw.rect(brs, ACCENT+(190,), (0,0,bw,13), border_radius=4)
                surf.blit(brs, (55 + i*165, py2+16))
                surf.blit(g.fonts["small"].render(f"{word} {score}%", True, ink_col(dark)),
                          (55 + i*165, py2+32))
        elif b.bert_ready:
            surf.blit(g.fonts["small"].render("Analysing…", True, muted_col(dark)), (55, py2))

        # result
        if b.result_msg:
            rc = (80,210,80) if "✅" in b.result_msg else (220,80,80)
            surf.blit(g.fonts["bold_sm"].render(b.result_msg, True, rc), (55, 278))

        # input + buttons
        _text_box(surf, g.fonts["normal"], b.user_input,
                  pygame.Rect(55, 312, 360, 36), dark)
        g._bert_btns = []
        for i, (lbl, act) in enumerate([("Check ✓","check"),
                                          ("Hint 💡","hint"),
                                          ("Skip ⟶","skip")]):
            br = pygame.Rect(430 + i*115, 312, 106, 36)
            bs = pygame.Surface((106,36), pygame.SRCALPHA)
            col = [(90,180,90),(90,160,210),(210,130,60)][i]
            pygame.draw.rect(bs, col+(210,), (0,0,106,36), border_radius=9)
            surf.blit(bs, br.topleft)
            surf.blit(g.fonts["normal"].render(lbl, True, WHITE), (br.x+8, br.y+8))
            g._bert_btns.append((br, act))

        g._frog_at(WIN_W - 145, WIN_H - 195, 145)
        surf.blit(g.fonts["small"].render(
            "Enter = Check answer",
            True, muted_col(dark)), (55, WIN_H - 108))

    # ── handle ────────────────────────────────────────────────────────────────

    def handle(self, g, ev):
        b   = g.bert
        tab = getattr(g, "_m2_tab", "classic")

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            # tab switch
            for tr, key in getattr(g, "_m2_tab_rects", []):
                if tr.collidepoint(ev.pos):
                    g._m2_tab = key; return

            if tab == "classic":
                for br, act in getattr(g, "_classic_btns", []):
                    if br.collidepoint(ev.pos):
                        if act == "check":
                            ok = b.check_classic()
                            if ok:
                                g.add_xp(10); g.add_coin(1)
                                g.set_mood("happy", 2)
                            else:
                                g.set_mood("sad", 1.5)
                            import threading, time
                            def _next():
                                time.sleep(1.4)
                                b._new_classic()
                                b.classic_state["result"] = ""
                            threading.Thread(target=_next, daemon=True).start()
                        elif act == "new":
                            b._new_classic()
                        return
            else:
                # BERT tab
                if hasattr(g,"_bert_load_rect") and g._bert_load_rect.collidepoint(ev.pos):
                    b.start_bert_loading(); return
                for tr, tkey in getattr(g,"_bert_type_rects",[]):
                    if tr.collidepoint(ev.pos):
                        b.puzzle_type = tkey; b.new_bert_puzzle(); return
                for br, act in getattr(g,"_bert_btns",[]):
                    if br.collidepoint(ev.pos):
                        if act == "check":   g.m2_bert_check()
                        elif act == "hint":  b.result_msg = b.get_hint()
                        elif act == "skip":  b.new_bert_puzzle(); b.result_msg = ""
                        return

        if ev.type == pygame.KEYDOWN:
            if tab == "classic":
                cs = b.classic_state
                if ev.key == pygame.K_RETURN:
                    ok = b.check_classic()
                    if ok: g.add_xp(10); g.add_coin(1); g.set_mood("happy",2)
                    else:  g.set_mood("sad",1.5)
                elif ev.key == pygame.K_BACKSPACE:
                    cs["input"] = cs.get("input","")[:-1]
                elif ev.unicode and ev.unicode.isprintable() and len(cs.get("input","")) < 30:
                    cs["input"] = cs.get("input","") + ev.unicode
            else:
                if ev.key == pygame.K_RETURN:
                    g.m2_bert_check()
                elif ev.key == pygame.K_BACKSPACE:
                    b.user_input = b.user_input[:-1]
                elif ev.unicode and ev.unicode.isprintable() and len(b.user_input) < 40:
                    b.user_input += ev.unicode


# ── Mode 3 ─────────────────────────────────────────────────────────────────────

class Mode3Scene:
    def draw(self, g):
        dark = is_dark_bg(g.state)
        surf = g.screen
        pr   = pygame.Rect(40, 100, WIN_W - 80, WIN_H - 200)
        _panel(surf, pr, dark)
        _title(surf, g.fonts["bold_sm"], "Brain Games (Mode 3)", 60, 112, dark)

        for i, (name, kind) in enumerate([("Sequences", "math"), ("Word", "word"), ("Sudoku", "sudoku")]):
            r = pygame.Rect(60 + i * 130, 132, 120, 28)
            col = ACCENT if g.m3_kind == kind else panel_col(dark)
            rs = pygame.Surface((120, 28), pygame.SRCALPHA)
            pygame.draw.rect(rs, col + (220,), (0, 0, 120, 28), border_radius=8)
            pygame.draw.rect(rs, INK+(100,), (0, 0, 120, 28), 1, border_radius=8)
            surf.blit(rs, r.topleft)
            t = g.fonts["normal"].render(name, True, WHITE if g.m3_kind == kind else ink_col(dark))
            surf.blit(t, (r.x + (120 - t.get_width()) // 2, r.y + 5))

        if not g.m3_kind:
            surf.blit(g.fonts["normal"].render("Pick a game above.", True, muted_col(dark)), (60, 185))
            return

        if g.m3_kind == "math":
            seq_str = ", ".join(str(n) for n in g.m3_payload["seq"]) + ", ?"
            surf.blit(g.fonts["xlarge"].render(seq_str, True, ink_col(dark)), (60, 200))
            _text_box(surf, g.fonts["normal"], g.m3_input, pygame.Rect(60, 250, 260, 36), dark)
        elif g.m3_kind == "word":
            surf.blit(g.fonts["xlarge"].render(g.m3_payload["scrambled"].upper(), True, ink_col(dark)), (60, 200))
            _text_box(surf, g.fonts["normal"], g.m3_input, pygame.Rect(60, 250, 260, 36), dark)
        elif g.m3_kind == "sudoku":
            p, sel = g.m3_payload["puzzle"], g.m3_payload["selected"]
            ox, oy, cs2 = 60, 180, 56
            for row in range(4):
                for col in range(4):
                    rect = pygame.Rect(ox + col * cs2, oy + row * cs2, cs2, cs2)
                    fill = (255, 250, 200) if (row, col) == sel else (255, 255, 255)
                    pygame.draw.rect(surf, fill, rect)
                    pygame.draw.rect(surf, INK,  rect, 2)
                    if p[row][col]:
                        t = g.fonts["xlarge"].render(str(p[row][col]), True, INK)
                        surf.blit(t, (rect.x + 16, rect.y + 10))

        # buttons
        bx = WIN_W - 220
        for i, (lbl, cb) in enumerate([("Check", g.m3_check), ("Skip", g.m3_skip),
                                        ("New",   lambda: g.m3_new(g.m3_kind))]):
            r = pygame.Rect(bx, 190 + i * 52, 160, 42)
            rs = pygame.Surface((160, 42), pygame.SRCALPHA)
            pygame.draw.rect(rs, panel_col(dark) + (200,), (0, 0, 160, 42), border_radius=10)
            pygame.draw.rect(rs, INK+(120,), (0, 0, 160, 42), 2, border_radius=10)
            surf.blit(rs, r.topleft)
            surf.blit(g.fonts["normal"].render(lbl, True, ink_col(dark)), (r.x + 12, r.y + 11))
            setattr(g, f"_m3btn_{i}", (r, cb))

        g._frog_at(WIN_W - 150, WIN_H - 200, 160)

        if g.m3_show_dialogue and g.m3_dialogue:
            bar = pygame.Rect(60, WIN_H - 140, WIN_W - 260, 50)
            bs  = pygame.Surface((bar.w, bar.h), pygame.SRCALPHA)
            pygame.draw.rect(bs, (255, 255, 200, 210), (0, 0, bar.w, bar.h), border_radius=10)
            pygame.draw.rect(bs, INK+(150,), (0, 0, bar.w, bar.h), 2, border_radius=10)
            surf.blit(bs, bar.topleft)
            surf.blit(g.fonts["bold_sm"].render(g.m3_dialogue, True, INK), (bar.x + 12, bar.y + 12))

    def handle(self, g, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for i, (name, kind) in enumerate([("Sequences", "math"), ("Word", "word"), ("Sudoku", "sudoku")]):
                if pygame.Rect(60 + i * 130, 132, 120, 28).collidepoint(ev.pos):
                    g.m3_new(kind); return
            for i in range(3):
                pair = getattr(g, f"_m3btn_{i}", None)
                if pair and pair[0].collidepoint(ev.pos):
                    pair[1](); return
            if g.m3_kind == "sudoku":
                ox, oy, cs2 = 60, 180, 56
                for row in range(4):
                    for col in range(4):
                        if pygame.Rect(ox + col * cs2, oy + row * cs2, cs2, cs2).collidepoint(ev.pos):
                            g.m3_payload["selected"] = (row, col)
        if ev.type == pygame.KEYDOWN:
            if g.m3_kind in ("math", "word"):
                if ev.key == pygame.K_RETURN: g.m3_check()
                elif ev.key == pygame.K_BACKSPACE: g.m3_input = g.m3_input[:-1]
                elif ev.unicode and ev.unicode.isprintable() and len(g.m3_input) < 20:
                    g.m3_input += ev.unicode
            elif g.m3_kind == "sudoku":
                if ev.key == pygame.K_RETURN: g.m3_check()
                elif ev.unicode in ("1","2","3","4"):
                    r2, c2 = g.m3_payload["selected"]
                    g.m3_payload["puzzle"][r2][c2] = int(ev.unicode)


# ── Bedroom ────────────────────────────────────────────────────────────────────

class BedroomScene:
    def draw(self, g):
        surf = g.screen
        g._frog_at(WIN_W // 2, WIN_H // 2 + 20, 200)
        remain = max(0, int(g.sleep_end - time.time()))
        mm, ss = divmod(remain, 60)
        t = g.fonts["xlarge"].render(f"💤 {mm:02d}:{ss:02d}", True, (220, 240, 255))
        surf.blit(t, (WIN_W // 2 - t.get_width() // 2, 110))
        if remain == 0:
            g.state["energy"] = 100
            g.sleep_end = 0
            g.set_mood("happy", 2)
            g.scene = "main"

    def handle(self, g, ev):
        pass


# ── Weather ────────────────────────────────────────────────────────────────────

# ── Weather ────────────────────────────────────────────────────────────────────

class WeatherScene:
    """
    Weather با انتخاب استان → شهر
    • threading: fetch در background — بازی فریز نمیشه
    • WeatherAPI (key) اول امتحان میشه، اگه نشد open-meteo (بدون key)
    • هر دو روی نت ملی ایران کار میکنن
    """

    WEATHERAPI_KEY = "24a2cc61070bb818b281fe242184ba48"

    # استان → شهرها (lat, lon)
    PROVINCES = {
        "Tehran":        {"Tehran":(35.69,51.39),"Karaj":(35.84,50.94),"Varamin":(35.32,51.65),"Shemiranat":(35.81,51.44)},
        "Isfahan":       {"Isfahan":(32.65,51.67),"Kashan":(33.98,51.44),"Najafabad":(32.63,51.37),"Shahinshahr":(32.86,51.55)},
        "Fars":          {"Shiraz":(29.59,52.58),"Marvdasht":(29.87,52.81),"Jahrom":(28.50,53.56),"Fasa":(28.94,53.65)},
        "Khorasan Razavi":{"Mashhad":(36.30,59.61),"Nishapur":(36.21,58.80),"Sabzevar":(36.21,57.68),"Torbat":(35.24,59.22)},
        "East Azerbaijan":{"Tabriz":(38.08,46.29),"Maragheh":(37.40,46.24),"Marand":(38.43,45.77),"Ahar":(38.48,47.07)},
        "Khuzestan":     {"Ahvaz":(31.32,48.67),"Dezful":(32.38,48.40),"Abadan":(30.34,48.30),"Khorramshahr":(30.44,48.17)},
        "Gilan":         {"Rasht":(37.28,49.59),"Anzali":(37.47,49.46),"Lahijan":(37.20,50.00),"Astara":(38.43,48.87)},
        "Mazandaran":    {"Sari":(36.56,53.06),"Babol":(36.55,52.68),"Amol":(36.47,52.35),"Chalus":(36.64,51.42)},
        "Kerman":        {"Kerman":(30.28,57.07),"Zarand":(30.81,56.57),"Jiroft":(28.68,57.74),"Rafsanjan":(30.41,55.99)},
        "Yazd":          {"Yazd":(31.90,54.37),"Meybod":(32.25,54.02),"Ardakan":(32.01,54.02),"Taft":(31.74,54.21)},
        "Semnan":        {"Semnan":(35.57,53.40),"Shahroud":(36.42,54.98),"Damghan":(36.17,54.35),"Garmsar":(35.22,52.34)},
        "Hormozgan":     {"Bandar Abbas":(27.19,56.27),"Minab":(27.15,57.08),"Qeshm":(26.96,56.27),"Kish":(26.54,53.98)},
        "West Azerbaijan":{"Urmia":(37.55,45.07),"Khoy":(38.55,44.96),"Mahabad":(36.77,45.72),"Miandoab":(36.96,46.10)},
        "Kermanshah":    {"Kermanshah":(34.31,47.07),"Islamabad":(34.12,46.46),"Kangavar":(34.50,47.97),"Harsin":(34.27,47.58)},
        "Bushehr":       {"Bushehr":(28.97,50.84),"Borazjan":(29.27,51.21),"Jam":(27.82,52.32),"Kangan":(27.83,52.06)},
        "Golestan":      {"Gorgan":(36.84,54.44),"Gonbad":(37.25,55.17),"Aliabad":(36.91,54.87),"Kordkuy":(36.79,54.12)},
        "Lorestan":      {"Khorramabad":(33.49,48.36),"Borujerd":(33.90,48.76),"Dorud":(33.49,49.06),"Aligudarz":(33.40,49.70)},
        "Hamedan":       {"Hamedan":(34.80,48.51),"Malayer":(34.30,48.82),"Nahavand":(34.19,48.37),"Tuyserkan":(34.54,48.45)},
        "Chaharmahal":   {"Shahrekord":(32.33,50.86),"Borujen":(31.97,51.29),"Farsan":(31.99,50.59),"Lordegan":(31.52,50.83)},
        "Zanjan":        {"Zanjan":(36.68,48.50),"Abhar":(36.15,49.22),"Khodabandeh":(36.32,48.74),"Mahneshan":(36.77,47.67)},
    }

    WMO = {
        0:"Clear ☀", 1:"Mainly clear 🌤", 2:"Partly cloudy ⛅", 3:"Overcast ☁️",
        45:"Fog 🌫", 51:"Drizzle 🌦", 61:"Rain 🌧", 63:"Rain 🌧", 65:"Heavy rain 🌧",
        71:"Snow 🌨", 73:"Snow 🌨", 75:"Heavy snow ❄️",
        80:"Showers 🌦", 95:"Thunderstorm ⛈",
    }

    def __init__(self):
        self._province = "Tehran"
        self._city = "Tehran"
        self._cache = None
        self._loading = False
        self._prov_rects = []
        self._city_rects = []
        self._ref_rect = None
        self._scroll = 0   # province list scroll

    # ── fetch in background thread ────────────────────────────────────────────

    def _trigger_fetch(self, city, coords):
        if self._loading: return
        self._loading = True
        self._cache   = None
        import threading
        threading.Thread(target=self._fetch_bg,
                         args=(city, coords), daemon=True).start()

    def _fetch_bg(self, city, coords):
        import urllib.request, json, urllib.parse
        lat, lon = coords
        lines = []
        try:
            # WeatherAPI
            url = (f"http://api.weatherapi.com/v1/forecast.json"
                   f"?key={self.WEATHERAPI_KEY}"
                   f"&q={lat},{lon}&days=3&aqi=no&lang=en")
            with urllib.request.urlopen(url, timeout=8) as r:
                d   = json.loads(r.read())
            cur  = d["current"]
            fore = d["forecast"]["forecastday"]
            lines = [
                f"📍 {city}  ({self._province})",
                f"🌡  {cur['temp_c']}°C  (feels {cur['feelslike_c']}°C)",
                f"☁️  {cur['condition']['text']}",
                f"💨  Wind {cur['wind_kph']} km/h {cur['wind_dir']}",
                f"💧  Humidity {cur['humidity']}%  |  UV {cur.get('uv','-')}",
                "", "📅 3-Day:",
            ]
            for day in fore:
                dv = day["day"]
                lines.append(f"  {day['date']}:  "
                             f"{dv['mintemp_c']}–{dv['maxtemp_c']}°C  "
                             f"{dv['condition']['text']}")
        except Exception:
            # open-meteo fallback
            try:
                url2 = (f"https://api.open-meteo.com/v1/forecast"
                        f"?latitude={lat}&longitude={lon}"
                        f"&current_weather=true"
                        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
                        f"&timezone=Asia%2FTehran&forecast_days=3")
                with urllib.request.urlopen(url2, timeout=8) as r2:
                    d2 = json.loads(r2.read())
                cw = d2["current_weather"]
                wmo = self.WMO.get(int(cw.get("weathercode",0)), "?")
                temp = cw.get("temperature","?")
                lines = [
                    f"📍 {city}  (open-meteo)",
                    f"🌡  {temp}°C  —  {wmo}",
                    f"💨  Wind {cw.get('windspeed','?')} km/h",
                    "", "📅 3-Day:",
                ]
                daily = d2.get("daily",{})
                dates = daily.get("time",[])
                t_max = daily.get("temperature_2m_max",[])
                t_min = daily.get("temperature_2m_min",[])
                precip = daily.get("precipitation_sum",[])
                for i in range(min(3, len(dates))):
                    lines.append(f"  {dates[i]}: {t_min[i]}–{t_max[i]}°C  🌧{precip[i]}mm")
            except Exception as e2:
                lines = ["❌ Could not fetch weather.", str(e2)[:60],
                         "", "Check internet connection."]

        # advice
        try:
            t = float(lines[1].split("°")[0].split()[-1])
            advice = ("Stay hydrated 💧" if t>35 else "Nice day! 🌿" if t>20
                      else "Wear a jacket 🧥" if t>10 else "Stay warm! ☕")
            lines += ["", f"🐸 Mr Fi says: {advice}"]
        except: pass

        self._cache = lines
        self._loading = False

    # ── draw ─────────────────────────────────────────────────────────────────

    def draw(self, g):
        dark = is_dark_bg(g.state)
        surf = g.screen
        pr   = pygame.Rect(35, 98, WIN_W - 75, WIN_H - 195)
        _panel(surf, pr, dark)
        _title(surf, g.fonts["bold_sm"], "Weather ☁️", 55, 110, dark)

        # ── province list (left column) ──────────────────────────────────────
        provs = list(self.PROVINCES.keys())
        self._prov_rects = []
        px, py0, pw, ph, pgap = 55, 136, 155, 22, 3
        for i, prov in enumerate(provs):
            pr2 = pygame.Rect(px, py0 + i*(ph+pgap), pw, ph)
            if pr2.bottom > WIN_H - 110: break   # clip
            ps  = pygame.Surface((pw, ph), pygame.SRCALPHA)
            act = (prov == self._province)
            pygame.draw.rect(ps, (ACCENT if act else panel_col(dark))+(200,),
                             (0,0,pw,ph), border_radius=6)
            surf.blit(ps, pr2.topleft)
            surf.blit(g.fonts["small"].render(prov, True,
                      WHITE if act else ink_col(dark)), (pr2.x+6, pr2.y+4))
            self._prov_rects.append((pr2, prov))

        # ── city list (middle column) ─────────────────────────────────────────
        cities = list(self.PROVINCES.get(self._province, {}).keys())
        self._city_rects = []
        cx2, cy0, cw, cph = 220, 136, 145, 28
        surf.blit(g.fonts["small"].render(self._province, True, ACCENT2), (cx2, 118))
        for i, city in enumerate(cities):
            cr = pygame.Rect(cx2, cy0 + i*(cph+3), cw, cph)
            cs = pygame.Surface((cw, cph), pygame.SRCALPHA)
            act = (city == self._city)
            pygame.draw.rect(cs, (ACCENT2 if act else panel_col(dark))+(200,),
                             (0,0,cw,cph), border_radius=7)
            surf.blit(cs, cr.topleft)
            surf.blit(g.fonts["small"].render(city, True,
                      WHITE if act else ink_col(dark)), (cr.x+8, cr.y+6))
            self._city_rects.append((cr, city))

        # ── weather data (right panel) ────────────────────────────────────────
        wx = 380
        if self._cache is None and not self._loading:
            coords = self.PROVINCES.get(self._province, {}).get(self._city, (35.69, 51.39))
            self._trigger_fetch(self._city, coords)

        if self._loading:
            dots = "." * (int(time.time()*3) % 4)
            surf.blit(g.fonts["xlarge"].render(f"Loading{dots}", True, ink_col(dark)), (wx, 150))
        elif self._cache:
            for i, line in enumerate(self._cache):
                surf.blit(g.fonts["normal"].render(line, True, ink_col(dark)),
                          (wx, 136 + i*26))

        # refresh button
        rr = pygame.Rect(WIN_W - 155, 110, 110, 26)
        rs = pygame.Surface((110, 26), pygame.SRCALPHA)
        pygame.draw.rect(rs, ACCENT2+(200,), (0,0,110,26), border_radius=7)
        surf.blit(rs, rr.topleft)
        surf.blit(g.fonts["small"].render("↺ Refresh", True, WHITE), (rr.x+20, rr.y+5))
        self._ref_rect = rr

        g._frog_at(WIN_W - 130, WIN_H - 185, 130)

    # ── handle ────────────────────────────────────────────────────────────────

    def handle(self, g, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self._ref_rect and self._ref_rect.collidepoint(ev.pos):
                self._cache = None
                coords = self.PROVINCES.get(self._province,{}).get(self._city,(35.69,51.39))
                self._trigger_fetch(self._city, coords)
                return
            for pr2, prov in self._prov_rects:
                if pr2.collidepoint(ev.pos) and prov != self._province:
                    self._province = prov
                    #
                    cities = list(self.PROVINCES.get(prov, {}).keys())
                    if cities:
                        self._city = cities[0]
                        self._cache = None
                        coords = self.PROVINCES[prov][self._city]
                        self._trigger_fetch(self._city, coords)
                    return
            for cr, city in self._city_rects:
                if cr.collidepoint(ev.pos) and city != self._city:
                    self._city  = city
                    self._cache = None
                    coords = self.PROVINCES.get(self._province,{}).get(city,(35.69,51.39))
                    self._trigger_fetch(city, coords)
                    return


# ── Menu ───────────────────────────────────────────────────────────────────────

class MenuScene:
    def draw(self, g):
        dark = is_dark_bg(g.state)
        surf = g.screen
        pr   = pygame.Rect(40, 100, WIN_W - 80, WIN_H - 200)
        _panel(surf, pr, dark)
        _title(surf, g.fonts["bold_sm"], "Menu", 60, 112, dark)
        g.menu_rects = []
        for i, (lbl, cb) in enumerate([("Save Game", g.menu_save),
                                        ("Load Game", g.menu_load),
                                        ("Quit",      g.menu_quit)]):
            r  = pygame.Rect(60, 148 + i * 60, 260, 46)
            rs = pygame.Surface((260, 46), pygame.SRCALPHA)
            pygame.draw.rect(rs, (255,255,255,180), (0, 0, 260, 46), border_radius=10)
            pygame.draw.rect(rs, INK+(120,), (0, 0, 260, 46), 2, border_radius=10)
            surf.blit(rs, r.topleft)
            surf.blit(g.fonts["bold_sm"].render(lbl, True, INK), (r.x + 14, r.y + 12))
            g.menu_rects.append((r, cb))

    def handle(self, g, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for r, cb in getattr(g, "menu_rects", []):
                if r.collidepoint(ev.pos):
                    cb(); return
