"config.py"
import os, time

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
ASSETS    = os.path.join(BASE_DIR, "assets")
IMG_DIR   = os.path.join(ASSETS, "images")
SND_DIR   = os.path.join(ASSETS, "sounds")
SAVE_FILE = os.path.join(BASE_DIR, "save.json")

WIN_W, WIN_H = 1100, 680
FPS = 60

BG           = (245, 240, 225)
PANEL        = (255, 252, 240)
PANEL_DARK   = (30,  30,  45)
INK          = (40,  40,  55)
INK_LIGHT    = (240, 240, 255)
MUTED        = (110, 110, 130)
MUTED_LIGHT  = (190, 190, 210)
ACCENT       = (90,  170, 110)
ACCENT2      = (240, 170, 90)
DANGER       = (220, 90,  90)
SKY          = (180, 220, 240)
WHITE        = (255, 255, 255)
YELLOW_LIGHT = (255, 255, 220)

HUD_ICON_H = 32
FOOD_IMG_H = 90

DARK_BACKGROUNDS = {"bg_bedroom", "bg_dark_forest", "bg_pond"}

FOOD_CATALOGUE = [
    ("egg_sandwich", "Egg Sandwich",  6,  14, "food_egg_sandwich.jpg"),
    ("bubble_tea",   "Bubble Tea",    4,   8, "food_bubble_tea.jpg"),
    ("grapefruit",   "Grapefruit",    3,  10, "food_grapefruit.jpg"),
    ("cake",         "Berry Cake",   12,  22, "food_cake.jpg"),
]

BACKGROUND_CATALOGUE = [
    ("bg_main",        "Sunny Forest",    0,  "bg_main.jpg",        False),
    ("bg_sunset",      "Sunset Meadow", 150,  "bg_sunset.jpg",      False),
    ("bg_dark_forest", "Dark Forest",   170,  "bg_dark_forest.jpg", False),
    ("bg_bedroom",     "Night Garden",    0,  "bg_bedroom.jpg",     False),
    ("bg_pond",        "Koi Pond",      200,  "bg_pond.gif",        True),
]

DECORATION_CATALOGUE = [
    ("deco_fluffy_flower", "Fluffy Flower",  50, "deco_fluffy_flower.png"),
    ("deco_rabbit_flower", "Rabbit Flower", 100, "deco_rabbit_flower.png"),
]

DEFAULT_STATE = {
    "hunger": 60, "happiness": 60, "energy": 60,
    "coins": 220, "coins_lifetime": 220,
    "xp": 0, "level": 1,
    "inventory": {"egg_sandwich": 1, "grapefruit": 1},
    "skip_streak": 0, "away_seconds": 0,
    "last_played": time.time(),
    "wallet_cap": 500, "piggy": 0,
    "owned_backgrounds":  ["bg_main", "bg_bedroom"],
    "active_background":  "bg_main",
    "owned_decorations":  [],
    "placed_decorations": [],
}
