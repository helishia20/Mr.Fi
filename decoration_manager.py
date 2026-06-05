"""
 decoration_manager.py"""
import math
import time
import pygame
from assets import scale_to_fit


DECO_ANIM = {
    "deco_fluffy_flower": "float",   # floating
    "deco_rabbit_flower": "swing",   # left and right pendulum
}

#decoration size in main scene
DECO_SIZE = 100


def _anim_offset(deco_id: str, placed_idx: int) -> tuple[int, int]:
    """
    محاسبه offset انیمیشن بر اساس نوع و زمان.
    هر دکوراسیون phase متفاوت داره تا همه یکسان نباشن.
    """
    t     = time.time()
    phase = placed_idx * 1.3   # phase seperatly for each item

    anim = DECO_ANIM.get(deco_id, "float")

    if anim == "float":
        # floating
        oy = int(math.sin(t * 1.2 + phase) * 6)
        ox = int(math.sin(t * 0.7 + phase) * 2)
    elif anim == "swing":
        # swinging
        ox = int(math.sin(t * 1.5 + phase) * 8)
        oy = int(abs(math.sin(t * 1.5 + phase)) * 2)
    elif anim == "spin":
        ox = int(math.cos(t * 2 + phase) * 5)
        oy = int(math.sin(t * 2 + phase) * 5)
    else:
        ox, oy = 0, 0

    return ox, oy


class DecorationManager:
    """
    مدیریت دکوراسیون‌های روی صفحه:
      placed_decorations: list of {"id": str, "x": int, "y": int}
    """

    def __init__(self):
        self.dragging_idx  = None   # index of item that is draging
        self.drag_offset   = (0, 0) # distance of mouse in middle of it
        self.hover_idx     = None   # the item that the mouse is on it

    def draw(self, surf: pygame.Surface, state: dict, deco_imgs: dict):
        """
    drawing all of animations with reg
        """
        placed = state.get("placed_decorations", [])
        for i, deco in enumerate(placed):
            img = deco_imgs.get(deco["id"])
            if not img:
                continue

            sc  = scale_to_fit(img, DECO_SIZE, DECO_SIZE)
            ox, oy = _anim_offset(deco["id"], i)

            # if its dragging do not offset
            if i == self.dragging_idx:
                mx, my = pygame.mouse.get_pos()
                dx, dy = self.drag_offset
                blit_x = mx - dx
                blit_y = my - dy
            else:
                blit_x = deco["x"] - sc.get_width()  // 2 + ox
                blit_y = deco["y"] - sc.get_height() // 2 + oy

            surf.blit(sc, (blit_x, blit_y))

            # hover highlight
            if i == self.hover_idx and i != self.dragging_idx:
                cx = blit_x + sc.get_width()  // 2
                cy = blit_y + sc.get_height() // 2
                r  = max(sc.get_width(), sc.get_height()) // 2 + 6
                glow = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 255, 100, 60), (r+2, r+2), r+2)
                pygame.draw.circle(glow, (255, 220, 50, 120), (r+2, r+2), r, 2)
                surf.blit(glow, (cx - r - 2, cy - r - 2))

                #guide for delete
                hint = pygame.font.SysFont("Arial", 12).render(
                    "Right-click to remove", True, (255, 80, 80))
                surf.blit(hint, (cx - hint.get_width()//2,
                                 blit_y - 18))

    def handle(self, ev: pygame.event.Event, state: dict,
               deco_imgs: dict) -> bool:
        """
        delete drag and delete mang.
       if the event was used returns true
        """
        placed = state.setdefault("placed_decorations", [])

        if ev.type == pygame.MOUSEMOTION:
            mx, my = ev.pos
            self.hover_idx = None
            for i, deco in enumerate(placed):
                img = deco_imgs.get(deco["id"])
                if not img:
                    continue
                sc  = scale_to_fit(img, DECO_SIZE, DECO_SIZE)
                rx  = deco["x"] - sc.get_width()  // 2
                ry  = deco["y"] - sc.get_height() // 2
                if pygame.Rect(rx, ry, sc.get_width(), sc.get_height()).collidepoint(mx, my):
                    self.hover_idx = i
                    break

            # updata drag
            if self.dragging_idx is not None:
                dx, dy = self.drag_offset
                placed[self.dragging_idx]["x"] = mx - dx + DECO_SIZE // 2
                placed[self.dragging_idx]["y"] = my - dy + DECO_SIZE // 2
            return False

        if ev.type == pygame.MOUSEBUTTONDOWN:
            mx, my = ev.pos

            if ev.button == 1:
                # is there any clicks on item?
                for i, deco in enumerate(placed):
                    img = deco_imgs.get(deco["id"])
                    if not img:
                        continue
                    sc  = scale_to_fit(img, DECO_SIZE, DECO_SIZE)
                    rx  = deco["x"] - sc.get_width()  // 2
                    ry  = deco["y"] - sc.get_height() // 2
                    if pygame.Rect(rx, ry, sc.get_width(), sc.get_height()).collidepoint(mx, my):
                        self.dragging_idx = i
                        self.drag_offset  = (mx - rx, my - ry)
                        return True

            elif ev.button == 3:
                # delte -right click
                for i, deco in enumerate(placed):
                    img = deco_imgs.get(deco["id"])
                    if not img:
                        continue
                    sc  = scale_to_fit(img, DECO_SIZE, DECO_SIZE)
                    rx  = deco["x"] - sc.get_width()  // 2
                    ry  = deco["y"] - sc.get_height() // 2
                    if pygame.Rect(rx, ry, sc.get_width(), sc.get_height()).collidepoint(mx, my):
                        placed.pop(i)
                        self.hover_idx    = None
                        self.dragging_idx = None
                        return True

        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self.dragging_idx is not None:
                self.dragging_idx = None
                return True

        return False
