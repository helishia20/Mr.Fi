"""
Mr Fi — v10
game.py

"""

import math, sys, time, random, threading
import pygame

from config  import (WIN_W, WIN_H, FPS, PANEL, INK, ACCENT, ACCENT2,
                     FOOD_CATALOGUE, BACKGROUND_CATALOGUE, DARK_BACKGROUNDS)
from assets  import Assets, scale_to_height
from save    import load_save, write_save
from audio   import play_click, play_coin, play_happy, play_sad, play_level_up, play_pat
from widgets import Button, draw_toast, draw_hud, draw_coin_row, is_dark_bg, ink_col
from scenes  import (FoodScene, ShopScene, Mode1Scene, Mode2Scene,
                     Mode3Scene, BedroomScene, WeatherScene, MenuScene)
from decoration_manager import DecorationManager


# ══════════════════════════════════════════════════════════════════════════════
#Api
# ══════════════════════════════════════════════════════════════════════════════
DEEPSEEK_KEY = ""
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "You are Mr Fi, an adorable smart frog in a pet game. "
    "Answer accurately in 1-2 sentences. Be friendly, add 1 emoji. "
    "Answer in the same language the user uses."
)


def deepseek_reply(message: str, history: list) -> str:

    import urllib.request, json

    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for who, txt in history[-6:]:
        if txt and txt != "...":
            msgs.append({"role": "assistant" if who == "mrfi" else "user",
                         "content": txt})
    msgs.append({"role": "user", "content": message})

    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": msgs,
        "max_tokens": 120,
        "temperature": 0.7,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            DEEPSEEK_URL, data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {DEEPSEEK_KEY}"},
            method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()

    except Exception as e:
        err = str(e).lower()
        #
        if "401" in err or "403" in err:
            return "API key error — check DEEPSEEK_KEY in game.py 🔑"
        #
        from offline_ai import OfflineAI
        reply = OfflineAI().get_response(message)
        return reply + "  *(offline)*"


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except:
            pass

        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Mr Fi ")
        self.clock  = pygame.time.Clock()

        best = "Arial"
        for fn in ["Tahoma", "Segoe UI", "Arial", "DejaVu Sans"]:
            try:
                pygame.font.SysFont(fn, 18)
                best = fn; break
            except:
                pass

        self.fonts = {
            "normal":  pygame.font.SysFont(best, 19),
            "bold_sm": pygame.font.SysFont(best, 22, bold=True),
            "small":   pygame.font.SysFont(best, 15),
            "xlarge":  pygame.font.SysFont(best, 30, bold=True),
            "bold":    pygame.font.SysFont(best, 22, bold=True),
            "title":   pygame.font.SysFont(best, 34, bold=True),
        }

        self.assets = Assets()
        self.deco_mgr = DecorationManager()

        from animated_bg import AnimatedBackground
        self.bg = AnimatedBackground()

        self.state = load_save()
        self.session_start = time.time()
        self._handle_returning_player()

        self.scene = "main"
        self.mood = "idle"
        self.mood_until = 0
        self.drag_food = None
        self.drag_deco = None   # drag از shop repository
        self.sleep_end = 0

        from offline_ai import OfflineAI
        self.ai = OfflineAI()

        self.m1_input = ""
        self.m1_log  = [("mrfi", "Hi! Ask me anything ")]
        self.m1_thinking = False

        from bert_puzzle import BertPuzzleEngine
        self.bert = BertPuzzleEngine()

        self.m3_kind = None; self.m3_payload = None
        self.m3_input = ""; self.m3_dialogue = ""; self.m3_show_dialogue = False

        self.toast = ""; self.toast_until = 0
        self.last_autosave = time.time()

        self._scenes = {
            "food":    FoodScene(),
            "shop":    ShopScene(),
            "mode1":   Mode1Scene(),
            "mode2":   Mode2Scene(),
            "mode3":   Mode3Scene(),
            "bedroom": BedroomScene(),
            "weather": WeatherScene(),
            "menu":    MenuScene(),
        }
        self._build_main_buttons()

    # ── helpers ───────────────────────────────────────────────────────────────

    def set_mood(self, key, hold=2.0):
        if key in self.assets.sprites:
            self.mood = key; self.mood_until = time.time() + hold

    def show_toast(self, msg, sec=2.5):
        self.toast = msg; self.toast_until = time.time() + sec

    def autosave(self):
        self.state["last_played"] = time.time()
        write_save(self.state)

    def add_xp(self, n):
        self.state["xp"] += n
        new_lvl = 1 + self.state["xp"] // 50
        if new_lvl > self.state["level"]:
            self.state["level"] = new_lvl
            self.show_toast(f"Level up! Lv {new_lvl} 🎉")
            self.set_mood("happy", 2.5)
            play_level_up()

    def add_coin(self, n):
        cap  = self.state["wallet_cap"]
        room = cap - self.state["coins"]
        gained = max(0, min(n, room))
        self.state["coins"] += gained
        self.state["piggy"] += (n - gained)
        self.state["coins_lifetime"] += n

    def _handle_returning_player(self):
        last  = self.state.get("last_played", time.time())
        away  = max(0, time.time() - last)
        cap   = self.state["wallet_cap"]
        gained = max(0, min(min(24, int(away // 3600)), cap - self.state["coins"]))
        self.state["coins"]          += gained
        self.state["coins_lifetime"] += gained
        dec = min(40, int(away // 600))
        self.state["hunger"] = max(0, self.state["hunger"] - dec)
        self.state["happiness"] = max(0, self.state["happiness"] - dec)
        self.state["energy"] = max(0, self.state["energy"] - dec // 2)
        if away > 3600:
            self.set_mood("crying", 6)

    def go(self, scene):
        play_click()
        self.scene = scene
        if scene == "bedroom" and self.sleep_end == 0:
            self.sleep_end = time.time() + 15 * 60
            self.set_mood("sleeping", 9999)

    def _active_bg(self):
        aid = self.state.get("active_background", "bg_main")
        for bg_id, _n, _p, img_file, is_gif in BACKGROUND_CATALOGUE:
            if bg_id == aid:
                return bg_id, img_file, is_gif
        return "bg_main", "bg_main.jpg", False

    # ── buttons ───────────────────────────────────────────────────────────────

    def _build_main_buttons(self):
        bx, by = WIN_W - 188, 92
        bw, bh, gap = 178, 40, 6
        defs = [
            ("Talk  (AI)", lambda: self.go("mode1")),
            ("BERT Puzzle", lambda: self.go("mode2")),
            ("Brain Games", lambda: self.go("mode3")),
            ("Food ", lambda: self.go("food")),
            ("Shop ", lambda: self.go("shop")),
            ("Bed ", lambda: self.go("bedroom")),
            ("Pat ", lambda: self.pat()),
            ("Weather ", lambda: self.go("weather")),
            ("Menu ", lambda: self.go("menu")),
        ]
        self.main_buttons = [
            Button((bx, by + i*(bh+gap), bw, bh), lbl, cb)
            for i, (lbl, cb) in enumerate(defs)
        ]

    def pat(self):
        play_pat()
        if self.state["happiness"] < 100:
            self.state["happiness"] = min(100, self.state["happiness"] + 5)
            self.add_coin(1)
        self.set_mood("enjoyed", 2)
        play_happy()
        if hasattr(self, "frog_rect"):
            cx, cy = self.frog_rect.center
            self.bg.add_sparkle(cx, cy - 40, 12)

    def shop_buy_food(self, key, price):
        if self.state["coins"] >= price:
            self.state["coins"] -= price
            self.state["inventory"][key] = self.state["inventory"].get(key, 0) + 1
            name = next((n for k, n, *_ in FOOD_CATALOGUE if k == key), key)
            self.show_toast(f"Bought {name}! 🛍")
            play_coin()
        else:
            self.show_toast("Not enough coins 💸")
            play_sad()

    def menu_save(self):
        self.state["last_played"] = time.time()
        self.show_toast("Saved ✅" if write_save(self.state) else "Save failed ❌")

    def menu_load(self):
        self.state = load_save()
        self.show_toast("Loaded ✅")

    def menu_quit(self):
        self.menu_save(); pygame.quit(); sys.exit(0)

    # ── sprite ────────────────────────────────────────────────────────────────

    def _frog_at(self, cx, cy, h=220):
        spr = self.assets.sprites.get(self.mood, self.assets.sprites["idle"])
        ow, oh = spr.get_size()
        nw  = max(1, int(ow * h / oh))
        img = pygame.transform.smoothscale(spr, (nw, h))
        off = int(math.sin(time.time() * 3) * 5)
        r   = img.get_rect(center=(cx, cy + off))
        self.screen.blit(img, r)
        return r

    # ── HUD ───────────────────────────────────────────────────────────────────

    def _draw_hud(self):
        dark = is_dark_bg(self.state)
        draw_coin_row(self.screen, self.fonts, self.state,
                      self.assets.icons.get("coin"), 178, 9, dark)
        draw_hud(self.screen, self.fonts, self.state,
                 self.assets.icons, WIN_W - 325, 9, dark)

    # ── main scene ────────────────────────────────────────────────────────────

    def _draw_main(self):
        dark = is_dark_bg(self.state)
        pr   = pygame.Rect(28, 86, WIN_W - 220, WIN_H - 130)

        from scenes import _panel
        _panel(self.screen, pr, dark)

        # DECORATION WITH ANIMIMATION
        self.deco_mgr.draw(self.screen, self.state, self.assets.deco_imgs)

        cx = pr.x + pr.w // 2
        cy = pr.y + pr.h // 2 + 10
        self.frog_rect = self._frog_at(cx, cy, 230)

        for b in self.main_buttons:
            b.dark = dark
            b.draw(self.screen, self.fonts["normal"], dark)

        if time.time() > self.mood_until and self.mood != "sleeping":
            self.mood = "idle"

        # decoration guide if you put item somewhere
        if self.state.get("placed_decorations"):
            hint = self.fonts["small"].render(
                "Right-click decoration to remove", True,
                (255,255,255,160) if dark else (80,80,80))
            self.screen.blit(hint, (pr.x + 8, pr.bottom - 20))

    # ── Mode 1 ───────────────────────────────────────────────────────────────

    def m1_send(self):
        msg = self.m1_input.strip()
        if not msg or self.m1_thinking:
            return
        self.m1_log.append(("u", msg))
        self.m1_input    = ""
        self.m1_thinking = True
        self.m1_log.append(("mrfi", "..."))
        history = list(self.m1_log[:-1])

        def _call():
            reply = deepseek_reply(msg, history)
            if self.m1_log and self.m1_log[-1] == ("mrfi", "..."):
                self.m1_log[-1] = ("mrfi", reply)
            else:
                self.m1_log.append(("mrfi", reply))
            self.m1_thinking = False
            self.set_mood("happy", 2)
            play_happy()

        threading.Thread(target=_call, daemon=True).start()

    # ── Mode 2 BERT ──────────────────────────────────────────────────────────

    def m2_bert_check(self):
        if not self.bert.user_input.strip():
            return
        ok = self.bert.check_bert()
        if ok:
            self.add_xp(10); self.add_coin(2)
            self.set_mood("happy", 2); play_happy()
            def _next():
                time.sleep(1.5); self.bert.new_bert_puzzle()
            threading.Thread(target=_next, daemon=True).start()
        else:
            self.set_mood("sad", 1.5); play_sad()

    # ── Mode 3 ───────────────────────────────────────────────────────────────

    def m3_new(self, kind="math"):
        self.m3_kind = kind; self.m3_input = ""
        self.m3_show_dialogue = False; self.m3_dialogue = ""
        if kind == "math":
            start = random.randint(1, 9); step = random.randint(2, 5)
            seq   = [start + step * i for i in range(4)]
            self.m3_payload = {"seq": seq, "answer": seq[-1] + step}
        elif kind == "word":
            w = random.choice(["frog","apple","star","heart","planet"])
            self.m3_payload = {"scrambled": "".join(random.sample(w, len(w))),
                               "answer": w}
        elif kind == "sudoku":
            base = [[1,2,3,4],[3,4,1,2],[2,1,4,3],[4,3,2,1]]
            puzz = [r[:] for r in base]
            for i in random.sample(range(16), 6): puzz[i//4][i%4] = 0
            self.m3_payload = {"puzzle": puzz, "solution": base, "selected": (0,0)}

    def m3_check(self):
        ok = False
        if self.m3_kind == "math":
            try: ok = int(self.m3_input) == self.m3_payload["answer"]
            except: pass
        elif self.m3_kind == "word":
            ok = self.m3_input.strip().lower() == self.m3_payload["answer"]
        elif self.m3_kind == "sudoku":
            ok = self.m3_payload["puzzle"] == self.m3_payload["solution"]
        if ok:
            self.m3_dialogue = "Yay! 💚"; self.m3_show_dialogue = True
            self.set_mood("happy",2); self.add_xp(15); self.add_coin(2)
            self.state["skip_streak"] = 0; play_happy()
            self.m3_new(self.m3_kind)
            self.m3_show_dialogue = True; self.m3_dialogue = "Yay! 💚"
        else:
            self.m3_dialogue = "Try again!"; self.m3_show_dialogue = True
            self.set_mood("sad", 1.5); play_sad()

    def m3_skip(self):
        self.state["skip_streak"] += 1
        self.m3_dialogue = "Stressed 😣" if self.state["skip_streak"] >= 2 else "OK!"
        self.m3_show_dialogue = True
        self.set_mood("stressed" if self.state["skip_streak"] >= 2 else "sad", 2)
        play_sad(); self.m3_new(self.m3_kind); self.m3_show_dialogue = True

    # ── draw ─────────────────────────────────────────────────────────────────

    def draw(self):
        self.bg.update()
        bg_id, img_file, is_gif = self._active_bg()

        if self.scene == "bedroom":
            self.bg.draw_bedroom_bg(self.screen)
        elif self.scene == "food":
            self.bg.draw_food_bg(self.screen, bg_id, img_file)
        elif self.scene == "shop":
            self.bg.draw_shop_bg(self.screen, bg_id, img_file)
        else:
            self.bg.draw_bg(self.screen, bg_id, img_file, is_gif)

        dark = is_dark_bg(self.state)
        tc   = (210,255,210) if dark else (25,25,45)
        self.screen.blit(self.fonts["title"].render("Mr Fi 🐸", True, tc), (10, 10))

        self._draw_hud()

        if self.scene == "main":
            self._draw_main()
        elif self.scene in self._scenes:
            self._scenes[self.scene].draw(self)

        if self.scene != "main":
            self.back_btn.dark = dark
            self.back_btn.draw(self.screen, self.fonts["normal"], dark)

        if time.time() < self.toast_until and self.toast:
            draw_toast(self.screen, self.fonts["bold_sm"], self.toast, WIN_W, WIN_H)

        pygame.display.flip()

    # ── events ────────────────────────────────────────────────────────────────

    def handle(self, ev):
        if ev.type == pygame.QUIT:
            self.menu_save(); pygame.quit(); sys.exit(0)

        # DRAG/DELETE IN MAIN SCENE FOR DECORATION ITEMS
        if self.scene == "main":
            consumed = self.deco_mgr.handle(ev, self.state, self.assets.deco_imgs)
            if consumed:
                return

        if self.scene != "main":
            self.back_btn.handle(ev)

        if self.scene == "main":
            for b in self.main_buttons:
                b.handle(ev)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if hasattr(self,"frog_rect") and self.frog_rect.collidepoint(ev.pos):
                    self.pat()
        elif self.scene in self._scenes:
            self._scenes[self.scene].handle(self, ev)

    # ── run ───────────────────────────────────────────────────────────────────

    def run(self):
        self.m3_new("math")
        self.back_btn = Button(
            (12, WIN_H-46, 108, 34), "← Back", lambda: self.go("main"))
        while True:
            for ev in pygame.event.get():
                self.handle(ev)
            if time.time() - self.last_autosave > 30:
                self.last_autosave = time.time(); self.autosave()
            self.draw()
            self.clock.tick(FPS)
