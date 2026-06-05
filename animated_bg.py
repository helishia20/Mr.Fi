
import math, time, random, os
import pygame
from config import WIN_W, WIN_H, IMG_DIR


class Particle:
    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.color       = color
        self.size        = size
        self.lifetime    = lifetime
        self.age         = 0

    def update(self, dt):
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.age += dt
        return self.age < self.lifetime

    def draw(self, surf):
        alpha = int(255 * max(0, 1 - self.age / self.lifetime))
        s = pygame.Surface((self.size * 2 + 2, self.size * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, self.color + (alpha,),
                           (self.size + 1, self.size + 1), self.size)
        surf.blit(s, (int(self.x - self.size), int(self.y - self.size)))


class Firefly:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(0, WIN_W)
        self.y = random.uniform(WIN_H * 0.3, WIN_H * 0.9)
        self.vx = random.uniform(-20, 20)
        self.vy = random.uniform(-15, 15)
        self.phase = random.uniform(0, math.pi * 2)
        self.size  = random.randint(2, 4)

    def update(self, dt):
        self.x += self.vx * dt + math.sin(time.time() + self.phase) * 0.5
        self.y += self.vy * dt + math.cos(time.time() * 0.7 + self.phase) * 0.3
        if self.x < 0 or self.x > WIN_W or self.y < 0 or self.y > WIN_H:
            self.reset()

    def draw(self, surf):
        blink = (math.sin(time.time() * 3 + self.phase) + 1) / 2
        alpha = int(180 * blink + 40)
        s = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (200, 255, 150, alpha),
                           (self.size * 2, self.size * 2), self.size * 2)
        pygame.draw.circle(s, (255, 255, 200, min(255, alpha + 60)),
                           (self.size * 2, self.size * 2), self.size)
        surf.blit(s, (int(self.x) - self.size * 2, int(self.y) - self.size * 2))


class AnimatedBackground:
    def __init__(self):
        self.t = 0
        self.last = time.time()
        self.particles  = []
        self.fireflies  = [Firefly() for _ in range(18)]

        # stars for night bg
        self.stars = [
            {"x": random.randint(0, WIN_W),
             "y": random.randint(0, int(WIN_H * 0.55)),
             "r": random.randint(1, 3),
             "phase": random.uniform(0, math.pi * 2)}
            for _ in range(60)
        ]

        # Loaded images cache: bg_id -> Surface
        self._img_cache: dict[str, pygame.Surface] = {}

        # GIF frames cache: bg_id -> list[Surface]
        self._gif_frames: dict[str, list] = {}
        self._gif_idx:    dict[str, int]  = {}
        self._gif_timer:  dict[str, float]= {}

        # Clouds for overlay
        self.clouds = [{"x": random.randint(-200, WIN_W),
                        "y": random.randint(40, 180),
                        "spd": random.uniform(6, 14),
                        "sc":  random.uniform(0.7, 1.4),
                        "a":   random.randint(35, 70)}
                       for _ in range(4)]

    # ── Asset loading ──────────────────────────────────────────────────────────

    def _load_bg(self, img_file: str) -> pygame.Surface:
        if img_file in self._img_cache:
            return self._img_cache[img_file]
        path = os.path.join(IMG_DIR, img_file)
        if not os.path.exists(path):
            s = pygame.Surface((WIN_W, WIN_H)); s.fill((40, 40, 60))
            return s
        img = pygame.image.load(path).convert()
        img = pygame.transform.scale(img, (WIN_W, WIN_H))
        self._img_cache[img_file] = img
        return img

    def _load_gif(self, img_file: str) -> list:
        """Load a GIF as a list of frames (or single frame for static img)."""
        key = img_file
        if key in self._gif_frames:
            return self._gif_frames[key]
        path = os.path.join(IMG_DIR, img_file)
        frames = []
        try:
            if img_file.lower().endswith(".gif"):
                # pygame doesn't support animated GIFs natively; load as static
                img = pygame.image.load(path).convert()
                img = pygame.transform.scale(img, (WIN_W, WIN_H))
                frames = [img]
            else:
                img = pygame.image.load(path).convert()
                img = pygame.transform.scale(img, (WIN_W, WIN_H))
                frames = [img]
        except Exception:
            s = pygame.Surface((WIN_W, WIN_H)); s.fill((20, 30, 50))
            frames = [s]
        self._gif_frames[key]  = frames
        self._gif_idx[key]     = 0
        self._gif_timer[key]   = 0.0
        return frames

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self):
        now = time.time()
        dt  = min(now - self.last, 0.05)
        self.last = now
        self.t   += dt

        for c in self.clouds:
            c["x"] += c["spd"] * dt
            if c["x"] > WIN_W + 250:
                c["x"] = -250
                c["y"] = random.randint(40, 180)

        for ff in self.fireflies:
            ff.update(dt)

        self.particles = [p for p in self.particles if p.update(dt)]

    # ── Sparkle helper ─────────────────────────────────────────────────────────

    def add_sparkle(self, x, y, count=8):
        import math, random
        for _ in range(count):
            a = random.uniform(0, 2 * math.pi)
            s = random.uniform(40, 100)
            self.particles.append(Particle(
                x, y, math.cos(a) * s, math.sin(a) * s,
                (255, 240, 100), random.randint(2, 5),
                random.uniform(0.5, 1.3)))

    # ── Overlay layers ─────────────────────────────────────────────────────────

    def _draw_clouds(self, surf):
        for c in self.clouds:
            cs = pygame.Surface((int(220 * c["sc"]), int(70 * c["sc"])), pygame.SRCALPHA)
            for cx, cy, r in [(55, 35, 32), (110, 28, 38), (155, 34, 30)]:
                pygame.draw.circle(cs, (255, 255, 255, c["a"]),
                                   (int(cx * c["sc"]), int(cy * c["sc"])), int(r * c["sc"]))
            surf.blit(cs, (int(c["x"]), int(c["y"])))

    def _draw_stars(self, surf):
        for s in self.stars:
            blink = (math.sin(self.t * 1.5 + s["phase"]) + 1) / 2
            alpha = int(100 + 155 * blink)
            ss = pygame.Surface((s["r"] * 4, s["r"] * 4), pygame.SRCALPHA)
            pygame.draw.circle(ss, (255, 255, 220, alpha),
                               (s["r"] * 2, s["r"] * 2), s["r"] * 2)
            surf.blit(ss, (s["x"] - s["r"] * 2, s["y"] - s["r"] * 2))

    def _draw_light_rays(self, surf):
        """Sun rays for day scenes."""
        ray_surf = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        sun_x, sun_y = WIN_W - 100, -40
        for i in range(6):
            angle  = math.pi * 0.35 + i * 0.12
            length = 700 + math.sin(self.t * 0.4 + i) * 60
            ex = int(sun_x + math.cos(angle) * length)
            ey = int(sun_y + math.sin(angle) * length)
            alpha = int(12 + 6 * math.sin(self.t * 0.5 + i))
            pygame.draw.polygon(ray_surf, (255, 255, 180, alpha),
                                [(sun_x - 18, sun_y), (sun_x + 18, sun_y),
                                 (ex + 50, ey), (ex - 50, ey)])
        surf.blit(ray_surf, (0, 0))

    def _draw_particles(self, surf):
        for p in self.particles:
            p.draw(surf)

    def draw_particles(self, surf):
        """Public alias for _draw_particles."""
        self._draw_particles(surf)

    # ── Per-scene draw ─────────────────────────────────────────────────────────

    def draw_bg(self, surf, bg_id: str, img_file: str, is_gif: bool):
        """Universal background draw with per-bg overlays."""
        frames = self._load_gif(img_file)
        if is_gif and len(frames) > 1:
            idx = self._gif_idx.get(img_file, 0)
            surf.blit(frames[idx], (0, 0))
            self._gif_timer[img_file] = self._gif_timer.get(img_file, 0) + 0.016
            if self._gif_timer[img_file] > 0.1:
                self._gif_idx[img_file] = (idx + 1) % len(frames)
                self._gif_timer[img_file] = 0
        else:
            surf.blit(frames[0], (0, 0))

        # per-background overlays
        if bg_id in ("bg_main", "bg_sunset"):
            self._draw_light_rays(surf)
            self._draw_clouds(surf)
        elif bg_id in ("bg_bedroom", "bg_dark_forest"):
            self._draw_stars(surf)
            for ff in self.fireflies:
                ff.draw(surf)
        elif bg_id == "bg_pond":
            # ripple overlay
            rip = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            for i in range(3):
                cx = int(WIN_W * (0.25 + i * 0.25))
                cy = int(WIN_H * 0.6 + math.sin(self.t + i) * 10)
                r  = int(30 + math.sin(self.t * 1.2 + i) * 10)
                pygame.draw.ellipse(rip, (255, 255, 255, 18),
                                    (cx - r * 2, cy - r // 2, r * 4, r))
            surf.blit(rip, (0, 0))

        self._draw_particles(surf)

    # ── Convenience wrappers (called by scenes) ────────────────────────────────

    def draw_main_bg(self, surf, bg_id="bg_main", img_file="bg_main.jpg"):
        self.draw_bg(surf, bg_id, img_file, False)

    def draw_bedroom_bg(self, surf):
        self.draw_bg(surf, "bg_bedroom", "bg_bedroom.jpg", False)

    def draw_food_bg(self, surf, bg_id="bg_main", img_file="bg_main.jpg"):
        self.draw_bg(surf, bg_id, img_file, False)
        # warm overlay
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((255, 220, 180, 30))
        surf.blit(ov, (0, 0))

    def draw_shop_bg(self, surf, bg_id="bg_main", img_file="bg_main.jpg"):
        self.draw_bg(surf, bg_id, img_file, False)

    def draw_weather_bg(self, surf):
        self.draw_bg(surf, "bg_main", "bg_main.jpg", False)
