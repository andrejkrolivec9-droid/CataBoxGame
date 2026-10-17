import kivy
from kivy.config import Config
# Target 120 FPS; actual frame rate depends on the device/display.
Config.set("graphics", "maxfps", "120")
kivy.require('2.0.0')

import os
import math
import random
from datetime import date, timedelta
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stencilview import StencilView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse, Line, Triangle
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition


BG_FILE = "bg.jpg"
HAS_BG = os.path.exists(BG_FILE)
Window.clearcolor = (0, 0, 0, 1) if HAS_BG else (0.05, 0.05, 0.1, 1)

try:
  SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.json")
except:
  SAVE_FILE = "scores.json"


def load_data():
  import json
  if os.path.exists(SAVE_FILE):
    try:
      with open(SAVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      return {}
  return {}


def save_data(data):
  import json
  try:
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
      json.dump(data, f)
  except Exception as e:
    print("SAVE ERROR:", e)


# ============================================================
# ДАННЫЕ ПРЕДМЕТОВ
# ============================================================
CAT_COLORS = {
  "gray": ((0.75, 0.75, 0.8), (0.92, 0.92, 0.97), (0.7, 0.7, 0.75)),
  "orange": ((1, 0.65, 0.3), (1, 0.85, 0.6), (1, 0.65, 0.3)),
  "black": ((0.18, 0.18, 0.22), (0.35, 0.35, 0.4), (0.18, 0.18, 0.22)),
  "gold": ((1, 0.85, 0.2), (1, 0.95, 0.6), (1, 0.85, 0.2)),
}
CAT_NAMES = {"gray": "Серый", "orange": "Рыжий", "black": "Чёрный", "gold": "ЗОЛОТОЙ"}
CAT_PRICES = {"gray": 5, "orange": 15, "black": 50, "gold": 200}

RAINBOW_CAT_COLORS = {
  "rainbow_classic": ((1.0, 0.2, 0.3), (1.0, 0.85, 0.2), (0.3, 0.7, 1.0)),
  "rainbow_sunset": ((1.0, 0.4, 0.1), (1.0, 0.2, 0.6), (0.8, 0.2, 0.9)),
  "rainbow_forest": ((0.2, 0.9, 0.3), (0.9, 0.95, 0.2), (0.1, 0.5, 0.9)),
  "rainbow_ice": ((0.4, 0.9, 1.0), (0.7, 0.6, 1.0), (1.0, 0.9, 1.0)),
  "rainbow_lava": ((1.0, 0.1, 0.1), (1.0, 0.6, 0.1), (0.6, 0.05, 0.05)),
  "rainbow_neon": ((1.0, 0.2, 0.9), (0.2, 1.0, 0.9), (0.9, 1.0, 0.2)),
}
RAINBOW_CAT_NAMES = {
  "rainbow_classic": "Радужный", "rainbow_sunset": "Закатный",
  "rainbow_forest": "Лесной", "rainbow_ice": "Ледяной",
  "rainbow_lava": "Лавовый", "rainbow_neon": "Неоновый",
}
RAINBOW_CAT_PRICES = {
  "rainbow_classic": 500, "rainbow_sunset": 750, "rainbow_forest": 900,
  "rainbow_ice": 1200, "rainbow_lava": 1500, "rainbow_neon": 2000,
}

PLANET_COLORS = {
  "mercury": ((0.55, 0.5, 0.45), (0.75, 0.7, 0.65)),
  "venus": ((1, 0.85, 0.5), (1, 0.95, 0.7)),
  "earth": ((0.2, 0.5, 0.9), (0.4, 0.7, 1)),
  "moon": ((0.85, 0.85, 0.85), (0.95, 0.95, 0.95)),
  "mars": ((0.8, 0.3, 0.15), (1, 0.5, 0.3)),
  "jupiter": ((0.85, 0.6, 0.4), (1, 0.8, 0.6)),
  "saturn": ((0.9, 0.8, 0.5), (1, 0.95, 0.7)),
  "uranus": ((0.4, 0.8, 0.85), (0.6, 0.95, 1)),
  "neptune": ((0.2, 0.4, 0.85), (0.4, 0.6, 1)),
  "sun": ((1, 0.6, 0.1), (1, 0.9, 0.4)),
}
PLANET_NAMES = {
  "mercury": "Меркурий", "venus": "Венера", "earth": "Земля", "moon": "Луна",
  "mars": "Марс", "jupiter": "Юпитер", "saturn": "Сатурн",
  "uranus": "Уран", "neptune": "Нептун", "sun": "Солнце",
}
PLANET_PRICES = {
  "mercury": 10, "venus": 15, "earth": 50, "moon": 60, "mars": 80,
  "jupiter": 200, "saturn": 250, "uranus": 500, "neptune": 700, "sun": 2000,
}

KNIFE_COLORS = {
  "karambit_vanilla": ((0.85, 0.85, 0.88), (1.0, 1.0, 1.0), (0.55, 0.55, 0.6)),
  "karambit_crimson": ((0.75, 0.1, 0.15), (1.0, 0.4, 0.4), (0.45, 0.05, 0.1)),
  "karambit_blue": ((0.15, 0.35, 0.85), (0.45, 0.7, 1.0), (0.05, 0.15, 0.55)),
  "karambit_green": ((0.15, 0.7, 0.25), (0.4, 0.95, 0.5), (0.05, 0.4, 0.15)),
  "karambit_gold": ((1.0, 0.8, 0.15), (1.0, 0.95, 0.5), (0.7, 0.5, 0.05)),
  "karambit_purple": ((0.55, 0.15, 0.85), (0.85, 0.5, 1.0), (0.3, 0.05, 0.55)),
  "karambit_cyan": ((0.1, 0.75, 0.8), (0.4, 1.0, 1.0), (0.05, 0.45, 0.5)),
  "karambit_pink": ((1.0, 0.35, 0.7), (1.0, 0.7, 0.9), (0.7, 0.15, 0.45)),
  "karambit_doppler": ((0.5, 0.15, 0.85), (0.9, 0.5, 1.0), (0.25, 0.05, 0.5)),
  "karambit_case_hard": ((1.0, 0.35, 0.55), (1.0, 0.7, 0.85), (0.7, 0.1, 0.3)),
  "karambit_sapphire": ((0.1, 0.4, 1.0), (0.6, 0.85, 1.0), (0.05, 0.2, 0.7)),
  "karambit_ruby": ((0.9, 0.05, 0.2), (1.0, 0.5, 0.6), (0.55, 0.0, 0.1)),
  "karambit_emerald": ((0.05, 0.85, 0.35), (0.5, 1.0, 0.7), (0.02, 0.5, 0.2)),
  "karambit_black_pearl": ((0.1, 0.1, 0.15), (0.4, 0.4, 0.5), (0.03, 0.03, 0.05)),
  "karambit_talisman": ((1.0, 0.85, 0.2), (1.0, 0.95, 0.6), (0.75, 0.55, 0.05)),
}
KNIFE_NAMES = {
  "karambit_vanilla": "Керамбит Обычный", "karambit_crimson": "Керамбит Малиновый",
  "karambit_blue": "Керамбит Синий", "karambit_green": "Керамбит Зелёный",
  "karambit_gold": "Керамбит Золотой", "karambit_purple": "Керамбит Фиолетовый",
  "karambit_cyan": "Керамбит Бирюзовый", "karambit_pink": "Керамбит Розовый",
  "karambit_doppler": "Керамбит Допплер", "karambit_case_hard": "Керамбит Спецназ",
  "karambit_sapphire": "Керамбит Сапфир", "karambit_ruby": "Керамбит Рубин",
  "karambit_emerald": "Керамбит Изумруд",
  "karambit_black_pearl": "Керамбит Чёрная жемчужина",
  "karambit_talisman": "Керамбит Талисман",
}
KNIFE_PRICES = {
  "karambit_vanilla": 150, "karambit_crimson": 300, "karambit_blue": 350,
  "karambit_green": 350, "karambit_gold": 500, "karambit_purple": 450,
  "karambit_cyan": 450, "karambit_pink": 550, "karambit_doppler": 900,
  "karambit_case_hard": 700, "karambit_sapphire": 1100, "karambit_ruby": 1300,
  "karambit_emerald": 1500, "karambit_black_pearl": 1800, "karambit_talisman": 2200,
}

GUN_COLORS = {
  "glock": ((0.15, 0.15, 0.18), (0.4, 0.4, 0.45), (0.05, 0.05, 0.08)),
  "usp": ((0.25, 0.25, 0.28), (0.5, 0.5, 0.55), (0.1, 0.1, 0.12)),
  "p250": ((0.4, 0.4, 0.45), (0.65, 0.65, 0.7), (0.2, 0.2, 0.25)),
  "deagle": ((0.7, 0.65, 0.35), (1.0, 0.95, 0.6), (0.4, 0.35, 0.1)),
  "fiveseven": ((0.5, 0.5, 0.5), (0.8, 0.8, 0.8), (0.25, 0.25, 0.25)),
  "tec9": ((0.3, 0.3, 0.35), (0.6, 0.6, 0.65), (0.1, 0.1, 0.15)),
  "berettas": ((0.35, 0.35, 0.4), (0.65, 0.65, 0.7), (0.15, 0.15, 0.2)),
  "cz75": ((0.2, 0.25, 0.3), (0.5, 0.55, 0.6), (0.08, 0.1, 0.12)),
  "revolver": ((0.4, 0.25, 0.15), (0.8, 0.5, 0.3), (0.2, 0.1, 0.05)),
  "gold_glock": ((0.95, 0.8, 0.2), (1.0, 0.95, 0.5), (0.7, 0.5, 0.05)),
  "hyperbeast": ((0.7, 0.15, 0.2), (0.3, 0.6, 1.0), (0.5, 0.05, 0.1)),
  "asiimov": ((0.95, 0.5, 0.1), (0.5, 0.5, 0.55), (0.7, 0.3, 0.05)),
  "dragon_lore": ((0.2, 0.5, 0.85), (0.9, 0.8, 0.3), (0.1, 0.3, 0.65)),
  "printstream": ((0.9, 0.9, 0.92), (1.0, 1.0, 1.0), (0.5, 0.5, 0.55)),
  "neon_rider": ((1.0, 0.3, 0.8), (0.3, 1.0, 0.9), (0.6, 0.15, 0.5)),
}
GUN_NAMES = {
  "glock": "Glock-18", "usp": "USP-S", "p250": "P250", "deagle": "Desert Eagle",
  "fiveseven": "Five-SeveN", "tec9": "Tec-9", "berettas": "Dual Berettas",
  "cz75": "CZ75-Auto", "revolver": "R8 Revolver", "gold_glock": "Glock Золотой",
  "hyperbeast": "Glock Гиперзверь", "asiimov": "P250 Асиимов",
  "dragon_lore": "Deagle Дракон", "printstream": "USP Принтстрим",
  "neon_rider": "Tec-9 Неон",
}
GUN_PRICES = {
  "glock": 50, "usp": 70, "p250": 80, "deagle": 150, "fiveseven": 90,
  "tec9": 100, "berettas": 120, "cz75": 130, "revolver": 200,
  "gold_glock": 600, "hyperbeast": 800, "asiimov": 1000,
  "dragon_lore": 1500, "printstream": 2000, "neon_rider": 2500,
}

SPIDER_COLORS = {
  "red": ((0.95, 0.2, 0.2), (1.0, 0.5, 0.5), (0.7, 0.05, 0.05)),
  "orange": ((1.0, 0.55, 0.15), (1.0, 0.75, 0.4), (0.75, 0.35, 0.05)),
  "yellow": ((1.0, 0.9, 0.2), (1.0, 0.98, 0.55), (0.75, 0.65, 0.05)),
  "green": ((0.3, 0.85, 0.35), (0.6, 0.98, 0.6), (0.15, 0.55, 0.15)),
  "blue": ((0.25, 0.55, 0.95), (0.55, 0.8, 1.0), (0.1, 0.3, 0.7)),
  "purple": ((0.65, 0.3, 0.9), (0.85, 0.6, 1.0), (0.4, 0.1, 0.6)),
  "pink": ((1.0, 0.45, 0.75), (1.0, 0.7, 0.9), (0.7, 0.2, 0.5)),
  "cyan": ((0.2, 0.9, 0.9), (0.55, 1.0, 1.0), (0.05, 0.6, 0.6)),
  "rainbow": ((1.0, 0.3, 0.5), (1.0, 0.9, 0.4), (0.5, 0.3, 0.9)),
  "shadow": ((0.1, 0.1, 0.15), (0.4, 0.3, 0.5), (0.03, 0.03, 0.05)),
  "toxic": ((0.6, 1.0, 0.2), (0.85, 1.0, 0.5), (0.35, 0.7, 0.05)),
  "galaxy": ((0.3, 0.2, 0.7), (0.7, 0.5, 1.0), (0.15, 0.05, 0.4)),
}
SPIDER_NAMES = {
  "red": "Красный паук", "orange": "Оранжевый паук", "yellow": "Жёлтый паук",
  "green": "Зелёный паук", "blue": "Синий паук", "purple": "Фиолетовый паук",
  "pink": "Розовый паук", "cyan": "Бирюзовый паук", "rainbow": "РАДУЖНЫЙ паук",
  "shadow": "Теневой паук", "toxic": "Токсичный паук", "galaxy": "Галактический паук",
}
SPIDER_PRICES = {
  "red": 20, "orange": 30, "yellow": 40, "green": 50, "blue": 70,
  "purple": 100, "pink": 130, "cyan": 160, "rainbow": 400,
  "shadow": 550, "toxic": 700, "galaxy": 1000,
}

ICE_COLORS = {
  "frost": ((0.7, 0.9, 1.0), (1.0, 1.0, 1.0), (0.4, 0.6, 0.8)),
  "snow": ((0.95, 0.98, 1.0), (1.0, 1.0, 1.0), (0.6, 0.7, 0.9)),
  "glacier": ((0.5, 0.8, 0.95), (0.8, 0.95, 1.0), (0.2, 0.5, 0.7)),
  "crystal_ice": ((0.4, 0.9, 1.0), (0.85, 1.0, 1.0), (0.15, 0.55, 0.75)),
  "frozen": ((0.35, 0.7, 1.0), (0.7, 0.9, 1.0), (0.1, 0.4, 0.7)),
  "blue_ice": ((0.2, 0.5, 0.9), (0.6, 0.8, 1.0), (0.05, 0.25, 0.6)),
  "aurora": ((0.3, 1.0, 0.7), (0.7, 1.0, 0.9), (0.1, 0.6, 0.4)),
  "absolute_zero": ((0.1, 0.2, 0.5), (0.5, 0.7, 0.9), (0.03, 0.08, 0.25)),
  "eternal_ice": ((0.8, 0.95, 1.0), (1.0, 1.0, 1.0), (0.5, 0.7, 0.9)),
  "cosmic_ice": ((0.4, 0.6, 1.0), (0.8, 0.9, 1.0), (0.15, 0.3, 0.7)),
}
ICE_NAMES = {
  "frost": "Мороз", "snow": "Снег", "glacier": "Ледник",
  "crystal_ice": "Ледяной кристалл", "frozen": "Замёрзший",
  "blue_ice": "Синий лёд", "aurora": "Аврора",
  "absolute_zero": "Абсолютный ноль", "eternal_ice": "Вечный лёд",
  "cosmic_ice": "Космический лёд",
}
ICE_PRICES = {
  "frost": 40, "snow": 90, "glacier": 180, "crystal_ice": 300,
  "frozen": 500, "blue_ice": 750, "aurora": 1100,
  "absolute_zero": 1800, "eternal_ice": 2800, "cosmic_ice": 4500,
}

FIRE_COLORS = {
  "spark": ((1.0, 0.9, 0.3), (1.0, 1.0, 0.7), (0.7, 0.5, 0.05)),
  "ember": ((1.0, 0.5, 0.1), (1.0, 0.75, 0.4), (0.6, 0.2, 0.0)),
  "flame": ((1.0, 0.3, 0.05), (1.0, 0.6, 0.3), (0.5, 0.1, 0.0)),
  "blaze": ((1.0, 0.15, 0.1), (1.0, 0.5, 0.4), (0.6, 0.05, 0.05)),
  "inferno": ((0.9, 0.05, 0.05), (1.0, 0.4, 0.3), (0.5, 0.0, 0.0)),
  "hellfire": ((0.7, 0.05, 0.2), (1.0, 0.3, 0.5), (0.4, 0.0, 0.1)),
  "phoenix": ((1.0, 0.6, 0.1), (1.0, 0.85, 0.5), (0.7, 0.3, 0.05)),
  "dragon_fire": ((0.9, 0.2, 0.1), (1.0, 0.6, 0.3), (0.55, 0.05, 0.05)),
  "solar_flare": ((1.0, 0.85, 0.2), (1.0, 0.95, 0.6), (0.75, 0.55, 0.05)),
  "eternal_flame": ((1.0, 0.4, 0.7), (1.0, 0.75, 0.9), (0.6, 0.15, 0.4)),
}
FIRE_NAMES = {
  "spark": "Искра", "ember": "Уголёк", "flame": "Пламя",
  "blaze": "Пожар", "inferno": "Инферно", "hellfire": "Адское пламя",
  "phoenix": "Феникс", "dragon_fire": "Пламя дракона",
  "solar_flare": "Солнечная вспышка", "eternal_flame": "Вечное пламя",
}
FIRE_PRICES = {
  "spark": 40, "ember": 90, "flame": 180, "blaze": 300,
  "inferno": 500, "hellfire": 750, "phoenix": 1100,
  "dragon_fire": 1800, "solar_flare": 2800, "eternal_flame": 4500,
}

COSMIC_COLORS = {
  "asteroid": ((0.5, 0.5, 0.55), (0.8, 0.8, 0.85), (0.25, 0.25, 0.3)),
  "comet": ((0.7, 0.9, 1.0), (1.0, 1.0, 1.0), (0.3, 0.5, 0.7)),
  "meteor": ((0.9, 0.6, 0.3), (1.0, 0.85, 0.5), (0.5, 0.25, 0.05)),
  "nebula": ((0.7, 0.3, 0.9), (1.0, 0.7, 1.0), (0.35, 0.1, 0.6)),
  "supernova": ((1.0, 0.5, 0.9), (1.0, 0.85, 1.0), (0.7, 0.2, 0.6)),
  "wormhole": ((0.4, 0.7, 1.0), (0.8, 0.95, 1.0), (0.1, 0.3, 0.6)),
  "quasar": ((0.3, 0.9, 0.9), (0.7, 1.0, 1.0), (0.05, 0.55, 0.55)),
  "dark_matter": ((0.15, 0.1, 0.3), (0.5, 0.4, 0.7), (0.05, 0.02, 0.12)),
  "big_bang": ((1.0, 0.9, 0.3), (1.0, 1.0, 0.6), (0.75, 0.55, 0.05)),
  "multiverse": ((0.9, 0.2, 0.6), (1.0, 0.6, 0.9), (0.5, 0.1, 0.35)),
}
COSMIC_NAMES = {
  "asteroid": "Астероид", "comet": "Комета", "meteor": "Метеорит",
  "nebula": "Туманность", "supernova": "Сверхновая", "wormhole": "Червоточина",
  "quasar": "Квазар", "dark_matter": "Тёмная материя",
  "big_bang": "Большой взрыв", "multiverse": "Мультивселенная",
}
COSMIC_PRICES = {
  "asteroid": 60, "comet": 120, "meteor": 200, "nebula": 350,
  "supernova": 600, "wormhole": 900, "quasar": 1400,
  "dark_matter": 2200, "big_bang": 3500, "multiverse": 6000,
}

MAGIC_COLORS = {
  "rune": ((0.6, 0.5, 0.4), (0.9, 0.8, 0.7), (0.3, 0.25, 0.2)),
  "scroll": ((0.9, 0.8, 0.6), (1.0, 0.95, 0.8), (0.55, 0.45, 0.3)),
  "potion": ((0.6, 0.2, 0.9), (0.9, 0.6, 1.0), (0.3, 0.05, 0.55)),
  "wand": ((0.5, 0.3, 0.9), (0.8, 0.6, 1.0), (0.2, 0.1, 0.5)),
  "orb": ((0.4, 0.6, 1.0), (0.7, 0.9, 1.0), (0.1, 0.3, 0.6)),
  "tome": ((0.4, 0.2, 0.5), (0.8, 0.5, 0.9), (0.15, 0.05, 0.25)),
  "staff": ((0.7, 0.5, 0.2), (1.0, 0.8, 0.5), (0.4, 0.25, 0.05)),
  "crystal_ball": ((0.5, 0.9, 0.9), (0.85, 1.0, 1.0), (0.15, 0.5, 0.5)),
  "arcane_ring": ((1.0, 0.4, 0.7), (1.0, 0.75, 0.9), (0.6, 0.15, 0.4)),
  "philosopher_stone": ((1.0, 0.3, 0.3), (1.0, 0.7, 0.5), (0.6, 0.05, 0.05)),
}
MAGIC_NAMES = {
  "rune": "Руна", "scroll": "Свиток", "potion": "Зелье",
  "wand": "Жезл", "orb": "Сфера", "tome": "Гримуар",
  "staff": "Посох", "crystal_ball": "Магический шар",
  "arcane_ring": "Магическое кольцо", "philosopher_stone": "Философский камень",
}
MAGIC_PRICES = {
  "rune": 50, "scroll": 100, "potion": 180, "wand": 300,
  "orb": 500, "tome": 800, "staff": 1200,
  "crystal_ball": 2000, "arcane_ring": 3200, "philosopher_stone": 5500,
}


# === НОВЫЕ 5 КЕЙСОВ ===
# Нексус (рыбки)
FISH_COLORS = {
  "guppy": ((1.0, 0.7, 0.3), (1.0, 0.85, 0.5), (0.6, 0.35, 0.05)),
  "goldfish": ((1.0, 0.5, 0.1), (1.0, 0.75, 0.4), (0.7, 0.25, 0.0)),
  "neon_tetra": ((0.3, 0.9, 1.0), (0.6, 1.0, 1.0), (0.1, 0.5, 0.6)),
  "angelfish": ((0.9, 0.9, 0.95), (1.0, 1.0, 1.0), (0.5, 0.5, 0.6)),
  "clownfish": ((1.0, 0.4, 0.1), (1.0, 0.7, 0.4), (0.7, 0.15, 0.05)),
  "betta": ((0.7, 0.2, 0.9), (0.9, 0.5, 1.0), (0.35, 0.05, 0.55)),
  "koi": ((1.0, 0.6, 0.4), (1.0, 0.85, 0.7), (0.6, 0.25, 0.1)),
  "arowana": ((0.9, 0.7, 0.3), (1.0, 0.9, 0.5), (0.55, 0.35, 0.05)),
  "discus": ((0.8, 0.4, 0.3), (1.0, 0.6, 0.5), (0.5, 0.15, 0.1)),
  "arctic_char": ((0.5, 0.9, 1.0), (0.8, 1.0, 1.0), (0.2, 0.5, 0.7)),
}
FISH_NAMES = {
  "guppy": "Гуппи", "goldfish": "Золотая рыбка", "neon_tetra": "Неоновая тетра",
  "angelfish": "Скалярия", "clownfish": "Рыба-клоун", "betta": "Петушок",
  "koi": "Кои", "arowana": "Арована", "discus": "Дискус",
  "arctic_char": "Арктический голец",
}
FISH_PRICES = {
  "guppy": 25, "goldfish": 60, "neon_tetra": 120, "angelfish": 220,
  "clownfish": 400, "betta": 700, "koi": 1200, "arowana": 2000,
  "discus": 3200, "arctic_char": 5500,
}

# Сад (растения)
PLANT_COLORS = {
  "daisy": ((0.95, 0.95, 0.9), (1.0, 0.98, 0.3), (0.5, 0.5, 0.4)),
  "tulip": ((1.0, 0.3, 0.4), (1.0, 0.6, 0.7), (0.5, 0.1, 0.15)),
  "rose": ((0.9, 0.1, 0.3), (1.0, 0.4, 0.6), (0.5, 0.0, 0.1)),
  "sunflower": ((1.0, 0.8, 0.15), (1.0, 0.95, 0.5), (0.5, 0.35, 0.05)),
  "orchid": ((0.8, 0.5, 1.0), (1.0, 0.75, 1.0), (0.4, 0.15, 0.6)),
  "lotus": ((1.0, 0.5, 0.8), (1.0, 0.75, 0.9), (0.55, 0.15, 0.4)),
  "cactus_flower": ((0.95, 0.2, 0.6), (1.0, 0.5, 0.8), (0.5, 0.05, 0.3)),
  "blue_bell": ((0.3, 0.5, 1.0), (0.6, 0.75, 1.0), (0.1, 0.2, 0.6)),
  "crystal_flower": ((0.7, 0.9, 1.0), (1.0, 1.0, 1.0), (0.3, 0.5, 0.7)),
  "eternal_bloom": ((1.0, 0.3, 0.9), (1.0, 0.7, 1.0), (0.6, 0.1, 0.5)),
}
PLANT_NAMES = {
  "daisy": "Ромашка", "tulip": "Тюльпан", "rose": "Роза",
  "sunflower": "Подсолнух", "orchid": "Орхидея", "lotus": "Лотос",
  "cactus_flower": "Кактусовый цветок", "blue_bell": "Синюшка",
  "crystal_flower": "Кристальный цветок", "eternal_bloom": "Вечное цветение",
}
PLANT_PRICES = {
  "daisy": 30, "tulip": 70, "rose": 150, "sunflower": 280,
  "orchid": 500, "lotus": 800, "cactus_flower": 1300,
  "blue_bell": 2000, "crystal_flower": 3200, "eternal_bloom": 6000,
}

# Меха (животные)
FUR_COLORS = {
  "fox": ((1.0, 0.5, 0.15), (1.0, 0.75, 0.4), (0.55, 0.25, 0.05)),
  "wolf": ((0.5, 0.5, 0.55), (0.75, 0.75, 0.8), (0.25, 0.25, 0.3)),
  "bear": ((0.4, 0.25, 0.15), (0.6, 0.4, 0.25), (0.2, 0.1, 0.05)),
  "snow_leopard": ((0.95, 0.95, 1.0), (1.0, 1.0, 1.0), (0.5, 0.5, 0.65)),
  "tiger": ((1.0, 0.6, 0.1), (1.0, 0.8, 0.4), (0.5, 0.25, 0.0)),
  "panther": ((0.15, 0.1, 0.2), (0.4, 0.3, 0.5), (0.05, 0.02, 0.1)),
  "lynx": ((0.9, 0.7, 0.5), (1.0, 0.85, 0.7), (0.5, 0.35, 0.2)),
  "panda": ((0.95, 0.95, 0.95), (1.0, 1.0, 1.0), (0.15, 0.15, 0.15)),
  "polar_bear": ((0.9, 0.95, 1.0), (1.0, 1.0, 1.0), (0.5, 0.6, 0.7)),
  "golden_panther": ((1.0, 0.8, 0.2), (1.0, 0.95, 0.5), (0.6, 0.4, 0.05)),
}
FUR_NAMES = {
  "fox": "Лиса", "wolf": "Волк", "bear": "Медведь",
  "snow_leopard": "Снежный барс", "tiger": "Тигр", "panther": "Пантера",
  "lynx": "Рысь", "panda": "Панда", "polar_bear": "Белый медведь",
  "golden_panther": "Золотая пантера",
}
FUR_PRICES = {
  "fox": 35, "wolf": 80, "bear": 180, "snow_leopard": 320,
  "tiger": 550, "panther": 900, "lynx": 1400,
  "panda": 2200, "polar_bear": 3500, "golden_panther": 6500,
}

# Минералы
MINERAL_COLORS = {
  "iron": ((0.5, 0.5, 0.55), (0.75, 0.75, 0.8), (0.25, 0.25, 0.3)),
  "copper": ((0.85, 0.5, 0.25), (1.0, 0.7, 0.5), (0.5, 0.25, 0.1)),
  "silver": ((0.85, 0.85, 0.9), (1.0, 1.0, 1.0), (0.5, 0.5, 0.6)),
  "gold_mineral": ((1.0, 0.8, 0.2), (1.0, 0.95, 0.5), (0.6, 0.4, 0.05)),
  "platinum": ((0.9, 0.95, 1.0), (1.0, 1.0, 1.0), (0.5, 0.55, 0.7)),
  "titanium": ((0.6, 0.65, 0.7), (0.85, 0.9, 0.95), (0.3, 0.35, 0.4)),
  "mythril": ((0.5, 0.9, 0.9), (0.75, 1.0, 1.0), (0.2, 0.5, 0.55)),
  "orichalcum": ((0.9, 0.4, 0.1), (1.0, 0.65, 0.35), (0.5, 0.15, 0.0)),
  "adamantite": ((0.5, 0.2, 0.9), (0.75, 0.5, 1.0), (0.25, 0.05, 0.55)),
  "meteorite": ((0.3, 0.2, 0.7), (0.6, 0.5, 1.0), (0.1, 0.05, 0.35)),
}
MINERAL_NAMES = {
  "iron": "Железо", "copper": "Медь", "silver": "Серебро",
  "gold_mineral": "Золото", "platinum": "Платина", "titanium": "Титан",
  "mythril": "Мифрил", "orichalcum": "Орихалк", "adamantite": "Адамантит",
  "meteorite": "Метеорит",
}
MINERAL_PRICES = {
  "iron": 20, "copper": 50, "silver": 120, "gold_mineral": 250,
  "platinum": 450, "titanium": 750, "mythril": 1200,
  "orichalcum": 1900, "adamantite": 3000, "meteorite": 5500,
}

# Растения/грибы
MUSHROOM_COLORS = {
  "white": ((0.95, 0.95, 0.95), (1.0, 1.0, 1.0), (0.5, 0.5, 0.5)),
  "brown": ((0.6, 0.4, 0.2), (0.8, 0.6, 0.4), (0.3, 0.15, 0.05)),
  "red": ((0.9, 0.15, 0.15), (1.0, 0.5, 0.5), (0.5, 0.05, 0.05)),
  "blue": ((0.3, 0.4, 0.9), (0.6, 0.7, 1.0), (0.1, 0.15, 0.55)),
  "purple": ((0.6, 0.2, 0.9), (0.85, 0.5, 1.0), (0.3, 0.05, 0.55)),
  "green": ((0.3, 0.85, 0.4), (0.6, 0.95, 0.6), (0.1, 0.5, 0.15)),
  "yellow": ((1.0, 0.85, 0.2), (1.0, 0.95, 0.5), (0.6, 0.4, 0.05)),
  "pink": ((1.0, 0.5, 0.8), (1.0, 0.75, 0.9), (0.55, 0.15, 0.45)),
  "cyan": ((0.2, 0.9, 0.9), (0.6, 1.0, 1.0), (0.05, 0.5, 0.5)),
  "glow": ((0.9, 0.9, 0.3), (1.0, 1.0, 0.7), (0.5, 0.5, 0.05)),
}
MUSHROOM_NAMES = {
  "white": "Белый гриб", "brown": "Боровик", "red": "Красный мухомор",
  "blue": "Синий гриб", "purple": "Фиолетовый гриб", "green": "Зелёный гриб",
  "yellow": "Жёлтый гриб", "pink": "Розовый гриб", "cyan": "Бирюзовый гриб",
  "glow": "Светящийся гриб",
}
MUSHROOM_PRICES = {
  "white": 25, "brown": 55, "red": 100, "blue": 200,
  "purple": 400, "green": 700, "yellow": 1100,
  "pink": 1800, "cyan": 2800, "glow": 5000,
}


CASE_INFO = {
  "cats": {"label": "Кейс с котами", "roulette": "cats", "item_type": "cat"},
  "planets": {"label": "Космический кейс", "roulette": "planets", "item_type": "planet"},
  "knives": {"label": "Кейс с керамбитами", "roulette": "knives", "item_type": "knives"},
  "spiders": {"label": "Кейс с пауками", "roulette": "spiders", "item_type": "spiders"},
  "rainbow": {"label": "Радужный кейс", "roulette": "rainbow", "item_type": "rainbow"},
  "guns": {"label": "Кейс с пистолетами", "roulette": "guns", "item_type": "guns"},
  "ice": {"label": "Ледяной кейс", "roulette": "ice", "item_type": "ice"},
  "fire": {"label": "Огненный кейс", "roulette": "fire", "item_type": "fire"},
  "cosmic": {"label": "Космический мистик", "roulette": "cosmic", "item_type": "cosmic"},
  "magic": {"label": "Магический кейс", "roulette": "magic", "item_type": "magic"},
  "fish": {"label": "Кейс с рыбками", "roulette": "fish", "item_type": "fish"},
  "plants": {"label": "Садовый кейс", "roulette": "plants", "item_type": "plants"},
  "fur": {"label": "Кейс с мехом", "roulette": "fur", "item_type": "fur"},
  "minerals": {"label": "Кейс с минералами", "roulette": "minerals", "item_type": "minerals"},
  "mushrooms": {"label": "Кейс с грибами", "roulette": "mushrooms", "item_type": "mushrooms"},
}


def get_name(item_type, kind):
  maps = {
    "cat": CAT_NAMES, "planet": PLANET_NAMES, "knives": KNIFE_NAMES,
    "spiders": SPIDER_NAMES, "rainbow": RAINBOW_CAT_NAMES, "guns": GUN_NAMES,
    "ice": ICE_NAMES, "fire": FIRE_NAMES, "cosmic": COSMIC_NAMES, "magic": MAGIC_NAMES,
    "fish": FISH_NAMES, "plants": PLANT_NAMES, "fur": FUR_NAMES,
    "minerals": MINERAL_NAMES, "mushrooms": MUSHROOM_NAMES,
  }
  return maps.get(item_type, {}).get(kind, "?")


def get_price(item_type, kind):
  maps = {
    "cat": CAT_PRICES, "planet": PLANET_PRICES, "knives": KNIFE_PRICES,
    "spiders": SPIDER_PRICES, "rainbow": RAINBOW_CAT_PRICES, "guns": GUN_PRICES,
    "ice": ICE_PRICES, "fire": FIRE_PRICES, "cosmic": COSMIC_PRICES, "magic": MAGIC_PRICES,
    "fish": FISH_PRICES, "plants": PLANT_PRICES, "fur": FUR_PRICES,
    "minerals": MINERAL_PRICES, "mushrooms": MUSHROOM_PRICES,
  }
  return maps.get(item_type, {}).get(kind, 0)


def case_prices(case_id):
  return {
    "cats": (100, 500, 1000), "planets": (100, 500, 1000),
    "knives": (200, 1000, 2000), "spiders": (100, 500, 1000),
    "rainbow": (500, 2500, 5000), "guns": (150, 750, 1500),
    "ice": (200, 1000, 2000), "fire": (200, 1000, 2000),
    "cosmic": (300, 1500, 3000), "magic": (350, 1750, 3500),
    "fish": (80, 400, 800), "plants": (80, 400, 800),
    "fur": (120, 600, 1200), "minerals": (100, 500, 1000),
    "mushrooms": (80, 400, 800),
  }.get(case_id, (100, 500, 1000))


def case_prizes(case_id):
  if case_id == "cats": return (["gray", "orange", "black", "gold"], [50, 30, 15, 5])
  if case_id == "planets":
    return (["mercury", "venus", "earth", "moon", "mars", "jupiter",
         "saturn", "uranus", "neptune", "sun"],
        [25, 22, 15, 12, 10, 6, 4, 3, 2, 1])
  if case_id == "knives":
    return (list(KNIFE_NAMES.keys()),
        [22, 18, 15, 12, 10, 8, 6, 4, 3, 2, 1, 0.7, 0.4, 0.2, 0.1])
  if case_id == "spiders":
    return (list(SPIDER_NAMES.keys()),
        [22, 18, 15, 12, 9, 7, 5, 4, 3, 2, 1.5, 0.5])
  if case_id == "rainbow":
    return (list(RAINBOW_CAT_NAMES.keys()), [40, 25, 15, 10, 7, 3])
  if case_id == "guns":
    return (list(GUN_NAMES.keys()),
        [22, 18, 15, 10, 9, 8, 6, 4, 3, 2, 1.5, 0.7, 0.4, 0.2, 0.1])
  if case_id == "ice":
    return (list(ICE_NAMES.keys()), [30, 22, 15, 10, 8, 6, 4, 2.5, 1.5, 0.5])
  if case_id == "fire":
    return (list(FIRE_NAMES.keys()), [30, 22, 15, 10, 8, 6, 4, 2.5, 1.5, 0.5])
  if case_id == "cosmic":
    return (list(COSMIC_NAMES.keys()), [28, 22, 15, 10, 8, 6, 4, 3, 2, 1])
  if case_id == "magic":
    return (list(MAGIC_NAMES.keys()), [28, 22, 15, 10, 8, 6, 4, 3, 2, 1])
  if case_id == "fish":
    return (list(FISH_NAMES.keys()), [30, 22, 15, 10, 8, 6, 4, 2.5, 1.5, 0.5])
  if case_id == "plants":
    return (list(PLANT_NAMES.keys()), [30, 22, 15, 10, 8, 6, 4, 2.5, 1.5, 0.5])
  if case_id == "fur":
    return (list(FUR_NAMES.keys()), [30, 22, 15, 10, 8, 6, 4, 2.5, 1.5, 0.5])
  if case_id == "minerals":
    return (list(MINERAL_NAMES.keys()), [30, 22, 15, 10, 8, 6, 4, 2.5, 1.5, 0.5])
  if case_id == "mushrooms":
    return (list(MUSHROOM_NAMES.keys()), [30, 22, 15, 10, 8, 6, 4, 2.5, 1.5, 0.5])
  return ([], [])


LEGENDARY_KINDS = {
  "gold", "sun", "rainbow_neon", "rainbow_lava",
  "karambit_talisman", "karambit_black_pearl",
  "galaxy", "neon_rider", "printstream",
  "cosmic_ice", "eternal_flame", "multiverse", "philosopher_stone",
  "arctic_char", "eternal_bloom", "golden_panther", "meteorite", "glow",
}


# ============================================================
# РАНГИ (17 штук)
# ============================================================
RANKS = [
  ("bronze_1", "Бронза I", (0.7, 0.45, 0.25), (0.9, 0.7, 0.5)),
  ("bronze_2", "Бронза II", (0.7, 0.45, 0.25), (0.9, 0.7, 0.5)),
  ("bronze_3", "Бронза III", (0.7, 0.45, 0.25), (0.9, 0.7, 0.5)),
  ("silver_1", "Серебро I", (0.75, 0.78, 0.85), (0.95, 0.98, 1.0)),
  ("silver_2", "Серебро II", (0.75, 0.78, 0.85), (0.95, 0.98, 1.0)),
  ("silver_3", "Серебро III", (0.75, 0.78, 0.85), (0.95, 0.98, 1.0)),
  ("gold_1", "Золото I", (1.0, 0.8, 0.15), (1.0, 0.95, 0.5)),
  ("gold_2", "Золото II", (1.0, 0.8, 0.15), (1.0, 0.95, 0.5)),
  ("gold_3", "Золото III", (1.0, 0.8, 0.15), (1.0, 0.95, 0.5)),
  ("platinum", "Платина", (0.85, 0.95, 1.0), (1.0, 1.0, 1.0)),
  ("diamond", "Алмаз", (0.4, 0.9, 1.0), (0.8, 0.98, 1.0)),
  ("master", "Мастер", (0.7, 0.2, 0.9), (1.0, 0.6, 1.0)),
  ("grandmaster", "Грандмастер", (0.9, 0.3, 0.7), (1.0, 0.7, 0.9)),
  ("elite", "Элита", (0.3, 0.9, 0.5), (0.7, 1.0, 0.8)),
  ("champion", "Чемпион", (1.0, 0.5, 0.1), (1.0, 0.8, 0.4)),
  ("legend", "Легенда", (1.0, 0.3, 0.4), (1.0, 0.8, 0.9)),
  ("pro", "PRO", (0.95, 0.82, 0.05), (1.0, 1.0, 0.22)),
]


def rank_threshold(index):
  """MMR threshold for a rank: Bronze starts at 1000, then +500 per rank."""
  return 1000 + max(0, int(index)) * 500


def rank_index_by_mmr(mmr):
  mmr = max(0, int(mmr))
  if mmr < rank_threshold(0):
    return 0
  return min(len(RANKS) - 1, (mmr - 1000) // 500)


# ============================================================
# РАМКИ
# ============================================================
FRAMES = [
  ("none", "Без рамки", 0, None, "circle"),
  ("bronze_frame", "Бронзовая", 200, (0.7, 0.45, 0.25), "circle"),
  ("silver_frame", "Серебряная", 500, (0.75, 0.78, 0.85), "circle"),
  ("gold_frame", "Золотая", 1500, (1.0, 0.8, 0.15), "circle"),
  ("ruby_frame", "Рубиновая", 3000, (0.95, 0.1, 0.25), "star"),
  ("sapphire_frame", "Сапфировая", 3000, (0.1, 0.4, 1.0), "star"),
  ("emerald_frame", "Изумрудная", 3500, (0.1, 0.8, 0.4), "star"),
  ("amethyst_frame", "Аметистовая", 4000, (0.6, 0.3, 0.9), "diamond"),
  ("cyan_frame", "Бирюзовая", 4500, (0.2, 0.9, 0.9), "diamond"),
  ("rose_frame", "Розовая", 5000, (1.0, 0.4, 0.7), "diamond"),
  ("rainbow_frame", "Радужная", 8000, (1.0, 0.3, 0.7), "rainbow"),
  ("cosmic_frame", "Космическая", 12000, (0.6, 0.4, 1.0), "rainbow"),
  ("flame_frame", "Пламенная", 16000, (1.0, 0.4, 0.1), "flame"),
  ("ice_frame", "Ледяная", 16000, (0.5, 0.9, 1.0), "flame"),
  ("legend_frame", "Легендарная", 25000, (1.0, 0.85, 0.2), "legend"),
  ("eternal_frame", "Вечная", 50000, (1.0, 0.5, 0.9), "legend"),
  ("plasma_frame", "Плазменная", 30000, (0.9, 0.6, 1.0), "flame"),
  ("nature_frame", "Природная", 20000, (0.3, 0.9, 0.4), "star"),
  ("ocean_frame", "Океаническая", 22000, (0.3, 0.7, 1.0), "rainbow"),
  ("sun_frame", "Солнечная", 28000, (1.0, 0.7, 0.1), "flame"),
  ("galaxy_frame", "Галактическая", 35000, (0.7, 0.4, 1.0), "rainbow"),
]


# ============================================================
# АВАТАРЫ
# ============================================================
AVATARS = [
  ("cat_orange", "Рыжий кот"),
  ("cat_black", "Чёрный кот"),
  ("cat_gold", "Золотой кот"),
  ("rainbow_classic", "Радужный кот"),
  ("rainbow_neon", "Неоновый кот"),
  ("spider_red", "Красный паук"),
  ("spider_galaxy", "Галактический паук"),
  ("karambit_doppler", "Керамбит Допплер"),
  ("karambit_talisman", "Керамбит Талисман"),
  ("glock", "Glock"),
  ("deagle", "Deagle"),
  ("sun", "Солнце"),
  ("rainbow_lava", "Лавовый кот"),
  ("spider_rainbow", "Радужный паук"),
  ("karambit_black_pearl", "Чёрная жемчужина"),
  ("neon_rider", "Неоновый стрелок"),
  ("guppy", "Гуппи"),
  ("goldfish", "Золотая рыбка"),
  ("betta", "Петушок"),
  ("koi", "Кои"),
  ("fox", "Лиса"),
  ("wolf", "Волк"),
  ("tiger", "Тигр"),
  ("panda", "Панда"),
  ("rose", "Роза"),
  ("sunflower", "Подсолнух"),
  ("lotus", "Лотос"),
  ("gold_mineral", "Золото"),
  ("meteorite", "Метеорит"),
  ("glow", "Светящийся гриб"),
]


def avatar_to_art(av_key, size):
  if av_key.startswith("cat_"):
    return CatArt(av_key.replace("cat_", ""), size)
  if av_key.startswith("rainbow_"):
    return CatArt(av_key, size)
  if av_key.startswith("spider_"):
    return SpiderArt(av_key.replace("spider_", ""), size)
  if av_key.startswith("karambit_"):
    return KnifeArt(av_key, size)
  if av_key in GUN_NAMES:
    return GunArt(av_key, size)
  if av_key in FISH_NAMES:
    return FishArt(av_key, size)
  if av_key in FUR_NAMES:
    return FurArt(av_key, size)
  if av_key in PLANT_NAMES:
    return PlantArt(av_key, size)
  if av_key in MINERAL_NAMES:
    return MineralArt(av_key, size)
  if av_key in MUSHROOM_NAMES:
    return MushroomArt(av_key, size)
  if av_key == "sun":
    return SunArt(size)
  return CatArt("orange", size)


# ============================================================
# ЕЖЕДНЕВНЫЕ ЗАДАНИЯ
# ============================================================
DAILY_QUESTS = [
  {"id": "tap_100", "label": "Сделай 100 тапов", "target": 100, "reward_coins": 500, "reward_mmr": 0, "progress_key": "taps_total"},
  {"id": "open_5", "label": "Открой 5 кейсов", "target": 5, "reward_coins": 800, "reward_mmr": 10, "progress_key": "cases_opened"},
  {"id": "win_casino_3", "label": "Выиграй 3 раза в казино", "target": 3, "reward_coins": 1200, "reward_mmr": 15, "progress_key": "casino_wins"},
  {"id": "hit_5_targets", "label": "Попади в 5 мишеней", "target": 5, "reward_coins": 1000, "reward_mmr": 50, "progress_key": "targets_hit"},
  {"id": "sell_3", "label": "Продай 3 предмета", "target": 3, "reward_coins": 300, "reward_mmr": 5, "progress_key": "items_sold"},
]


# ============================================================
# АНИМИРОВАННЫЕ ОБОИ
# ============================================================
class AnimatedBg(FloatLayout):
  def __init__(self, theme="sun", style="particles_up", **kwargs):
    super().__init__(**kwargs)
    self.theme = theme; self.style = style
    self.time = 0.0
    self.stars = []; self.orbs = []; self.particles = []; self.lines = []
    self._ev = None

    palettes = {
      "sun": ((0.06, 0.04, 0.02, 1), [(1, 0.65, 0.15), (1, 0.85, 0.35), (1, 0.5, 0.05)]),
      "cat": ((0.10, 0.05, 0.03, 1), [(1, 0.55, 0.30), (1, 0.75, 0.50), (0.9, 0.4, 0.2)]),
      "spider": ((0.04, 0.02, 0.10, 1), [(0.55, 0.15, 0.85), (0.35, 0.05, 0.6), (0.75, 0.4, 1.0)]),
      "rainbow": ((0.05, 0.02, 0.08, 1), [(1, 0.2, 0.5), (0.3, 0.9, 1), (1, 0.85, 0.2)]),
      "knife": ((0.08, 0.02, 0.03, 1), [(0.9, 0.2, 0.3), (1, 0.4, 0.5), (0.7, 0.1, 0.15)]),
      "gun": ((0.05, 0.06, 0.08, 1), [(0.55, 0.6, 0.7), (0.4, 0.45, 0.55), (0.75, 0.8, 0.9)]),
      "ice": ((0.02, 0.05, 0.10, 1), [(0.6, 0.9, 1.0), (0.9, 0.98, 1.0), (0.4, 0.7, 0.95)]),
      "fire": ((0.10, 0.02, 0.01, 1), [(1.0, 0.4, 0.1), (1.0, 0.7, 0.2), (0.9, 0.2, 0.05)]),
      "cosmic": ((0.02, 0.01, 0.08, 1), [(0.6, 0.4, 1.0), (1.0, 0.3, 0.8), (0.3, 0.9, 1.0)]),
      "magic": ((0.05, 0.02, 0.10, 1), [(0.7, 0.3, 1.0), (0.4, 0.9, 0.9), (1.0, 0.6, 0.9)]),
      "fish": ((0.01, 0.05, 0.10, 1), [(0.3, 0.8, 1.0), (0.5, 1.0, 0.9), (0.1, 0.5, 0.9)]),
      "plants": ((0.02, 0.08, 0.03, 1), [(0.3, 1.0, 0.5), (0.7, 1.0, 0.4), (0.1, 0.7, 0.3)]),
      "fur": ((0.08, 0.05, 0.02, 1), [(1.0, 0.6, 0.2), (0.8, 0.5, 0.2), (0.6, 0.35, 0.1)]),
      "minerals": ((0.03, 0.03, 0.05, 1), [(0.8, 0.8, 0.9), (1.0, 0.9, 0.4), (0.6, 0.7, 0.8)]),
      "mushrooms": ((0.05, 0.02, 0.06, 1), [(1.0, 0.5, 0.7), (0.8, 0.4, 1.0), (0.5, 0.9, 1.0)]),
    }
    self.base_color, self.orb_colors = palettes.get(theme, palettes["sun"])

    with self.canvas.before:
      self.bg_color = Color(*self.base_color)
      self.bg_rect = Rectangle(pos=self.pos, size=self.size)
      if style == "particles_up":
        for _ in range(25):
          pc = self.orb_colors[random.randint(0, len(self.orb_colors) - 1)]
          c = Color(pc[0], pc[1], pc[2], 0)
          e = Ellipse(pos=(0, 0), size=(0, 0))
          self.particles.append([c, e, random.uniform(0, 1), random.uniform(0, 1),
                      random.uniform(0.3, 1.5), random.random() * 6.28])
      elif style == "rank_sticks":
        # Короткие вытянутые частицы вместо круглых точек; без крупных орбов по углам.
        for _ in range(28):
          pc = self.orb_colors[random.randint(0, len(self.orb_colors) - 1)]
          c = Color(pc[0], pc[1], pc[2], 0)
          ln = Line(points=[], width=dp(1.5), cap='round')
          self.lines.append([c, ln, random.random(), random.random(), random.uniform(0.4, 1.0), random.random() * 6.28])
      elif style == "corners":
        for i, (fx, fy) in enumerate([(0.05, 0.05), (0.95, 0.05), (0.05, 0.95), (0.95, 0.95)]):
          pc = self.orb_colors[i % len(self.orb_colors)]
          c = Color(pc[0], pc[1], pc[2], 0)
          e = Ellipse(pos=(0, 0), size=(0, 0))
          self.orbs.append([c, e, fx, fy, random.random() * 6.28, i])
        for _ in range(12):
          c = Color(1, 1, 1, 0)
          e = Ellipse(pos=(0, 0), size=(0, 0))
          self.stars.append([c, e, random.random(), random.random(), random.random() * 6.28])
      elif style == "spiral":
        for i in range(30):
          c = Color(0.4, 0.6, 1.0, 0)
          e = Ellipse(pos=(0, 0), size=(0, 0))
          self.particles.append([c, e, i / 30.0, i, 0, 0])
      elif style == "waves":
        for i in range(4):
          c = Color(1, 1, 1, 0)
          ln = Line(points=[], width=dp(2), cap='round')
          self.lines.append([c, ln, i])
      else:
        for _ in range(15):
          c = Color(1, 1, 1, 0)
          e = Ellipse(pos=(0, 0), size=(0, 0))
          self.stars.append([c, e, random.random(), random.random(), random.random() * 6.28])

    self.bind(pos=self._upd, size=self._upd)
    self._ev = Clock.schedule_interval(self._tick, 1.0 / 120.0)

  def _upd(self, *args):
    self.bg_rect.pos = self.pos; self.bg_rect.size = self.size

  def stop_animation(self):
    try:
      if self._ev is not None:
        self._ev.cancel(); self._ev = None
    except: pass
    try: self.canvas.clear()
    except: pass

  def _tick(self, dt):
    self.time += dt
    W, H = self.width, self.height
    if W < 10 or H < 10: return
    if self.style == "particles_up":
      for p in self.particles:
        c, e, x_f, y_f, speed, phase = p
        y = (y_f - self.time * speed * 0.08) % 1.0
        x = x_f + 0.03 * math.sin(self.time * 0.5 + phase)
        r = 2.5 + 2.0 * math.sin(self.time * 1.5 + phase)
        c.a = 0.4 + 0.4 * math.sin(self.time * 2 + phase)
        e.pos = (x * W - r, y * H - r); e.size = (r * 2, r * 2)
    elif self.style == "rank_sticks":
      for c, ln, x_f, y_f, speed, phase in self.lines:
        y = (y_f - self.time * speed * 0.045) % 1.0
        x = x_f + 0.012 * math.sin(self.time * 0.7 + phase)
        length = dp(7 + 3 * (0.5 + 0.5 * math.sin(self.time * 1.4 + phase)))
        dx = dp(1.2) * math.sin(phase)
        c.a = 0.25 + 0.3 * (0.5 + 0.5 * math.sin(self.time * 2 + phase))
        ln.points = [x * W, y * H, x * W + dx, y * H + length]
    elif self.style == "corners":
      for orb in self.orbs:
        c, e, fx, fy, phase, idx = orb
        px = fx * W + 0.05 * W * math.sin(self.time * 0.5 + phase)
        py = fy * H + 0.05 * H * math.cos(self.time * 0.6 + phase)
        r = W * 0.18 + W * 0.03 * math.sin(self.time + phase)
        c.a = 0.15 + 0.12 * math.sin(self.time * 1.2 + phase)
        e.pos = (px - r, py - r); e.size = (r * 2, r * 2)
      for star in self.stars:
        c, e, x_f, y_f, phase = star
        x = x_f * W; y = y_f * H
        r = 1.5 + 1.0 * math.sin(self.time * 2 + phase)
        c.a = 0.5 + 0.4 * math.sin(self.time * 3 + phase)
        e.pos = (x - r, y - r); e.size = (r * 2, r * 2)
    elif self.style == "spiral":
      cx, cy = W / 2, H / 2
      for p in self.particles:
        c, e, t, i, _, _ = p
        angle = t * 8 * math.pi + self.time * 0.5
        radius = (0.05 + 0.45 * t) * min(W, H)
        x = cx + radius * math.cos(angle); y = cy + radius * math.sin(angle)
        r = 2 + 2 * (1 - t)
        pc = self.orb_colors[i % 3]
        c.rgba = (pc[0], pc[1], pc[2], 0.5 + 0.4 * math.sin(self.time * 2 + i))
        e.pos = (x - r, y - r); e.size = (r * 2, r * 2)
    elif self.style == "waves":
      for line in self.lines:
        c, ln, i = line
        pts = []
        y_base = H * (0.15 + 0.18 * i)
        amp = H * 0.04
        for k in range(21):
          t = k / 20.0
          x = t * W
          y = y_base + amp * math.sin(t * 4 * math.pi + self.time * 1.5 + i)
          pts.extend([x, y])
        ln.points = pts
        pc = self.orb_colors[i % len(self.orb_colors)]
        c.rgba = (pc[0], pc[1], pc[2], 0.4)# ============================================================
# РИСОВАНИЕ
# ============================================================
class CatDraw:
  def __init__(self, canvas, size=dp(80), cat_type="orange"):
    self.canvas = canvas; self.size = size; self.cx = 0; self.cy = 0
    self.cat_type = cat_type; self.active = False
    if cat_type in RAINBOW_CAT_COLORS:
      self.is_rainbow = True
      c1, c2, c3 = RAINBOW_CAT_COLORS[cat_type]
      body_c = c1; belly_c = (1, 1, 1); ear_c = c2
      self.stripe_colors = [c1, c2, c3]
    else:
      self.is_rainbow = False
      body_c, belly_c, ear_c = CAT_COLORS.get(cat_type, CAT_COLORS["orange"])
      self.stripe_colors = None
    with canvas:
      self.ear_color = Color(*ear_c, 0)
      self.ear_l = Line(points=[], width=dp(10), cap='round', joint='round', close=True)
      self.ear_r = Line(points=[], width=dp(10), cap='round', joint='round', close=True)
      self.ear_inner_color = Color(*belly_c, 0)
      self.ear_inner_l = Line(points=[], width=dp(5), cap='round', joint='round', close=True)
      self.ear_inner_r = Line(points=[], width=dp(5), cap='round', joint='round', close=True)
      self.stripe_color_1 = Color(1, 1, 1, 0); self.stripe_1 = Line(points=[], width=dp(6), cap='round')
      self.stripe_color_2 = Color(1, 1, 1, 0); self.stripe_2 = Line(points=[], width=dp(6), cap='round')
      self.stripe_color_3 = Color(1, 1, 1, 0); self.stripe_3 = Line(points=[], width=dp(6), cap='round')
      self.body_color = Color(*body_c, 0); self.body = Ellipse()
      self.belly_color = Color(*belly_c, 0); self.belly = Ellipse()
      self.paw_color = Color(*belly_c, 0); self.paw_l = Ellipse(); self.paw_r = Ellipse()
      self.head_color = Color(*body_c, 0); self.head = Ellipse()
      self.face_color = Color(*belly_c, 0); self.face = Ellipse()
      self.eye_color = Color(0.1, 0.1, 0.1, 0); self.eye_l = Ellipse(); self.eye_r = Ellipse()
      self.nose_color = Color(1, 0.4, 0.5, 0); self.nose = Ellipse()

  def set_position(self, cx, cy, clip_x_min=-99999, clip_x_max=99999):
    try:
      self.cx = cx; self.cy = cy
      half = self.size
      if (cx - half >= clip_x_min) and (cx + half <= clip_x_max):
        if not self.active: self.activate()
        self.redraw()
      else:
        if self.active: self.deactivate()
    except: pass

  def activate(self):
    try:
      self.active = True
      for c in [self.ear_color, self.ear_inner_color, self.body_color,
           self.belly_color, self.paw_color, self.head_color,
           self.face_color, self.eye_color, self.nose_color]:
        c.a = 1
      if self.is_rainbow:
        self.stripe_color_1.a = 1; self.stripe_color_2.a = 1; self.stripe_color_3.a = 1
    except: pass

  def deactivate(self):
    try:
      self.active = False
      for obj in [self.ear_l, self.ear_r, self.ear_inner_l, self.ear_inner_r,
            self.stripe_1, self.stripe_2, self.stripe_3]:
        obj.points = []
      for obj in [self.body, self.belly, self.paw_l, self.paw_r,
            self.head, self.face, self.eye_l, self.eye_r, self.nose]:
        obj.pos = (-5000, -5000); obj.size = (0, 0)
    except: pass

  def destroy(self): self.deactivate()

  def hard_remove(self):
    try:
      objs = [self.ear_color, self.ear_l, self.ear_r,
          self.ear_inner_color, self.ear_inner_l, self.ear_inner_r,
          self.stripe_color_1, self.stripe_1,
          self.stripe_color_2, self.stripe_2,
          self.stripe_color_3, self.stripe_3,
          self.body_color, self.body, self.belly_color, self.belly,
          self.paw_color, self.paw_l, self.paw_r,
          self.head_color, self.head, self.face_color, self.face,
          self.eye_color, self.eye_l, self.eye_r,
          self.nose_color, self.nose]
      for obj in objs:
        try: self.canvas.remove(obj)
        except: pass
    except: pass

  def redraw(self):
    s = self.size; cx, cy = self.cx, self.cy
    body_w = s * 0.72; body_h = s * 0.68
    body_x = cx - body_w / 2; body_y = cy - s * 0.55
    self.body.pos = (body_x, body_y); self.body.size = (body_w, body_h)
    belly_w = body_w * 0.55; belly_h = body_h * 0.7
    self.belly.pos = (cx - belly_w / 2, body_y + body_h * 0.08); self.belly.size = (belly_w, belly_h)
    if self.is_rainbow:
      def stripe_path(y_offset, sag):
        pts = []
        x1 = body_x + body_w * 0.08; x2 = body_x + body_w * 0.92
        ybase = body_y + body_h * y_offset
        for i in range(11):
          t = i / 10.0
          pts.extend([x1 + (x2 - x1) * t, ybase - sag * math.sin(math.pi * t)])
        return pts
      self.stripe_1.points = stripe_path(0.80, s * 0.05)
      self.stripe_2.points = stripe_path(0.60, s * 0.06)
      self.stripe_3.points = stripe_path(0.40, s * 0.06)
      c1, c2, c3 = self.stripe_colors
      self.stripe_color_1.rgba = (c1[0], c1[1], c1[2], 1)
      self.stripe_color_2.rgba = (c2[0], c2[1], c2[2], 1)
      self.stripe_color_3.rgba = (c3[0], c3[1], c3[2], 1)
    else:
      self.stripe_1.points = []; self.stripe_2.points = []; self.stripe_3.points = []
    paw_w = body_w * 0.24; paw_h = body_h * 0.16
    self.paw_l.pos = (cx - body_w * 0.30, body_y - paw_h * 0.3); self.paw_l.size = (paw_w, paw_h)
    self.paw_r.pos = (cx + body_w * 0.06, body_y - paw_h * 0.3); self.paw_r.size = (paw_w, paw_h)
    head_size = s * 0.56
    head_x = cx - head_size / 2; head_y = cy + s * 0.02
    self.head.pos = (head_x, head_y); self.head.size = (head_size, head_size)
    ear_h = head_size * 0.32
    self.ear_l.points = [head_x + head_size * 0.10, head_y + head_size * 0.72,
               head_x + head_size * 0.20, head_y + head_size * 0.72 + ear_h,
               head_x + head_size * 0.44, head_y + head_size * 0.88]
    self.ear_r.points = [head_x + head_size * 0.56, head_y + head_size * 0.88,
               head_x + head_size * 0.80, head_y + head_size * 0.72 + ear_h,
               head_x + head_size * 0.90, head_y + head_size * 0.72]
    self.ear_inner_l.points = [head_x + head_size * 0.14, head_y + head_size * 0.76,
                  head_x + head_size * 0.22, head_y + head_size * 0.72 + ear_h * 0.8,
                  head_x + head_size * 0.40, head_y + head_size * 0.85]
    self.ear_inner_r.points = [head_x + head_size * 0.60, head_y + head_size * 0.85,
                  head_x + head_size * 0.78, head_y + head_size * 0.72 + ear_h * 0.8,
                  head_x + head_size * 0.86, head_y + head_size * 0.76]
    face_w = head_size * 0.58; face_h = head_size * 0.44
    self.face.pos = (head_x + head_size * 0.21, head_y + head_size * 0.10); self.face.size = (face_w, face_h)
    eye_w = head_size * 0.13; eye_h = head_size * 0.16
    self.eye_l.pos = (head_x + head_size * 0.30 - eye_w/2, head_y + head_size * 0.52); self.eye_l.size = (eye_w, eye_h)
    self.eye_r.pos = (head_x + head_size * 0.70 - eye_w/2, head_y + head_size * 0.52); self.eye_r.size = (eye_w, eye_h)
    nose_w = head_size * 0.09; nose_h = head_size * 0.06
    self.nose.pos = (head_x + head_size * 0.455, head_y + head_size * 0.30); self.nose.size = (nose_w, nose_h)


class CatArt(FloatLayout):
  def __init__(self, cat_type="orange", size_cat=dp(70), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None); self.size = (size_cat, size_cat)
    self.cat_type = cat_type; self._draw = None
    self.bind(pos=self._redraw, size=self._redraw)
    Clock.schedule_once(self._init_draw, 0.05)

  def _init_draw(self, dt):
    if self.width < 5 or self.height < 5:
      Clock.schedule_once(self._init_draw, 0.1); return
    try:
      self._draw = CatDraw(self.canvas, min(self.width, self.height), self.cat_type)
      self._draw.activate(); self._redraw()
    except: pass

  def _redraw(self, *args):
    try:
      if self._draw is not None: self._draw.set_position(self.center_x, self.center_y)
    except: pass


# Облегчённая векторная графика предметов кейсов: меньше мелких бликов и деталей,
# чтобы снизить число операций рисования при прокрутке. Силуэты и палитры сохранены.
class DetailedItemArt(FloatLayout):
  def __init__(self, item_type, kind, size_s=dp(70), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None)
    self.size = (size_s, size_s)
    self.item_type = item_type
    self.kind = kind
    self.bind(pos=self.redraw, size=self.redraw)
    Clock.schedule_once(self.redraw, 0)

  def _color(self, rgb, a=1):
    Color(float(rgb[0]), float(rgb[1]), float(rgb[2]), a)

  def _ellipse(self, c, x, y, w, h, a=1):
    self._color(c, a); Ellipse(pos=(x, y), size=(w, h))

  def _rect(self, c, x, y, w, h, radius=0, a=1):
    self._color(c, a)
    if radius:
      RoundedRectangle(pos=(x, y), size=(w, h), radius=[radius])
    else:
      Rectangle(pos=(x, y), size=(w, h))

  def _line(self, c, pts, width=1.5, close=False):
    self._color(c); Line(points=pts, width=width, close=close, cap='round', joint='round')

  def _tri(self, c, pts):
    # Lightweight filled shape: preserve recognizable silhouettes without
    # creating a separate outline instruction for every small triangle.
    self._color(c); Triangle(points=pts)

  def redraw(self, *args):
    if self.width < 4 or self.height < 4:
      return
    self.canvas.clear()
    x, y, w, h = self.x, self.y, self.width, self.height
    cx, cy = x+w*.5, y+h*.48
    s = min(w, h)
    palette_map = {
      'fish': FISH_COLORS, 'plants': PLANT_COLORS, 'fur': FUR_COLORS,
      'minerals': MINERAL_COLORS, 'mushrooms': MUSHROOM_COLORS,
      'ice': ICE_COLORS, 'fire': FIRE_COLORS, 'cosmic': COSMIC_COLORS,
      'magic': MAGIC_COLORS,
    }
    pal = palette_map.get(self.item_type, MUSHROOM_COLORS).get(self.kind)
    if not pal:
      pal = ((.55,.45,.75),(.9,.8,1),(.2,.12,.4))
    base, light, dark = pal
    # Сохраняем облегчённый рендер, но используем отдельные силуэты каждого предмета,
    # чтобы животные, рыбы, кристаллы и растения не выглядели одинаковыми кружками.
    with self.canvas:
      # ground shadow for all icons
      self._ellipse((.02,.015,.04), x+w*.22, y+h*.09, w*.56, h*.10, .55)
      t = self.item_type
      if t == 'mushrooms':
        # Stem, underside, broad cap, rim and speckles.
        self._rect((.30,.19,.10), cx-s*.105, y+h*.18, s*.21, s*.34, s*.075)
        self._rect((.96,.84,.62), cx-s*.075, y+h*.20, s*.15, s*.29, s*.06)
        self._ellipse(dark, cx-s*.42, cy-s*.02, s*.84, s*.35)
        self._ellipse(base, cx-s*.42, cy, s*.84, s*.33)
        self._ellipse(light, cx-s*.32, cy+s*.055, s*.64, s*.20)
        self._ellipse((1,1,1), cx-s*.23, cy+s*.12, s*.13, s*.055)
        self._ellipse((1,1,1), cx+s*.08, cy+s*.10, s*.095, s*.05)
        self._ellipse((1,1,1), cx-s*.02, cy+s*.02, s*.07, s*.04)
        self._line(dark, [cx-s*.38,cy+s*.015,cx-s*.22,cy-s*.015,cx,cy-s*.025,cx+s*.24,cy-s*.015,cx+s*.38,cy+s*.015], s*.018)
      elif t == 'fish':
        # Tail fin, fins, layered body, gill, eye and scales.
        self._tri(dark, [x+w*.18,cy,x+w*.04,cy+s*.19,x+w*.04,cy-s*.19])
        self._tri(base, [x+w*.20,cy,x+w*.08,cy+s*.15,x+w*.08,cy-s*.15])
        self._tri(light, [cx-s*.08,cy+s*.02,cx+s*.05,cy+s*.25,cx+s*.17,cy+s*.02])
        self._ellipse(dark, x+w*.16, cy-s*.22, w*.68, h*.43)
        self._ellipse(base, x+w*.17, cy-s*.18, w*.65, h*.40)
        self._ellipse(light, x+w*.22, cy+s*.015, w*.48, h*.19)
        self._line(dark,[cx+s*.16,cy+s*.13,cx+s*.19,cy,cx+s*.16,cy-s*.12],s*.025)
        self._ellipse((.04,.04,.07),cx+s*.22,cy+s*.04,s*.075,s*.075)
        self._ellipse((1,1,1),cx+s*.235,cy+s*.065,s*.025,s*.025)
        for ox,oy in [(-.06,.06)]:
          self._ellipse(light,cx+s*ox,cy+s*oy,s*.045,s*.045,.9)
      elif t == 'plants':
        # Pot/soil, stem, leaves and a multi-petal flower.
        self._rect((.30,.16,.08),cx-s*.19,y+h*.13,s*.38,s*.18,s*.035)
        self._rect((.55,.29,.12),cx-s*.22,y+h*.27,s*.44,s*.055,s*.025)
        self._line((.15,.48,.20),[cx,y+h*.28,cx-s*.015,cy+s*.12,cx+s*.02,cy+s*.35],s*.045)
        self._ellipse((.12,.55,.24),cx-s*.30,cy+s*.02,s*.32,s*.13)
        self._ellipse((.18,.72,.30),cx-s*.27,cy+s*.04,s*.26,s*.09)
        self._ellipse((.12,.55,.24),cx+s*.02,cy+s*.12,s*.30,s*.13)
        self._ellipse((.18,.72,.30),cx+s*.04,cy+s*.14,s*.24,s*.09)
        for i in range(5):
          a=2*math.pi*i/5
          px=cx+math.cos(a)*s*.16; py=cy+s*.34+math.sin(a)*s*.13
          self._ellipse(light,px-s*.075,py-s*.07,s*.15,s*.14)
        self._ellipse(base,cx-s*.13,cy+s*.21,s*.26,s*.25)
        self._ellipse(light,cx-s*.065,cy+s*.27,s*.13,s*.13)
        # Убран дополнительный микроблик
      elif t == 'fur':
        # Distinct animal head with ears, muzzle, eyes and fur markings.
        self._tri(dark,[cx-s*.29,cy+s*.08,cx-s*.30,cy+s*.36,cx-s*.08,cy+s*.25])
        self._tri(dark,[cx+s*.29,cy+s*.08,cx+s*.30,cy+s*.36,cx+s*.08,cy+s*.25])
        self._tri(light,[cx-s*.23,cy+s*.13,cx-s*.23,cy+s*.29,cx-s*.11,cy+s*.23])
        self._tri(light,[cx+s*.23,cy+s*.13,cx+s*.23,cy+s*.29,cx+s*.11,cy+s*.23])
        self._ellipse(dark,cx-s*.34,cy-s*.24,s*.68,s*.62)
        self._ellipse(base,cx-s*.31,cy-s*.20,s*.62,s*.56)
        self._ellipse(light,cx-s*.20,cy-s*.20,s*.40,s*.28)
        self._ellipse((.05,.04,.05),cx-s*.17,cy+s*.04,s*.075,s*.09)
        self._ellipse((.05,.04,.05),cx+s*.095,cy+s*.04,s*.075,s*.09)
        self._ellipse((1,1,1),cx-s*.15,cy+s*.075,s*.025,s*.025)
        self._ellipse((1,1,1),cx+s*.115,cy+s*.075,s*.025,s*.025)
        self._ellipse((.96,.72,.68),cx-s*.12,cy-s*.17,s*.24,s*.16)
        self._ellipse(dark,cx-s*.035,cy-s*.12,s*.07,s*.05)
        self._line(dark,[cx,cy-s*.16,cx-s*.04,cy-s*.20,cx-s*.09,cy-s*.18],s*.012)
        self._line(dark,[cx,cy-s*.16,cx+s*.04,cy-s*.20,cx+s*.09,cy-s*.18],s*.012)
        # fur streaks
        for side in (-1,1):
          self._line(light,[cx+side*s*.23,cy-s*.02,cx+side*s*.18,cy-s*.10],s*.018)
      elif t == 'minerals':
        # Faceted crystal cluster, not a sphere.
        pts=[(cx-s*.35,cy-s*.18),(cx-s*.29,cy+s*.12),(cx-s*.10,cy+s*.33),(cx+s*.06,cy+s*.17),(cx+s*.22,cy+s*.28),(cx+s*.36,cy+s*.02),(cx+s*.27,cy-s*.22),(cx-s*.02,cy-s*.30)]
        self._color(dark); Line(points=[v for p in pts for v in p],close=True,width=s*.025)
        self._tri(base,[cx-s*.35,cy-s*.18,cx-s*.29,cy+s*.12,cx-s*.10,cy+s*.33])
        self._tri(light,[cx-s*.29,cy+s*.12,cx-s*.10,cy+s*.33,cx+s*.06,cy+s*.17])
        self._tri(base,[cx-s*.10,cy+s*.33,cx+s*.06,cy+s*.17,cx+s*.22,cy+s*.28])
        self._tri(light,[cx+s*.06,cy+s*.17,cx+s*.22,cy+s*.28,cx+s*.36,cy+s*.02])
        self._tri(dark,[cx-s*.35,cy-s*.18,cx+s*.36,cy+s*.02,cx+s*.27,cy-s*.22])
        self._line((1,1,1),[cx-s*.20,cy+s*.10,cx-s*.10,cy+s*.25,cx-s*.04,cy+s*.12],s*.025)
        # Убран дополнительный микроблик
      elif t == 'ice':
        # Jagged ice shard with inner crystalline facets.
        pts=[(cx-s*.28,y+h*.20),(cx-s*.20,cy+s*.05),(cx-s*.12,cy+s*.18),(cx-s*.03,y+h*.83),(cx+s*.10,cy+s*.20),(cx+s*.20,cy+s*.04),(cx+s*.28,y+h*.22),(cx+s*.12,y+h*.15),(cx-s*.12,y+h*.15)]
        self._tri(dark,[cx-s*.28,y+h*.20,cx-s*.03,y+h*.83,cx-s*.12,y+h*.15])
        self._tri(base,[cx-s*.03,y+h*.83,cx+s*.10,cy+s*.20,cx-s*.12,y+h*.15])
        self._tri(light,[cx-s*.03,y+h*.83,cx+s*.28,y+h*.22,cx+s*.10,cy+s*.20])
        self._line((.85,1,1),[cx-s*.03,y+h*.83,cx-s*.01,cy+s*.02,cx+s*.10,cy-s*.10],s*.025)
        self._ellipse((1,1,1),cx-s*.16,cy+s*.12,s*.06,s*.06,.8)
      elif t == 'fire':
        # Layered flame silhouette, ember core and sparks.
        self._tri(dark,[cx-s*.32,y+h*.14,cx-s*.25,cy+s*.12,cx-s*.08,cy+s*.03,cx-s*.03,y+h*.83,cx+s*.08,cy+s*.10,cx+s*.22,cy+s*.25,cx+s*.27,y+h*.15])
        self._ellipse(base,cx-s*.27,y+h*.13,s*.54,s*.52)
        self._tri(base,[cx-s*.25,y+h*.30,cx-s*.09,cy+s*.08,cx+s*.02,y+h*.75,cx+s*.12,cy+s*.08,cx+s*.24,y+h*.30])
        self._ellipse(light,cx-s*.15,y+h*.15,s*.30,s*.38)
        self._tri(light,[cx-s*.13,y+h*.30,cx-s*.02,y+h*.68,cx+s*.10,y+h*.30])
        self._ellipse((1,.95,.65),cx-s*.06,y+h*.20,s*.12,s*.16)
        for ox,oy in [(-.31,.55),(.28,.63)]:
          self._ellipse((1,.75,.25),cx+s*ox, y+h*oy,s*.055,s*.055)
      elif t == 'cosmic':
        if self.kind in ('comet','meteor'):
          self._line(light,[cx-s*.42,cy+s*.20,cx-s*.18,cy+s*.10,cx-s*.02,cy],s*.09)
          self._line(base,[cx-s*.40,cy-s*.02,cx-s*.17,cy-s*.02,cx,cy],s*.045)
        self._ellipse(dark,cx-s*.29,cy-s*.28,s*.58,s*.58)
        self._ellipse(base,cx-s*.25,cy-s*.23,s*.50,s*.50)
        self._ellipse(light,cx-s*.15,cy+s*.02,s*.20,s*.17,.85)
        for ox,oy,rr in [(-.14,-.02,.07),(.10,.08,.05),(.08,-.13,.07)]:
          self._ellipse(dark,cx+s*ox,cy+s*oy,s*rr,s*rr,.8)
        if self.kind in ('nebula','supernova','quasar','big_bang','multiverse','wormhole'):
          self._line(light,[cx-s*.42,cy,cx-s*.24,cy+s*.10,cx,cy+s*.14,cx+s*.24,cy+s*.10,cx+s*.42,cy],s*.025)
          self._ellipse((1,1,1),cx+s*.18,cy+s*.18,s*.06,s*.06)
      elif t == 'magic':
        k=self.kind
        if k in ('potion','crystal_ball','orb','philosopher_stone'):
          self._rect(dark,cx-s*.13,y+h*.20,s*.26,s*.34,s*.06)
          self._ellipse(dark,cx-s*.22,y+h*.18,s*.44,s*.38)
          self._ellipse(base,cx-s*.19,y+h*.21,s*.38,s*.32)
          self._ellipse(light,cx-s*.11,y+h*.30,s*.12,s*.14)
          self._ellipse((1,1,1),cx-s*.07,y+h*.39,s*.05,s*.05)
          self._rect(light,cx-s*.10,y+h*.53,s*.20,s*.07,s*.02)
          self._rect(dark,cx-s*.14,y+h*.59,s*.28,s*.06,s*.02)
        elif k in ('wand','staff'):
          self._line(dark,[cx-s*.22,y+h*.15,cx+s*.16,y+h*.72],s*.10)
          self._line(base,[cx-s*.20,y+h*.17,cx+s*.17,y+h*.73],s*.055)
          self._ellipse(light,cx+s*.05,y+h*.66,s*.24,s*.24)
          self._ellipse((1,1,1),cx+s*.10,y+h*.75,s*.06,s*.06)
          for ox,oy in [(-.2,.68),(.28,.60),(.25,.85)]: self._ellipse(light,cx+s*ox,y+h*oy,s*.045,s*.045)
        elif k in ('scroll','tome'):
          self._rect(dark,cx-s*.25,y+h*.19,s*.50,s*.53,s*.04)
          self._rect(base,cx-s*.21,y+h*.22,s*.42,s*.47,s*.025)
          self._line(light,[cx-s*.12,y+h*.58,cx+s*.12,y+h*.58,cx+s*.08,y+h*.49,cx-s*.10,y+h*.49],s*.025)
          self._line(dark,[cx-s*.11,y+h*.40,cx+s*.12,y+h*.40],s*.018)
          self._ellipse(light,cx-s*.05,y+h*.29,s*.10,s*.10)
        else:
          self._ellipse(dark,cx-s*.30,cy-s*.30,s*.60,s*.60)
          self._ellipse(base,cx-s*.25,cy-s*.25,s*.50,s*.50)
          self._line(light,[cx,cy+s*.18,cx+s*.14,cy,cx,cy-s*.18,cx-s*.14,cy,cx,cy+s*.18],s*.035)
          self._ellipse((1,1,1),cx-s*.04,cy+s*.04,s*.08,s*.08)
    # One restrained highlight per item (instead of several tiny glints).
    # Main silhouettes, eyes, fins, leaves and crystal facets remain distinct.
    with self.canvas:
      if self.item_type in ('ice', 'minerals', 'cosmic', 'magic', 'knives', 'guns'):
        self._line((.86,.94,1), [x+w*.70, y+h*.43, x+w*.74, y+h*.51], max(0.6, s*.012))
      elif self.item_type in ('fish', 'plants', 'fur', 'mushrooms', 'cat', 'rainbow', 'spiders'):
        self._ellipse((1.0,.94,.82), x+w*.31, y+h*.65, s*.045, s*.022, .72)


def FishArt(fish_type="guppy", size=dp(70)):
  return DetailedItemArt("fish", fish_type, size)


def PlantArt(plant_type="daisy", size=dp(70)):
  return DetailedItemArt("plants", plant_type, size)


def FurArt(fur_type="fox", size=dp(70)):
  return DetailedItemArt("fur", fur_type, size)


def MineralArt(mineral_type="iron", size=dp(70)):
  return DetailedItemArt("minerals", mineral_type, size)


def MushroomArt(mushroom_type="white", size=dp(70)):
  return DetailedItemArt("mushrooms", mushroom_type, size)


class PlanetDraw:
  def __init__(self, canvas, size=dp(80), planet_type="earth"):
    self.canvas = canvas; self.size = size; self.cx = 0; self.cy = 0
    self.planet_type = planet_type; self.active = False
    body_c, highlight_c = PLANET_COLORS.get(planet_type, PLANET_COLORS["earth"])
    with canvas:
      self.body_color = Color(*body_c, 0); self.body = Ellipse()
      self.highlight_color = Color(*highlight_c, 0); self.highlight = Ellipse()
      self.shadow_color = Color(0, 0, 0, 0); self.shadow = Ellipse()
      self.ring_color = Color(*highlight_c, 0); self.ring = Line(points=[], width=dp(4))

  def set_position(self, cx, cy, clip_x_min=-99999, clip_x_max=99999):
    try:
      self.cx = cx; self.cy = cy
      half = self.size
      if (cx - half >= clip_x_min) and (cx + half <= clip_x_max):
        if not self.active: self.activate()
        self.redraw()
      else:
        if self.active: self.deactivate()
    except: pass

  def activate(self):
    try:
      self.active = True
      self.body_color.a = 1; self.highlight_color.a = 0.7
      self.shadow_color.a = 0.5; self.ring_color.a = 1
    except: pass

  def deactivate(self):
    try:
      self.active = False
      for obj in [self.body, self.highlight, self.shadow]:
        obj.pos = (-5000, -5000); obj.size = (0, 0)
      self.ring.points = []
    except: pass

  def destroy(self): self.deactivate()

  def hard_remove(self):
    try:
      objs = [self.body_color, self.body, self.highlight_color, self.highlight,
          self.shadow_color, self.shadow, self.ring_color, self.ring]
      for obj in objs:
        try: self.canvas.remove(obj)
        except: pass
    except: pass

  def redraw(self):
    s = self.size; cx, cy = self.cx, self.cy
    body_r = s * 0.4
    self.body.pos = (cx - body_r, cy - body_r); self.body.size = (body_r * 2, body_r * 2)
    hl_r = s * 0.15
    self.highlight.pos = (cx - body_r * 0.6 - hl_r/2, cy + body_r * 0.3 - hl_r/2); self.highlight.size = (hl_r, hl_r)
    sh_r = s * 0.3
    self.shadow.pos = (cx + body_r * 0.2 - sh_r/2, cy - body_r * 0.5 - sh_r/2); self.shadow.size = (sh_r, sh_r)
    if self.planet_type == "saturn":
      ring_w = s * 0.75; ring_h = s * 0.18
      pts = []
      for i in range(30):
        a = 2 * math.pi * i / 30
        pts.extend([cx + ring_w / 2 * math.cos(a), cy + ring_h / 2 * math.sin(a)])
      self.ring.points = pts
    else: self.ring.points = []


class PlanetArt(FloatLayout):
  def __init__(self, planet_type="earth", size_p=dp(70), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None); self.size = (size_p, size_p)
    self.planet_type = planet_type; self._draw = None
    self.bind(pos=self._redraw, size=self._redraw)
    Clock.schedule_once(self._init_draw, 0.05)

  def _init_draw(self, dt):
    if self.width < 5 or self.height < 5:
      Clock.schedule_once(self._init_draw, 0.1); return
    try:
      self._draw = PlanetDraw(self.canvas, min(self.width, self.height), self.planet_type)
      self._draw.activate(); self._redraw()
    except: pass

  def _redraw(self, *args):
    try:
      if self._draw is not None: self._draw.set_position(self.center_x, self.center_y)
    except: pass


class KnifeDraw:
  def __init__(self, canvas, size=dp(80), knife_type="karambit_vanilla"):
    self.canvas = canvas; self.size = size; self.cx = 0; self.cy = 0
    self.knife_type = knife_type; self.active = False
    blade_c, shine_c, handle_c = KNIFE_COLORS.get(knife_type, KNIFE_COLORS["karambit_vanilla"])
    with canvas:
      self.ring_color = Color(*handle_c, 0)
      self.ring = Line(points=[], width=dp(4), cap='round', joint='round')
      self.handle_color = Color(*handle_c, 0)
      self.handle = RoundedRectangle(radius=[dp(4)])
      self.blade_color = Color(*blade_c, 0)
      self.blade = Line(points=[], width=dp(8), cap='round', joint='round', close=True)
      self.shine_color = Color(*shine_c, 0)
      self.shine = Line(points=[], width=dp(2), cap='round')

  def set_position(self, cx, cy, clip_x_min=-99999, clip_x_max=99999):
    try:
      self.cx = cx; self.cy = cy
      half = self.size
      if (cx - half >= clip_x_min) and (cx + half <= clip_x_max):
        if not self.active: self.activate()
        self.redraw()
      else:
        if self.active: self.deactivate()
    except: pass

  def activate(self):
    try:
      self.active = True
      for c in [self.ring_color, self.handle_color, self.blade_color, self.shine_color]:
        c.a = 1
    except: pass

  def deactivate(self):
    try:
      self.active = False
      self.ring.points = []; self.blade.points = []; self.shine.points = []
      self.handle.pos = (-5000, -5000); self.handle.size = (0, 0)
    except: pass

  def destroy(self): self.deactivate()

  def hard_remove(self):
    try:
      objs = [self.ring_color, self.ring, self.handle_color, self.handle,
          self.blade_color, self.blade, self.shine_color, self.shine]
      for obj in objs:
        try: self.canvas.remove(obj)
        except: pass
    except: pass

  def redraw(self):
    s = self.size; cx, cy = self.cx, self.cy
    ring_cx = cx + s * 0.32; ring_cy = cy - s * 0.32
    ring_r = s * 0.09
    pts = []
    for i in range(25):
      a = 2 * math.pi * i / 24
      pts.extend([ring_cx + ring_r * math.cos(a), ring_cy + ring_r * math.sin(a)])
    self.ring.points = pts
    self.handle.pos = (cx + s * 0.14, cy - s * 0.22); self.handle.size = (s * 0.14, s * 0.07)
    blade_pts = [
      cx + s * 0.10, cy - s * 0.18, cx - s * 0.05, cy - s * 0.12,
      cx - s * 0.22, cy + s * 0.00, cx - s * 0.34, cy + s * 0.15,
      cx - s * 0.38, cy + s * 0.30, cx - s * 0.32, cy + s * 0.35,
      cx - s * 0.28, cy + s * 0.25, cx - s * 0.20, cy + s * 0.13,
      cx - s * 0.08, cy + s * 0.05, cx + s * 0.08, cy + s * 0.02,
    ]
    self.blade.points = blade_pts
    self.shine.points = blade_pts[:6]


class KnifeArt(FloatLayout):
  def __init__(self, knife_type="karambit_vanilla", size_k=dp(70), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None); self.size = (size_k, size_k)
    self.knife_type = knife_type; self._draw = None
    self.bind(pos=self._redraw, size=self._redraw)
    Clock.schedule_once(self._init_draw, 0.05)

  def _init_draw(self, dt):
    if self.width < 5 or self.height < 5:
      Clock.schedule_once(self._init_draw, 0.1); return
    try:
      self._draw = KnifeDraw(self.canvas, min(self.width, self.height), self.knife_type)
      self._draw.activate(); self._redraw()
    except: pass

  def _redraw(self, *args):
    try:
      if self._draw is not None: self._draw.set_position(self.center_x, self.center_y)
    except: pass


class GunDraw:
  def __init__(self, canvas, size=dp(80), gun_type="glock"):
    self.canvas = canvas; self.size = size; self.cx = 0; self.cy = 0
    self.gun_type = gun_type; self.active = False
    body_c, highlight_c, dark_c = GUN_COLORS.get(gun_type, GUN_COLORS["glock"])
    with canvas:
      self.slide_color = Color(*body_c, 0); self.slide = RoundedRectangle(radius=[dp(4)])
      self.grip_color = Color(*dark_c, 0); self.grip = RoundedRectangle(radius=[dp(3)])
      self.hammer_color = Color(*highlight_c, 0); self.hammer = RoundedRectangle(radius=[dp(2)])
      self.sight_color = Color(*highlight_c, 0); self.sight = RoundedRectangle(radius=[dp(1)])
      self.trigger_color = Color(*dark_c, 0); self.trigger = Line(points=[], width=dp(3), cap='round')

  def set_position(self, cx, cy, clip_x_min=-99999, clip_x_max=99999):
    try:
      self.cx = cx; self.cy = cy
      half = self.size
      if (cx - half >= clip_x_min) and (cx + half <= clip_x_max):
        if not self.active: self.activate()
        self.redraw()
      else:
        if self.active: self.deactivate()
    except: pass

  def activate(self):
    try:
      self.active = True
      for c in [self.slide_color, self.grip_color, self.hammer_color,
           self.sight_color, self.trigger_color]:
        c.a = 1
    except: pass

  def deactivate(self):
    try:
      self.active = False
      for obj in [self.slide, self.grip, self.hammer, self.sight]:
        obj.pos = (-5000, -5000); obj.size = (0, 0)
      self.trigger.points = []
    except: pass

  def destroy(self): self.deactivate()

  def hard_remove(self):
    try:
      objs = [self.slide_color, self.slide, self.grip_color, self.grip,
          self.hammer_color, self.hammer,
          self.sight_color, self.sight, self.trigger_color, self.trigger]
      for obj in objs:
        try: self.canvas.remove(obj)
        except: pass
    except: pass

  def redraw(self):
    s = self.size; cx, cy = self.cx, self.cy
    slide_w = s * 0.75; slide_h = s * 0.18
    slide_x = cx - slide_w * 0.55; slide_y = cy + s * 0.05
    self.slide.pos = (slide_x, slide_y); self.slide.size = (slide_w, slide_h)
    hammer_w = s * 0.10; hammer_h = s * 0.20
    self.hammer.pos = (slide_x + slide_w - hammer_w * 0.2, slide_y - s * 0.01); self.hammer.size = (hammer_w, hammer_h)
    grip_w = s * 0.24; grip_h = s * 0.42
    grip_x = slide_x + slide_w * 0.10; grip_y = slide_y - grip_h + s * 0.05
    self.grip.pos = (grip_x, grip_y); self.grip.size = (grip_w, grip_h)
    sight_w = s * 0.05; sight_h = s * 0.04
    self.sight.pos = (slide_x + slide_w * 0.85, slide_y + slide_h - s * 0.02); self.sight.size = (sight_w, sight_h)
    self.trigger.points = [slide_x + slide_w * 0.35, slide_y - s * 0.01,
                 slide_x + slide_w * 0.40, slide_y - s * 0.10,
                 slide_x + slide_w * 0.50, slide_y - s * 0.01]


class GunArt(FloatLayout):
  def __init__(self, gun_type="glock", size_g=dp(70), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None); self.size = (size_g, size_g)
    self.gun_type = gun_type; self._draw = None
    self.bind(pos=self._redraw, size=self._redraw)
    Clock.schedule_once(self._init_draw, 0.05)

  def _init_draw(self, dt):
    if self.width < 5 or self.height < 5:
      Clock.schedule_once(self._init_draw, 0.1); return
    try:
      self._draw = GunDraw(self.canvas, min(self.width, self.height), self.gun_type)
      self._draw.activate(); self._redraw()
    except: pass

  def _redraw(self, *args):
    try:
      if self._draw is not None: self._draw.set_position(self.center_x, self.center_y)
    except: pass


class SpiderDraw:
  def __init__(self, canvas, size=dp(80), spider_type="red"):
    self.canvas = canvas; self.size = size; self.cx = 0; self.cy = 0
    self.spider_type = spider_type; self.active = False
    body_c, highlight_c, leg_c = SPIDER_COLORS.get(spider_type, SPIDER_COLORS["red"])
    with canvas:
      self.leg_color = Color(*leg_c, 0)
      self.legs = [Line(points=[], width=dp(6), cap='round', joint='round') for _ in range(4)]
      self.body_color = Color(*body_c, 0); self.body = Ellipse()
      self.head_color = Color(*highlight_c, 0); self.head = Ellipse()
      self.eye_color = Color(1, 1, 1, 0); self.eye_l = Ellipse(); self.eye_r = Ellipse()

  def set_position(self, cx, cy, clip_x_min=-99999, clip_x_max=99999):
    try:
      self.cx = cx; self.cy = cy
      half = self.size
      if (cx - half >= clip_x_min) and (cx + half <= clip_x_max):
        if not self.active: self.activate()
        self.redraw()
      else:
        if self.active: self.deactivate()
    except: pass

  def activate(self):
    try:
      self.active = True
      for c in [self.leg_color, self.body_color, self.head_color, self.eye_color]:
        c.a = 1
    except: pass

  def deactivate(self):
    try:
      self.active = False
      for leg in self.legs: leg.points = []
      for obj in [self.body, self.head, self.eye_l, self.eye_r]:
        obj.pos = (-5000, -5000); obj.size = (0, 0)
    except: pass

  def destroy(self): self.deactivate()

  def hard_remove(self):
    try:
      objs = [self.leg_color] + self.legs + [self.body_color, self.body,
          self.head_color, self.head, self.eye_color, self.eye_l, self.eye_r]
      for obj in objs:
        try: self.canvas.remove(obj)
        except: pass
    except: pass

  def redraw(self):
    s = self.size; cx, cy = self.cx, self.cy
    abdomen_r = s * 0.28; abdomen_cy = cy - s * 0.10
    self.body.pos = (cx - abdomen_r, abdomen_cy - abdomen_r); self.body.size = (abdomen_r * 2, abdomen_r * 2)
    head_r = s * 0.18; head_cy = cy + s * 0.15
    self.head.pos = (cx - head_r, head_cy - head_r); self.head.size = (head_r * 2, head_r * 2)
    eye_r_size = s * 0.03
    self.eye_l.pos = (cx - head_r * 0.5, head_cy + head_r * 0.15); self.eye_l.size = (eye_r_size, eye_r_size)
    self.eye_r.pos = (cx + head_r * 0.5 - eye_r_size, head_cy + head_r * 0.15); self.eye_r.size = (eye_r_size, eye_r_size)
    leg_len = s * 0.38
    self.legs[0].points = [cx + head_r * 0.5, cy + s * 0.20,
                (cx + head_r * 0.5 + cx + leg_len) / 2, cy + s * 0.40,
                cx + leg_len, cy + s * 0.30]
    self.legs[1].points = [cx + abdomen_r * 0.5, cy - s * 0.05,
                (cx + abdomen_r * 0.5 + cx + leg_len * 0.95) / 2, cy + s * 0.05,
                cx + leg_len * 0.95, cy - s * 0.10]
    self.legs[2].points = [cx - head_r * 0.5, cy + s * 0.20,
                (cx - head_r * 0.5 + cx - leg_len) / 2, cy + s * 0.40,
                cx - leg_len, cy + s * 0.30]
    self.legs[3].points = [cx - abdomen_r * 0.5, cy - s * 0.05,
                (cx - abdomen_r * 0.5 + cx - leg_len * 0.95) / 2, cy + s * 0.05,
                cx - leg_len * 0.95, cy - s * 0.10]


class SpiderArt(FloatLayout):
  def __init__(self, spider_type="red", size_s=dp(70), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None); self.size = (size_s, size_s)
    self.spider_type = spider_type; self._draw = None
    self.bind(pos=self._redraw, size=self._redraw)
    Clock.schedule_once(self._init_draw, 0.05)

  def _init_draw(self, dt):
    if self.width < 5 or self.height < 5:
      Clock.schedule_once(self._init_draw, 0.1); return
    try:
      self._draw = SpiderDraw(self.canvas, min(self.width, self.height), self.spider_type)
      self._draw.activate(); self._redraw()
    except: pass

  def _redraw(self, *args):
    try:
      if self._draw is not None: self._draw.set_position(self.center_x, self.center_y)
    except: pass


class SunDraw:
  def __init__(self, canvas, size=dp(80)):
    self.canvas = canvas; self.size = size; self.cx = 0; self.cy = 0
    self.active = False
    with canvas:
      self.glow_color = Color(1, 0.85, 0.3, 0); self.glow = Ellipse()
      self.body_color = Color(1, 0.7, 0.15, 0); self.body = Ellipse()
      self.core_color = Color(1, 0.95, 0.5, 0); self.core = Ellipse()

  def set_position(self, cx, cy, clip_x_min=-99999, clip_x_max=99999):
    try:
      self.cx = cx; self.cy = cy
      half = self.size
      if (cx - half >= clip_x_min) and (cx + half <= clip_x_max):
        if not self.active: self.activate()
        self.redraw()
      else:
        if self.active: self.deactivate()
    except: pass

  def activate(self):
    try:
      self.active = True
      self.glow_color.a = 0.35; self.body_color.a = 0.9; self.core_color.a = 1
    except: pass

  def deactivate(self):
    try:
      self.active = False
      for obj in [self.glow, self.body, self.core]:
        obj.pos = (-5000, -5000); obj.size = (0, 0)
    except: pass

  def destroy(self): self.deactivate()

  def hard_remove(self):
    try:
      objs = [self.glow_color, self.glow, self.body_color, self.body,
          self.core_color, self.core]
      for obj in objs:
        try: self.canvas.remove(obj)
        except: pass
    except: pass

  def redraw(self):
    s = self.size; cx, cy = self.cx, self.cy
    glow_r = s * 0.5
    self.glow.pos = (cx - glow_r, cy - glow_r); self.glow.size = (glow_r * 2, glow_r * 2)
    body_r = s * 0.38
    self.body.pos = (cx - body_r, cy - body_r); self.body.size = (body_r * 2, body_r * 2)
    core_r = s * 0.22
    self.core.pos = (cx - core_r, cy - core_r); self.core.size = (core_r * 2, core_r * 2)


class SunArt(FloatLayout):
  def __init__(self, size_s=dp(70), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None); self.size = (size_s, size_s)
    self._draw = None
    self.bind(pos=self._redraw, size=self._redraw)
    Clock.schedule_once(self._init_draw, 0.05)

  def _init_draw(self, dt):
    if self.width < 5 or self.height < 5:
      Clock.schedule_once(self._init_draw, 0.1); return
    try:
      self._draw = SunDraw(self.canvas, min(self.width, self.height))
      self._draw.activate(); self._redraw()
    except: pass

  def _redraw(self, *args):
    try:
      if self._draw is not None: self._draw.set_position(self.center_x, self.center_y)
    except: pass


# Для ледяных, огненных, космических и магических наград используются
# отдельные узнаваемые силуэты вместо цветных кругов.
def IceArt(ice_type="frost", size=dp(70)):
  return DetailedItemArt("ice", ice_type, size)


def FireArt(fire_type="spark", size=dp(70)):
  return DetailedItemArt("fire", fire_type, size)


def CosmicArt(cosmic_type="asteroid", size=dp(70)):
  return DetailedItemArt("cosmic", cosmic_type, size)


def MagicArt(magic_type="rune", size=dp(70)):
  return DetailedItemArt("magic", magic_type, size)


def make_art(item_type, kind, size):
  if item_type in ("cat", "rainbow"): return CatArt(kind, size)
  if item_type == "planet": return PlanetArt(kind, size)
  if item_type == "knives": return KnifeArt(kind, size)
  if item_type == "spiders": return SpiderArt(kind, size)
  if item_type == "guns": return GunArt(kind, size)
  if item_type == "ice": return IceArt(kind, size)
  if item_type == "fire": return FireArt(kind, size)
  if item_type == "cosmic": return CosmicArt(kind, size)
  if item_type == "magic": return MagicArt(kind, size)
  if item_type == "fish": return FishArt(kind, size)
  if item_type == "plants": return PlantArt(kind, size)
  if item_type == "fur": return FurArt(kind, size)
  if item_type == "minerals": return MineralArt(kind, size)
  if item_type == "mushrooms": return MushroomArt(kind, size)
  return CatArt("orange", size)


# ============================================================
# СУНДУКИ
# ============================================================
class ChestDraw:
  def __init__(self, canvas, size=dp(120), chest_type="cats"):
    self.canvas = canvas; self.size = size; self.cx = 0; self.cy = 0
    self.chest_type = chest_type; self.active = False
    configs = {
      "cats": ((0.55, 0.32, 0.15), (0.65, 0.40, 0.20), (0.95, 0.78, 0.25), (0.75, 0.55, 0.10), (1, 0.85, 0.35)),
      "planets": ((0.18, 0.22, 0.45), (0.25, 0.30, 0.55), (0.55, 0.75, 1.0), (0.30, 0.50, 0.85), (0.75, 0.90, 1.0)),
      "knives": ((0.15, 0.15, 0.20), (0.25, 0.25, 0.32), (0.85, 0.30, 0.30), (0.60, 0.15, 0.15), (1.0, 0.55, 0.55)),
      "spiders": ((0.35, 0.15, 0.55), (0.50, 0.20, 0.70), (1.0, 0.85, 0.30), (0.85, 0.55, 0.15), (1.0, 0.95, 0.55)),
      "rainbow": ((0.85, 0.25, 0.55), (0.95, 0.4, 0.7), (1.0, 0.85, 0.25), (0.6, 0.9, 1.0), (1.0, 0.95, 0.55)),
      "guns": ((0.25, 0.28, 0.30), (0.35, 0.38, 0.42), (0.85, 0.85, 0.90), (0.5, 0.5, 0.55), (0.95, 0.95, 1.0)),
      "ice": ((0.4, 0.7, 0.9), (0.5, 0.8, 1.0), (0.9, 1.0, 1.0), (0.6, 0.9, 1.0), (1.0, 1.0, 1.0)),
      "fire": ((0.6, 0.15, 0.05), (0.8, 0.25, 0.1), (1.0, 0.7, 0.2), (1.0, 0.5, 0.05), (1.0, 0.95, 0.6)),
      "cosmic": ((0.1, 0.05, 0.25), (0.2, 0.1, 0.4), (0.9, 0.6, 1.0), (0.6, 0.3, 0.9), (1.0, 0.85, 1.0)),
      "magic": ((0.3, 0.1, 0.5), (0.4, 0.15, 0.65), (1.0, 0.85, 0.4), (0.9, 0.5, 0.2), (1.0, 0.95, 0.7)),
      "fish": ((0.1, 0.3, 0.5), (0.15, 0.4, 0.65), (0.5, 0.9, 1.0), (0.3, 0.7, 0.9), (0.8, 1.0, 1.0)),
      "plants": ((0.15, 0.4, 0.2), (0.2, 0.55, 0.3), (0.5, 0.9, 0.4), (0.3, 0.7, 0.2), (0.7, 1.0, 0.6)),
      "fur": ((0.4, 0.25, 0.1), (0.5, 0.35, 0.15), (0.9, 0.7, 0.4), (0.7, 0.5, 0.2), (1.0, 0.85, 0.6)),
      "minerals": ((0.3, 0.3, 0.35), (0.4, 0.4, 0.45), (0.9, 0.9, 1.0), (0.6, 0.6, 0.7), (1.0, 1.0, 1.0)),
      "mushrooms": ((0.4, 0.1, 0.3), (0.55, 0.15, 0.4), (1.0, 0.6, 0.8), (0.9, 0.4, 0.6), (1.0, 0.85, 0.9)),
    }
    body_c, lid_c, strap_c, strap_d, accent_c = configs.get(chest_type, configs["cats"])
    with canvas:
      self.shadow_color = Color(0, 0, 0, 0); self.shadow = Ellipse()
      self.body_color = Color(*body_c, 0); self.body = RoundedRectangle(radius=[dp(8)])
      self.lid_color = Color(*lid_c, 0); self.lid = RoundedRectangle(radius=[dp(10)])
      self.strap_color = Color(*strap_c, 0)
      self.strap_l = RoundedRectangle(radius=[dp(3)])
      self.strap_r = RoundedRectangle(radius=[dp(3)])
      self.strap_h_color = Color(*strap_d, 0)
      self.strap_h = RoundedRectangle(radius=[dp(3)])
      self.lock_color = Color(*accent_c, 0)
      self.lock_bg = RoundedRectangle(radius=[dp(5)])
      self.lock_hole_color = Color(0.15, 0.10, 0.05, 0)
      self.lock_hole = Ellipse()
      # Объёмные детали корпуса кейса: фаски, панели, швы, заклёпки и блики.
      self.edge_color = Color(0.04, 0.05, 0.08, 0)
      self.body_edge = RoundedRectangle(radius=[dp(8)])
      self.panel_color = Color(1, 1, 1, 0)
      self.body_panel = RoundedRectangle(radius=[dp(5)])
      self.lid_panel = RoundedRectangle(radius=[dp(5)])
      self.top_glint_color = Color(1, 1, 1, 0)
      self.top_glint = Line(points=[], width=dp(1.2))
      self.seam_color = Color(0.03, 0.03, 0.05, 0)
      self.seam = Line(points=[], width=dp(1))
      self.rivet_color = Color(0.9, 0.9, 1, 0)
      self.rivets = [Ellipse() for _ in range(8)]
      self.texture_color = Color(1, 1, 1, 0)
      self.texture_lines = [Line(points=[], width=dp(0.6)) for _ in range(5)]

  def set_position(self, cx, cy, clip_x_min=-99999, clip_x_max=99999):
    try:
      self.cx = cx; self.cy = cy
      half = self.size * 0.8
      if (cx - half >= clip_x_min) and (cx + half <= clip_x_max):
        if not self.active: self.activate()
        self.redraw()
      else:
        if self.active: self.deactivate()
    except: pass

  def activate(self):
    try:
      self.active = True
      self.shadow_color.a = 0.25
      for c in [self.body_color, self.lid_color, self.strap_color,
           self.strap_h_color, self.lock_color, self.lock_hole_color,
           self.edge_color, self.panel_color, self.top_glint_color,
           self.seam_color, self.rivet_color, self.texture_color]:
        c.a = 1
    except: pass

  def deactivate(self):
    try:
      self.active = False
      for obj in [self.shadow, self.body, self.lid, self.strap_l, self.strap_r,
            self.strap_h, self.lock_bg, self.lock_hole, self.body_edge,
            self.body_panel, self.lid_panel, *self.rivets]:
        obj.pos = (-5000, -5000); obj.size = (0, 0)
      for obj in [self.top_glint, self.seam, *self.texture_lines]: obj.points = []
    except: pass

  def destroy(self): self.deactivate()

  def hard_remove(self):
    try:
      objs = [self.shadow_color, self.shadow, self.body_color, self.body,
          self.lid_color, self.lid, self.strap_color, self.strap_l, self.strap_r,
          self.strap_h_color, self.strap_h, self.lock_color, self.lock_bg,
          self.lock_hole_color, self.lock_hole, self.edge_color, self.body_edge,
          self.panel_color, self.body_panel, self.lid_panel, self.top_glint_color,
          self.top_glint, self.seam_color, self.seam, self.rivet_color,
          *self.rivets, self.texture_color, *self.texture_lines]
      for obj in objs:
        try: self.canvas.remove(obj)
        except: pass
    except: pass

  def redraw(self):
    s = self.size; cx, cy = self.cx, self.cy
    w = s * 1.0; h = s * 0.7
    x = cx - w / 2; y = cy - h / 2
    sh_w = w * 1.05; sh_h = h * 0.18
    self.shadow.pos = (cx - sh_w / 2, y - sh_h * 0.6); self.shadow.size = (sh_w, sh_h)
    body_h = h * 0.55
    self.body.pos = (x, y); self.body.size = (w, body_h)
    lid_h = h * 0.45
    self.lid.pos = (x, y + body_h - dp(2)); self.lid.size = (w, lid_h)
    strap_w = w * 0.07
    self.strap_l.pos = (x + w * 0.15, y); self.strap_l.size = (strap_w, h - dp(2))
    self.strap_r.pos = (x + w * 0.78, y); self.strap_r.size = (strap_w, h - dp(2))
    strap_h_h = h * 0.08
    self.strap_h.pos = (x, y + body_h * 0.6); self.strap_h.size = (w, strap_h_h)
    lock_w = w * 0.20; lock_h = h * 0.22
    self.lock_bg.pos = (cx - lock_w / 2, y + body_h - lock_h * 0.6); self.lock_bg.size = (lock_w, lock_h)
    hole_r = lock_w * 0.18
    self.lock_hole.pos = (cx - hole_r, y + body_h - lock_h * 0.35); self.lock_hole.size = (hole_r * 2, hole_r * 2)
    # Панели корпуса и крышки с тонкой фаской.
    self.body_edge.pos = (x + w * 0.025, y + h * 0.035)
    self.body_edge.size = (w * 0.95, body_h * 0.90)
    self.body_panel.pos = (x + w * 0.09, y + body_h * 0.13)
    self.body_panel.size = (w * 0.82, body_h * 0.70)
    self.lid_panel.pos = (x + w * 0.08, y + body_h + lid_h * 0.14)
    self.lid_panel.size = (w * 0.84, lid_h * 0.68)
    self.top_glint.points = [x+w*.12, y+body_h+lid_h*.83, x+w*.82, y+body_h+lid_h*.83]
    self.seam.points = [x+w*.04, y+body_h, x+w*.96, y+body_h]
    rivet_r = max(dp(1.5), s * 0.025)
    rivet_xy = [(x+w*.10,y+body_h*.20),(x+w*.90,y+body_h*.20),
          (x+w*.10,y+body_h*.78),(x+w*.90,y+body_h*.78),
          (x+w*.12,y+body_h+lid_h*.30),(x+w*.88,y+body_h+lid_h*.30),
          (x+w*.12,y+body_h+lid_h*.78),(x+w*.88,y+body_h+lid_h*.78)]
    for dot, (rx, ry) in zip(self.rivets, rivet_xy):
      dot.pos = (rx-rivet_r, ry-rivet_r); dot.size = (rivet_r*2, rivet_r*2)
    for i, line in enumerate(self.texture_lines):
      yy = y + body_h * (0.22 + i * 0.13)
      line.points = [x+w*.22, yy, x+w*.42, yy+h*.018]
    self.panel_color.rgba = (min(1,self.body_color.r*1.35), min(1,self.body_color.g*1.35), min(1,self.body_color.b*1.35), .42)
    self.top_glint_color.rgba = (1,1,1,.68)
    self.seam_color.rgba = (.02,.025,.04,.72)
    self.edge_color.rgba = (.025,.03,.045,.48)
    self.rivet_color.rgba = (.92,.95,1,.82)
    self.texture_color.rgba = (1,1,1,.18)


class ChestArt(FloatLayout):
  """ФИКС: теперь с фиксированным size_hint"""
  def __init__(self, chest_type="cats", size_c=dp(120), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None)
    self.size = (size_c, size_c)
    self.chest_type = chest_type
    self._draw = None
    self._last_pos = (None, None)
    self.bind(pos=self._redraw, size=self._redraw)
    Clock.schedule_once(self._init_draw, 0.05)
    Clock.schedule_once(self._redraw, 0.15)
    Clock.schedule_once(self._redraw, 0.3)

  def _init_draw(self, dt):
    if self.width < 5 or self.height < 5:
      Clock.schedule_once(self._init_draw, 0.1); return
    try:
      self._draw = ChestDraw(self.canvas, min(self.width, self.height), self.chest_type)
      self._draw.activate(); self._redraw()
    except: pass

  def _redraw(self, *args):
    try:
      if self._draw is None: return
      cx = self.x + self.width / 2; cy = self.y + self.height / 2
      if (cx, cy) == self._last_pos and self._draw.active: return
      self._last_pos = (cx, cy)
      self._draw.set_position(cx, cy)
    except: pass


# ============================================================
# РАНГ-ИКОНКА
# ============================================================
class RankIcon(FloatLayout):
  """Компактная многослойная эмблема ранга с металлической окантовкой.
  Использует только Canvas-примитивы, чтобы не создавать тяжёлые изображения."""
  def __init__(self, rank_idx=0, size_r=dp(90), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None); self.size = (size_r, size_r)
    self.rank_idx = max(0, min(rank_idx, len(RANKS) - 1))
    with self.canvas:
      # Тёмная подложка и толстый внешний металлический кант.
      self.shadow_color = Color(0.015, 0.02, 0.04, 0.95)
      self.shadow = Line(points=[], width=dp(8), cap='round', joint='round', close=True)
      self.edge_color = Color(0.72, 0.76, 0.84, 1)
      self.edge = Line(points=[], width=dp(5), cap='round', joint='round', close=True)
      self.shield_color = Color(0.2, 0.22, 0.28, 1)
      self.shield = Line(points=[], width=dp(3), cap='round', joint='round', close=True)
      self.inner_color = Color(0.95, 0.96, 1.0, 1)
      self.inner = Line(points=[], width=dp(2), cap='round', joint='round', close=True)
      self.wing_color = Color(1, 1, 1, 1)
      self.wings = [Line(points=[], width=dp(3.2), cap='round', joint='round') for _ in range(2)]
      self.crown_color = Color(1, 0.88, 0.32, 1)
      self.crown = Line(points=[], width=dp(3), cap='round', joint='round', close=True)
      # Деления ранга рисуем короткими палочками, а не круглыми точками.
      self.gem_colors = []
      self.gems = []
      for _ in range(3):
        self.gem_colors.append(Color(1, 1, 1, 1))
        self.gems.append(Rectangle(pos=(-5000, -5000), size=(0, 0)))
      self.glint_color = Color(1, 1, 1, 0.72)
      self.glint = Line(points=[], width=dp(1.4), cap='round')
      # Elite badge: a small world medallion with feather-like wings.
      self.elite_globe_color = Color(0.15, 0.55, 0.95, 0.0)
      self.elite_globe = Ellipse(pos=(-5000, -5000), size=(0, 0))
      self.elite_globe_edge_color = Color(0.75, 0.95, 1.0, 0.0)
      self.elite_globe_edge = Line(circle=(-5000, -5000, 1), width=dp(1.5))
      self.elite_meridians = [Line(points=[], width=dp(1.1)) for _ in range(3)]
      self.elite_latitudes = [Line(points=[], width=dp(1.1)) for _ in range(2)]
    self.bind(pos=self.redraw, size=self.redraw)
    Clock.schedule_once(lambda dt: self.redraw(), 0.05)

  def redraw(self, *args):
    s = self.width
    if s < 5: return
    cx = self.x + s / 2; cy = self.y + s / 2
    idx = self.rank_idx
    base = RANKS[idx][2]; light = RANKS[idx][3]
    # Polygonal shield silhouette, with a slightly different top for elite ranks.
    r = s * (0.36 if idx <= 2 else 0.39)
    pts = [cx-r*0.82, cy+r*0.45, cx-r*0.70, cy+r*0.78,
        cx, cy+r*0.98, cx+r*0.70, cy+r*0.78,
        cx+r*0.82, cy+r*0.45, cx+r*0.70, cy-r*0.34,
        cx, cy-r*0.88, cx-r*0.70, cy-r*0.34]
    self.shadow.points = pts
    self.edge.points = pts
    self.edge_color.rgba = (min(1, light[0]*0.92+0.08), min(1, light[1]*0.92+0.08), min(1, light[2]*0.92+0.08), 1)
    inner_pts = []
    for i in range(0, len(pts), 2):
      inner_pts.extend([cx + (pts[i]-cx)*0.82, cy + (pts[i+1]-cy)*0.82])
    self.shield.points = inner_pts
    self.shield_color.rgba = (base[0]*0.48, base[1]*0.48, base[2]*0.48, 1)
    inner2 = []
    for i in range(0, len(pts), 2):
      inner2.extend([cx + (pts[i]-cx)*0.59, cy + (pts[i+1]-cy)*0.59])
    self.inner.points = inner2
    self.inner_color.rgba = (*light, 0.95)
    # Tier accents: side fins for advanced ranks and a crown for the highest tier.
    if idx >= 6:
      wl = s * (0.25 if RANKS[idx][0] == "elite" else 0.18)
      if RANKS[idx][0] == "elite":
        self.wings[0].points = [cx-s*0.25,cy+s*0.08, cx-s*0.42,cy+s*0.22,
          cx-s*0.50,cy+s*0.18, cx-s*0.43,cy+s*0.10,
          cx-s*0.53,cy+s*0.08, cx-s*0.43,cy+s*0.015,
          cx-s*0.48,cy-s*0.06, cx-s*0.36,cy-s*0.055, cx-s*0.25,cy-s*0.12]
        self.wings[1].points = [cx+s*0.25,cy+s*0.08, cx+s*0.42,cy+s*0.22,
          cx+s*0.50,cy+s*0.18, cx+s*0.43,cy+s*0.10,
          cx+s*0.53,cy+s*0.08, cx+s*0.43,cy+s*0.015,
          cx+s*0.48,cy-s*0.06, cx+s*0.36,cy-s*0.055, cx+s*0.25,cy-s*0.12]
      else:
        # Новая текстура крыльев: вытянутые перья с зубчатым краем.
        left_pts = [
          cx-s*0.29, cy+s*0.05,
          cx-s*0.39, cy+s*0.20,
          cx-s*0.43, cy+s*0.14,
          cx-s*0.49, cy+s*0.16,
          cx-s*0.46, cy+s*0.07,
          cx-s*0.53, cy+s*0.07,
          cx-s*0.47, cy-s*0.01,
          cx-s*0.49, cy-s*0.09,
          cx-s*0.41, cy-s*0.07,
          cx-s*0.34, cy-s*0.13,
          cx-s*0.28, cy-s*0.04]
        right_pts = []
        for j in range(0, len(left_pts), 2):
          right_pts.extend([2*cx-left_pts[j], left_pts[j+1]])
        self.wings[0].points = left_pts
        self.wings[1].points = right_pts
      self.wing_color.rgba = (*light, 1)
    else:
      self.wings[0].points = []; self.wings[1].points = []
    if idx >= len(RANKS)-1:
      cr=s*0.30 if RANKS[idx][0] == "pro" else s*0.24
      self.crown.points = [cx-cr,cy+s*0.29,cx-cr*0.72,cy+s*0.43,
                 cx-cr*0.32,cy+s*0.33,cx,cy+s*0.48,
                 cx+cr*0.32,cy+s*0.33,cx+cr*0.72,cy+s*0.43,
                 cx+cr,cy+s*0.29,cx+cr,cy+s*0.19,cx-cr,cy+s*0.19]
      self.crown_color.rgba = (1.0, 0.95, 0.05, 1) if RANKS[idx][0] == "pro" else (*light, 1)
    else:
      self.crown.points = []; self.crown_color.a = 0
    level = (idx % 3) + 1 if idx <= 8 else min(3, 1 + (idx-9)//3)
    for i, (gc, g) in enumerate(zip(self.gem_colors, self.gems)):
      if i < level:
        # Тонкие прямоугольные вертикальные деления I / II / III без скругления.
        gx = cx + (i-(level-1)/2)*s*0.12
        gy = cy + s*0.015
        bar_w = max(dp(2.2), s * 0.038)
        bar_h = s * 0.14
        g.pos = (gx - bar_w / 2, gy - bar_h / 2)
        g.size = (bar_w, bar_h)
        gc.rgba = (1, 1, 1, 1) if i == 0 else (*light, 1)
      else:
        g.pos = (-5000, -5000)
        g.size = (0, 0)
    self.glint.points = [cx-r*0.48, cy+r*0.42, cx-r*0.15, cy+r*0.62]
    rank_id = RANKS[idx][0]
    if rank_id in ("elite", "champion", "legend", "pro"):
      # Глобус для высших рангов; цвет подбирается под цвет конкретного ранга.
      gr = s * 0.17
      self.elite_globe.pos = (cx-gr, cy-gr*0.62)
      self.elite_globe.size = (2*gr, 1.24*gr)
      globe_palette = {
        "elite": ((0.08, 0.34, 0.78, 1), (0.72, 0.95, 1.0, 1)),
        "champion": ((0.95, 0.48, 0.06, 1), (1.0, 0.84, 0.32, 1)),
        "legend": ((0.72, 0.12, 0.28, 1), (1.0, 0.62, 0.72, 1)),
        "pro": ((0.12, 0.42, 0.12, 1), (1.0, 0.92, 0.08, 1)),
      }
      globe_fill, globe_edge = globe_palette[rank_id]
      self.elite_globe_color.rgba = globe_fill
      self.elite_globe_edge_color.rgba = globe_edge
      self.elite_globe_edge.circle = (cx, cy, gr*0.92)
      self.elite_meridians[0].points = [cx,cy-gr*0.60,cx-s*0.035,cy-gr*0.28,cx-s*0.035,cy+gr*0.28,cx,cy+gr*0.60]
      self.elite_meridians[1].points = [cx,cy-gr*0.60,cx+s*0.035,cy-gr*0.28,cx+s*0.035,cy+gr*0.28,cx,cy+gr*0.60]
      self.elite_meridians[2].points = [cx-gr*0.42,cy,cx+gr*0.42,cy]
      self.elite_latitudes[0].points = [cx-gr*0.78,cy-gr*0.22,cx,cy-gr*0.30,cx+gr*0.78,cy-gr*0.22]
      self.elite_latitudes[1].points = [cx-gr*0.78,cy+gr*0.22,cx,cy+gr*0.30,cx+gr*0.78,cy+gr*0.22]
      for line in self.elite_meridians + self.elite_latitudes:
        line.width = dp(1.1)
        line_color = globe_edge
        # Цвет линий глобуса совпадает с его светлой окантовкой.
        # Kivy Line использует текущий Color, поэтому цвет задан отдельным canvas Color ниже.
      self.elite_globe_edge_color.rgba = globe_edge
    else:
      self.elite_globe.pos = (-5000,-5000); self.elite_globe.size = (0,0)
      self.elite_globe_color.rgba = (0.08,0.34,0.78,0)
      self.elite_globe_edge_color.rgba = (0.72,0.95,1.0,0)
      self.elite_globe_edge.circle = (-5000,-5000,1)
      for line in self.elite_meridians + self.elite_latitudes:
        line.points = []


# ============================================================
# РАМКИ
# ============================================================
class FrameArt(FloatLayout):
  def __init__(self, frame_key="none", size_f=dp(120), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None); self.size = (size_f, size_f)
    self.frame_key = frame_key
    with self.canvas:
      color = None; shape = "circle"
      for fk, fn, fp, fc, fs in FRAMES:
        if fk == frame_key:
          color = fc; shape = fs; break
      self.shape = shape
      self.main_color = Color(*(color if color else (0.5, 0.5, 0.5)), 0.0)
      self.line = Line(points=[], width=dp(6), cap='round', joint='round', close=True)
      self.glow_color = Color(*(color if color else (0.5, 0.5, 0.5)), 0.0)
      self.glow = Ellipse(pos=(-5000, -5000), size=(0, 0))
      self.extra_color = Color(1, 1, 1, 0.0)
      self.extras = [Line(points=[], width=dp(2), cap='round') for _ in range(8)]
    self.bind(pos=self.redraw, size=self.redraw)
    Clock.schedule_once(lambda dt: self.redraw(), 0.05)

  def redraw(self, *args):
    s = self.width
    if s < 5: return
    cx = self.x + s / 2; cy = self.y + s / 2
    color = None
    for fk, fn, fp, fc, fs in FRAMES:
      if fk == self.frame_key:
        color = fc; break
    if color is None:
      self.main_color.a = 0; self.glow_color.a = 0; self.extra_color.a = 0
      self.line.points = []; self.glow.pos = (-5000, -5000); self.glow.size = (0, 0)
      for e in self.extras: e.points = []
      return
    self.main_color.rgba = (color[0], color[1], color[2], 1)
    self.glow_color.rgba = (color[0], color[1], color[2], 0.35)
    glow_r = s * 0.5
    self.glow.pos = (cx - glow_r, cy - glow_r); self.glow.size = (glow_r * 2, glow_r * 2)
    if self.shape == "circle":
      r = s * 0.42
      pts = []
      for i in range(25):
        a = 2 * math.pi * i / 24
        pts.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
      self.line.points = pts
    elif self.shape == "star":
      pts = []
      for i in range(11):
        a = -math.pi / 2 + 2 * math.pi * i / 10
        r = s * 0.45 if i % 2 == 0 else s * 0.22
        pts.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
      self.line.points = pts
    elif self.shape == "diamond":
      r = s * 0.42
      self.line.points = [cx, cy + r, cx + r*0.7, cy, cx, cy - r, cx - r*0.7, cy]
    elif self.shape == "rainbow":
      r = s * 0.42
      pts = []
      for i in range(25):
        a = 2 * math.pi * i / 24
        pts.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
      self.line.points = pts
      for i, e in enumerate(self.extras):
        a = 2 * math.pi * i / 8
        x1 = cx + r * 0.85 * math.cos(a); y1 = cy + r * 0.85 * math.sin(a)
        x2 = cx + r * 1.05 * math.cos(a); y2 = cy + r * 1.05 * math.sin(a)
        e.points = [x1, y1, x2, y2]
      self.extra_color.rgba = (1, 1, 1, 0.7)
    elif self.shape == "flame":
      pts = []
      r = s * 0.42
      for i in range(37):
        a = 2 * math.pi * i / 36
        rr = r + s * 0.05 * math.sin(a * 8)
        pts.extend([cx + rr * math.cos(a), cy + rr * math.sin(a)])
      self.line.points = pts
      for i, e in enumerate(self.extras):
        if i >= 6: break
        a = 2 * math.pi * i / 6
        x1 = cx + r * 0.9 * math.cos(a); y1 = cy + r * 0.9 * math.sin(a)
        x2 = cx + r * 1.1 * math.cos(a); y2 = cy + r * 1.1 * math.sin(a)
        e.points = [x1, y1, x2, y2]
      self.extra_color.rgba = (1, 1, 1, 0.5)
    elif self.shape == "legend":
      r = s * 0.42
      pts = []
      for i in range(37):
        a = 2 * math.pi * i / 36
        rr = r + s * 0.04 * math.sin(a * 6)
        pts.extend([cx + rr * math.cos(a), cy + rr * math.sin(a)])
      self.line.points = pts
      for i, e in enumerate(self.extras):
        a = 2 * math.pi * i / 8
        x1 = cx + r * 0.9 * math.cos(a); y1 = cy + r * 0.9 * math.sin(a)
        x2 = cx + r * 1.15 * math.cos(a); y2 = cy + r * 1.15 * math.sin(a)
        e.points = [x1, y1, x2, y2]
      self.extra_color.rgba = (1, 0.9, 0.3, 0.9)


# ============================================================
# КНОПКИ
# ============================================================
class GlassButton(Button):
  """Cosmic liquid-glass button with violet-blue rim and soft inner glow."""
  radius = NumericProperty(dp(22))
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.background_normal = ''; self.background_down = ''
    self.background_color = (0, 0, 0, 0); self.color = (0.96, 0.97, 1.0, 1)
    self.font_size = dp(16); self.size_hint_y = None; self.height = dp(54)
    with self.canvas.before:
      self.fill_color = Color(0.12, 0.15, 0.30, 0.68)
      self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
      self.glow_color = Color(0.46, 0.42, 1.0, 0.22)
      self.glow = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius), width=dp(0.8))
      self.edge_color = Color(0.67, 0.65, 1.0, 0.62)
      self.outline = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius), width=dp(0.7))
      self.glint_color = Color(0.86, 0.91, 1.0, 0.18)
      self.glint = Line(points=[self.x + dp(22), self.y + self.height - dp(3), self.x + self.width - dp(22), self.y + self.height - dp(3)], width=dp(0.5))
    self.bind(pos=self.update_rect, size=self.update_rect, state=self.update_state)

  def update_rect(self, *args):
    self.rect.pos = self.pos; self.rect.size = self.size; self.rect.radius = [self.radius]
    self.outline.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius)
    self.glow.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius)
    self.glint.points = [self.x + dp(22), self.y + self.height - dp(3), self.x + self.width - dp(22), self.y + self.height - dp(3)]

  def update_state(self, *args):
    if self.state == 'down':
      self.fill_color.rgba = (0.24, 0.22, 0.48, 0.86)
      self.edge_color.rgba = (0.35, 0.88, 1.0, 0.78)
      self.glow_color.rgba = (0.28, 0.72, 1.0, 0.16)
    else:
      self.fill_color.rgba = (0.12, 0.15, 0.30, 0.68)
      self.edge_color.rgba = (0.67, 0.65, 1.0, 0.62)
      self.glow_color.rgba = (0.46, 0.42, 1.0, 0.08)# ============================================================
# ЗОЛОТОЙ КУБОК ДЛЯ РАНГА PRO
# ============================================================
class TrophyIcon(Widget):
  """Small canvas-drawn gold trophy, independent of emoji fonts."""
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    with self.canvas:
      Color(0.25, 0.12, 0.01, 0.85)
      self.shadow = Ellipse(pos=(-5000, -5000), size=(0, 0))
      Color(1.0, 0.62, 0.03, 1)
      self.cup = Triangle(points=[])
      self.left_handle = Line(points=[], width=dp(3), cap='round')
      self.right_handle = Line(points=[], width=dp(3), cap='round')
      self.stem = Line(points=[], width=dp(4), cap='round')
      self.base = Line(points=[], width=dp(5), cap='round')
      Color(1.0, 0.88, 0.25, 1)
      self.highlight = Line(points=[], width=dp(2), cap='round')
    self.bind(pos=self.redraw, size=self.redraw)
    Clock.schedule_once(lambda dt: self.redraw(), 0.05)
  def redraw(self, *args):
    x, y, w, h = self.x, self.y, self.width, self.height
    if w < 2 or h < 2: return
    cx = x + w * 0.5
    self.shadow.pos = (x+w*0.18, y+h*0.02); self.shadow.size = (w*0.64, h*0.15)
    self.cup.points = [x+w*.25, y+h*.82, x+w*.75, y+h*.82, x+w*.64, y+h*.40, x+w*.36, y+h*.40]
    self.left_handle.points = [x+w*.28,y+h*.73, x+w*.13,y+h*.76, x+w*.12,y+h*.59, x+w*.34,y+h*.53]
    self.right_handle.points = [x+w*.72,y+h*.73, x+w*.87,y+h*.76, x+w*.88,y+h*.59, x+w*.66,y+h*.53]
    self.stem.points = [cx,y+h*.40,cx,y+h*.20]
    self.base.points = [x+w*.34,y+h*.17,x+w*.66,y+h*.17]
    self.highlight.points = [x+w*.34,y+h*.76,x+w*.42,y+h*.76,x+w*.48,y+h*.55]


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================
class MainMenuScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "particles_up")
    self.add_widget(self.bg_widget)

    data = load_data()
    coins = data.get("coins", 0)
    nick = data.get("nickname", "Игрок")
    mmr = data.get("mmr", 0)
    rank_idx = rank_index_by_mmr(mmr)

    outer = FloatLayout()
    # Центрируем весь блок главного меню по горизонтали и вертикали.
    # Высота рассчитана по сумме фиксированных высот элементов и промежутков.
    main = BoxLayout(orientation='vertical',
             size_hint=(0.92, None),
             height=dp(620),
             pos_hint={'center_x': 0.5, 'center_y': 0.5},
             spacing=dp(8))

    # Компактная шапка заполняет пустое место сверху и задаёт меню законченный вид.
    header = BoxLayout(orientation='vertical', size_hint_y=None,
               height=dp(72), spacing=dp(1), padding=(dp(4), dp(2)))
    header_title = Label(text="CataCase", font_size=dp(30), bold=True,
               color=(1, 1, 1, 1), halign='center', valign='middle',
               size_hint_y=None, height=dp(42))
    header_title.bind(size=lambda w, v: setattr(w, 'text_size', v))
    header_subtitle = Label(text="СОБИРАЙ  •  ПРОКАЧИВАЙСЯ  •  ПОБЕЖДАЙ",
               font_size=dp(9), bold=True, color=(0.78, 0.84, 0.94, 1),
               halign='center', valign='middle', size_hint_y=None, height=dp(18))
    header_subtitle.bind(size=lambda w, v: setattr(w, 'text_size', v))
    header.add_widget(header_title)
    header.add_widget(header_subtitle)
    main.add_widget(header)

    top_card = BoxLayout(orientation='horizontal', size_hint_y=None,
               height=dp(150), padding=dp(10), spacing=dp(8))
    with top_card.canvas.before:
      Color(0.10, 0.13, 0.28, 0.78)
      tc = RoundedRectangle(pos=top_card.pos, size=top_card.size, radius=[dp(24)])
      Color(0.62, 0.57, 1.0, 0.96)
      tc_edge = Line(rounded_rectangle=(top_card.x, top_card.y, top_card.width, top_card.height, dp(24)), width=dp(1.2))
      Color(0.40, 0.80, 1.0, 0.22)
      tc_glow = Line(rounded_rectangle=(top_card.x, top_card.y, top_card.width, top_card.height, dp(24)), width=dp(3))
    top_card.bind(pos=lambda w, v, r=tc: setattr(r, 'pos', v),
            size=lambda w, v, r=tc: setattr(r, 'size', v))
    top_card.bind(pos=lambda w, v, r=tc_edge: setattr(r, 'rounded_rectangle', (w.x, w.y, w.width, w.height, dp(24))),
            size=lambda w, v, r=tc_edge: setattr(r, 'rounded_rectangle', (w.x, w.y, w.width, w.height, dp(24))))
    top_card.bind(pos=lambda w, v, r=tc_glow: setattr(r, 'rounded_rectangle', (w.x, w.y, w.width, w.height, dp(24))),
            size=lambda w, v, r=tc_glow: setattr(r, 'rounded_rectangle', (w.x, w.y, w.width, w.height, dp(24))))

    # Аватарка игрока с выбранной рамкой; значок текущего ранга накладывается сверху.
    avatar_key = data.get("avatar", "cat_orange")
    frame_key = data.get("frame", "none")
    rank_holder = FloatLayout(size_hint_x=None, width=dp(150))

    frame_art = FrameArt(frame_key, dp(130))
    frame_art.pos_hint = {"center_x": 0.5, "center_y": 0.5}
    rank_holder.add_widget(frame_art)

    avatar_art = avatar_to_art(avatar_key, dp(70))
    if avatar_art is not None:
      avatar_art.size_hint = (None, None)
      avatar_art.size = (dp(70), dp(70))
      avatar_art.pos_hint = {"center_x": 0.5, "center_y": 0.5}
      rank_holder.add_widget(avatar_art)
    else:
      # Надёжный простой fallback, если выбранный ключ аватарки неизвестен.
      fallback = Label(text="?", font_size=dp(30), bold=True,
                       color=(1, 1, 1, 1), size_hint=(None, None),
                       size=(dp(70), dp(70)), pos_hint={"center_x": 0.5, "center_y": 0.5})
      rank_holder.add_widget(fallback)

    rank_badge_holder = FloatLayout(size_hint=(None, None), size=(dp(54), dp(54)),
                                    pos_hint={"center_x": 0.80, "center_y": 0.20})
    rank_badge = RankIcon(max(0, min(int(data.get("profile_rank", rank_idx)), len(RANKS) - 1)), dp(46))
    rank_badge.size_hint = (None, None)
    rank_badge.size = (dp(46), dp(46))
    rank_badge.pos_hint = {"center_x": 0.5, "center_y": 0.5}
    rank_badge_holder.add_widget(rank_badge)
    rank_holder.add_widget(rank_badge_holder)
    top_card.add_widget(rank_holder)

    # Имя и ранг находятся в верхней части карточки; MMR здесь не показываем,
    # чтобы надписи не пересекались с аватаркой и значком ранга.
    nick_box = BoxLayout(orientation='vertical', spacing=dp(2),
                         size_hint_y=None, height=dp(58),
                         pos_hint={'top': 0.91})
    nick_label = Label(text=nick, font_size=dp(17), bold=True,
                  color=(1, 1, 1, 1), size_hint_y=None, height=dp(28),
                  halign='center', valign='middle')
    nick_label.bind(size=lambda w, v: setattr(w, 'text_size', v))
    nick_box.add_widget(nick_label)
    rank_label = Label(text=RANKS[rank_idx][1], font_size=dp(12),
                  color=(0.85, 0.85, 0.9, 1), size_hint_y=None, height=dp(22),
                  halign='center', valign='middle')
    rank_label.bind(size=lambda w, v: setattr(w, 'text_size', v))
    nick_box.add_widget(rank_label)
    top_card.add_widget(nick_box)

    coins_box = BoxLayout(orientation='vertical', size_hint_x=None, width=dp(95),
                          size_hint_y=None, height=dp(52),
                          pos_hint={'top': 0.91})
    coins_box.add_widget(Label(text=str(coins), font_size=dp(20), bold=True,
                   color=(1, 0.85, 0.4, 1), size_hint_y=None, height=dp(28)))
    coins_box.add_widget(Label(text="монет", font_size=dp(10),
                   color=(0.85, 0.85, 0.9, 1), size_hint_y=None, height=dp(20)))
    top_card.add_widget(coins_box)
    main.add_widget(top_card)

    tap_btn = GlassButton(text="ТАПАТЬ", height=dp(80))
    tap_btn.font_size = dp(23)
    tap_btn.bold = True
    tap_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'clicker'))
    main.add_widget(tap_btn)

    # Все пункты меню используют один нейтральный Liquid Glass стиль.
    menu_items = [
      ("Кейсы", "cases"),
      ("Инвентарь", "inventory"),
      ("Ранги", "ranks"),
      ("Профиль", "profile"),
      ("Магазин", "shop"),
      ("Рейтинговый матч", "shooter"),
    ]
    grid = GridLayout(cols=2, spacing=dp(9), size_hint_y=None, height=dp(210))
    for label, target in menu_items:
      btn = GlassButton(text=label, height=dp(70))
      btn.font_size = dp(14)
      btn.bind(on_press=lambda _btn, t=target: setattr(self.manager, 'current', t))
      grid.add_widget(btn)
    main.add_widget(grid)

    # Быстрый доступ к отдельным инвентарям рамок и аватарок.
    cosmetics_inventory = BoxLayout(orientation='horizontal', spacing=dp(9),
                                    size_hint_y=None, height=dp(52))
    frames_inventory_btn = GlassButton(text='Инвентарь рамок', height=dp(52))
    frames_inventory_btn.font_size = dp(12)
    frames_inventory_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'frames_inventory'))
    avatars_inventory_btn = GlassButton(text='Инвентарь аватарок', height=dp(52))
    avatars_inventory_btn.font_size = dp(12)
    avatars_inventory_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'avatars_inventory'))
    cosmetics_inventory.add_widget(frames_inventory_btn)
    cosmetics_inventory.add_widget(avatars_inventory_btn)
    main.add_widget(cosmetics_inventory)

    outer.add_widget(main)
    self.add_widget(outer)

  def on_pre_enter(self, *args):
    self._build_ui()


# ============================================================
# КЛИКЕР
# ============================================================
THEME_LABELS = {
  "sun": "Солнце", "cat": "Кот", "spider": "Паук",
  "rainbow_cat": "Радужный кот", "knife": "Керамбит", "gun": "Пистолет",
  "eternal_flame": "Вечное пламя",
  "mushrooms": "Гриб", "minerals": "Минерал",
}


class ThemeTapWidget(FloatLayout):
  def __init__(self, theme="sun", size_d=dp(240), **kwargs):
    super().__init__(**kwargs)
    self.theme = theme
    self.base_size = size_d
    self.size_hint = (None, None); self.size = (size_d, size_d)
    self._event = None
    self.jumping = False
    self._sub_art = None
    with self.canvas:
      self.glow_color = Color(1, 0.85, 0.3, 0)
      self.glow = Ellipse(pos=(-5000, -5000), size=(0, 0))
    Clock.schedule_once(lambda dt: self._setup_subart(), 0.05)
    self.bind(pos=self.redraw, size=self.redraw)

  def _setup_subart(self):
    try:
      theme_map = {
        "cat": lambda: CatArt("orange", self.width * 0.75),
        "rainbow_cat": lambda: CatArt("rainbow_classic", self.width * 0.75),
        "spider": lambda: SpiderArt("purple", self.width * 0.75),
        "knife": lambda: KnifeArt("karambit_ruby", self.width * 0.75),
        "gun": lambda: GunArt("deagle", self.width * 0.75),
        "sun": lambda: SunArt(self.width * 0.75),
        "mushrooms": lambda: MushroomArt("glow", self.width * 0.75),
        "minerals": lambda: MineralArt("gold_mineral", self.width * 0.75),
        "eternal_flame": lambda: DetailedItemArt("eternal_flame", "fire", self.width * 0.75),
      }
      if self.theme in theme_map:
        self._sub_art = theme_map[self.theme]()
        self._sub_art.size_hint = (None, None)
        self._sub_art.size = (self.width * 0.75, self.width * 0.75)
        self._sub_art.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.add_widget(self._sub_art)
    except: pass

  def redraw(self, *args):
    s = self.width
    if s < 5: return
    cx = self.x + s / 2; cy = self.y + s / 2
    if self._sub_art is not None:
      self._sub_art.size = (s * 0.75, s * 0.75)
    glow_r = s * 0.48
    self.glow.pos = (cx - glow_r, cy - glow_r); self.glow.size = (glow_r * 2, glow_r * 2)
    theme_glow = {
      "sun": (1, 0.6, 0.1, 0.35), "cat": (1, 0.6, 0.3, 0.20),
      "mushrooms": (0.9, 0.25, 0.75, 0.3), "minerals": (1.0, 0.72, 0.08, 0.38),
      "rainbow_cat": (1, 0.4, 0.7, 0.25), "spider": (0.6, 0.3, 0.9, 0.25),
      "knife": (0.9, 0.2, 0.3, 0.22), "gun": (0.6, 0.7, 0.9, 0.22),
    }
    self.glow_color.rgba = theme_glow.get(self.theme, (1, 0.8, 0.5, 0.25))

  def pulse(self):
    if self.jumping: return
    self.jumping = True
    self._step = 0; self._total = 30
    self._event = Clock.schedule_interval(self._tick, 0.02)

  def _tick(self, dt):
    self._step += 1
    if self._step <= 8:
      p = self._step / 8.0; scale = 1.0 + 0.12 * p
    elif self._step <= 18:
      p = (self._step - 8) / 10.0; scale = 1.12 - 0.12 * p * p
    elif self._step <= 23:
      p = (self._step - 18) / 5.0; scale = 1.0 - 0.04 * p
    else:
      p = (self._step - 23) / 7.0; scale = 0.96 + 0.04 * p
    new_size = self.base_size * scale
    self.size = (new_size, new_size)
    if self._step >= self._total:
      self.size = (self.base_size, self.base_size)
      if self._event: self._event.cancel()
      self._event = None
      self.jumping = False


class ClickerScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    data = load_data()
    self.coins = data.get("coins", 0)
    self.theme = data.get("clicker_theme", "eternal_flame")
    self.tap_widget = None
    self._created = False
    self._bg_widget = None

    self._bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "particles_up")
    self.add_widget(self._bg_widget)

    self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
    self.coins_label = Label(text=f"Монеты: {self.coins}", font_size=dp(30),
                 size_hint_y=None, height=dp(50))
    self.layout.add_widget(self.coins_label)
    self.hint_label = Label(text=f"Тапай по: {THEME_LABELS[self.theme]}",
                font_size=dp(16), size_hint_y=None, height=dp(30))
    self.layout.add_widget(self.hint_label)
    self.tap_holder = FloatLayout(size_hint_y=None, height=dp(360))
    self.layout.add_widget(self.tap_holder)
    options_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                            height=dp(48), spacing=dp(10))
    btn_wallpapers = GlassButton(text="Обои", height=dp(48))
    btn_wallpapers.bind(on_press=lambda *_: setattr(self.manager, "current", "wallpaper"))
    btn_themes = GlassButton(text="Темы", height=dp(48))
    btn_themes.bind(on_press=lambda *_: setattr(self.manager, "current", "theme"))
    options_row.add_widget(btn_wallpapers)
    options_row.add_widget(btn_themes)
    self.layout.add_widget(options_row)
    btn_back = GlassButton(text="Назад в меню", height=dp(48))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    self.layout.add_widget(btn_back)
    self.add_widget(self.layout)
    Clock.schedule_once(self._try_create_tap_widget, 0.3)

  def _bg_theme_for(self, theme):
    if theme in ("rainbow_cat",): return "rainbow"
    if theme == "knife": return "knife"
    if theme == "gun": return "gun"
    return theme

  def _try_create_tap_widget(self, dt):
    if self._created: return
    if self.tap_holder.width < 50 or self.tap_holder.height < 50:
      Clock.schedule_once(self._try_create_tap_widget, 0.2); return
    self._created = True
    try:
      self.tap_widget = ThemeTapWidget(self.theme, dp(220))
      self.tap_widget.size_hint = (None, None)
      self.tap_widget.size = (dp(220), dp(220))
      self.tap_widget.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
      self.tap_widget.bind(on_touch_down=self._on_tap)
      self.tap_holder.add_widget(self.tap_widget)
    except: pass

  def _on_tap(self, widget, touch):
    if widget.collide_point(*touch.pos):
      data = load_data()
      boost = max(1, int(data.get("tap_boost", 1)))
      self.coins += boost
      self.coins_label.text = f"Монеты: {self.coins}"
      if self.tap_widget: self.tap_widget.pulse()
      data["coins"] = self.coins
      data["taps_total"] = data.get("taps_total", 0) + 1
      save_data(data)
      return True
    return False

  def update_coins(self):
    data = load_data()
    self.coins = data.get("coins", 0)
    self.coins_label.text = f"Монеты: {self.coins}"

  def on_pre_enter(self, *args):
    self.update_coins()
    data = load_data()
    wallpaper = data.get("wallpaper_theme", "fire")
    if self._bg_widget is not None and self._bg_widget.theme != wallpaper:
      try:
        self._bg_widget.stop_animation()
        self.remove_widget(self._bg_widget)
      except Exception:
        pass
      self._bg_widget = AnimatedBg(wallpaper, "particles_up")
      self.add_widget(self._bg_widget, index=len(self.children))
    new_theme = data.get("clicker_theme", "eternal_flame")
    if new_theme != self.theme:
      try:
        if self._bg_widget is not None:
          self._bg_widget.stop_animation()
          self.remove_widget(self._bg_widget)
          self._bg_widget = None
      except: pass
      try:
        if self.tap_widget is not None:
          self.tap_holder.remove_widget(self.tap_widget)
          self.tap_widget = None
      except: pass
      self.theme = new_theme
      self.hint_label.text = f"Тапай по: {THEME_LABELS[self.theme]}"
      self._bg_widget = AnimatedBg(data.get("wallpaper_theme", "fire"), "particles_up")
      self.add_widget(self._bg_widget, index=len(self.children))
      self._created = False
      Clock.schedule_once(self._try_create_tap_widget, 0.1)


# ============================================================
# ВЫБОР ТЕМЫ (ФИКС вылета)
# ============================================================
class ThemeSelectScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "particles_up")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
    layout.add_widget(Label(text="Выбор темы", font_size=dp(26), bold=True,
                size_hint_y=None, height=dp(45)))
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    inner = BoxLayout(orientation='vertical', spacing=dp(8),
              size_hint_y=None, padding=dp(2))
    inner.bind(minimum_height=inner.setter('height'))
    for theme in ["mushrooms", "minerals", "sun", "cat", "spider", "rainbow_cat", "knife", "gun"]:
      inner.add_widget(ThemeCardButton(theme))
    scroll.add_widget(inner)
    layout.add_widget(scroll)
    btn_back = GlassButton(text="Назад", height=dp(55))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'clicker'))
    layout.add_widget(btn_back)
    self.add_widget(layout)


class WallpaperSelectScreen(Screen):
  OPTIONS = [("sun", "Солнечные"), ("cat", "Кошачьи"), ("spider", "Паучьи"),
    ("rainbow", "Радужные"), ("knife", "Красно-рубиновая"), ("gun", "Стальные"),
    ("ice", "Ледяные"), ("fire", "Огненные"), ("cosmic", "Космические"),
    ("magic", "Магические"), ("fish", "Подводные"), ("plants", "Растения"),
    ("minerals", "Минералы"), ("mushrooms", "Грибы")]
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "particles_up"); self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8))
    layout.add_widget(Label(text="Анимированные обои", font_size=dp(24), bold=True,
                            size_hint_y=None, height=dp(44)))
    scroll = ScrollView(do_scroll_x=False)
    inner = BoxLayout(orientation="vertical", spacing=dp(7), size_hint_y=None, padding=dp(2))
    inner.bind(minimum_height=inner.setter("height"))
    for key, label in self.OPTIONS:
      btn = GlassButton(text=label, height=dp(48))
      btn.bind(on_press=lambda instance, k=key: self.choose(k)); inner.add_widget(btn)
    scroll.add_widget(inner); layout.add_widget(scroll)
    back = GlassButton(text="Назад в тапалку", height=dp(50))
    back.bind(on_press=lambda *_: setattr(self.manager, "current", "clicker")); layout.add_widget(back)
    self.add_widget(layout)
  def choose(self, key):
    data = load_data(); data["wallpaper_theme"] = key; save_data(data)
    self.manager.current = "clicker"


class ThemeCardButton(GlassButton):
  """Rounded liquid-glass theme card with centered title and subtitle."""
  def __init__(self, theme, **kwargs):
    super().__init__(**kwargs)
    self.theme = theme
    self.text = THEME_LABELS.get(theme, theme) + "\nНажми, чтобы выбрать"
    self.font_size = dp(18)
    self.bold = True
    self.halign = "center"
    self.valign = "middle"
    self.size_hint_y = None
    self.height = dp(82)
    self.padding = (dp(12), dp(8))
    self.radius = dp(18)
    self.bind(size=self._sync_text_size)
    self._sync_text_size()
    self.bind(on_press=self._select)

  def _sync_text_size(self, *args):
    self.text_size = (max(0, self.width - dp(24)), self.height - dp(12))

  def _select(self, *args):
    try:
      data = load_data()
      data['clicker_theme'] = self.theme
      wallpaper_for_theme = {
        'sun': 'sun', 'cat': 'cat', 'spider': 'spider',
        'rainbow_cat': 'rainbow', 'knife': 'knife', 'gun': 'gun',
        'mushrooms': 'mushrooms', 'minerals': 'minerals',
        'eternal_flame': 'fire',
      }
      data['wallpaper_theme'] = wallpaper_for_theme.get(self.theme, 'fire')
      save_data(data)
      # После выбора сразу возвращаемся во вкладку «Тапалка».
      parent = self.parent
      while parent is not None and not hasattr(parent, 'screens'):
        parent = getattr(parent, 'parent', None)
      if parent is not None:
        parent.current = 'clicker'
    except Exception as e:
      print('ОШИБКА выбора темы:', e)


# ============================================================
# КЕЙСЫ
# ============================================================
CASE_ACCENTS = {
  "cats": (1, 0.65, 0.30, 0.55), "planets": (0.45, 0.65, 1.0, 0.55),
  "knives": (0.9, 0.25, 0.30, 0.60), "spiders": (0.75, 0.35, 1.0, 0.60),
  "rainbow": (1.0, 0.4, 0.7, 0.65), "guns": (0.6, 0.65, 0.7, 0.60),
  "ice": (0.4, 0.8, 1.0, 0.60), "fire": (1.0, 0.4, 0.1, 0.60),
  "cosmic": (0.6, 0.3, 0.9, 0.60), "magic": (0.8, 0.4, 1.0, 0.60),
  "fish": (0.3, 0.7, 1.0, 0.60), "plants": (0.3, 0.9, 0.4, 0.60),
  "fur": (0.9, 0.6, 0.2, 0.60), "minerals": (0.8, 0.8, 0.9, 0.60),
  "mushrooms": (0.95, 0.5, 0.8, 0.60),
}
CASE_BTN_COLORS = {
  "cats": (1, 0.55, 0.20, 0.90), "planets": (0.30, 0.50, 0.95, 0.90),
  "knives": (0.85, 0.20, 0.30, 0.92), "spiders": (0.65, 0.25, 0.95, 0.92),
  "rainbow": (0.95, 0.35, 0.75, 0.92), "guns": (0.4, 0.45, 0.5, 0.92),
  "ice": (0.3, 0.7, 0.9, 0.92), "fire": (0.9, 0.35, 0.1, 0.92),
  "cosmic": (0.55, 0.25, 0.85, 0.92), "magic": (0.7, 0.35, 0.95, 0.92),
  "fish": (0.3, 0.65, 0.9, 0.92), "plants": (0.3, 0.75, 0.4, 0.92),
  "fur": (0.85, 0.55, 0.15, 0.92), "minerals": (0.7, 0.7, 0.8, 0.92),
  "mushrooms": (0.9, 0.4, 0.7, 0.92),
}


class CaseMiniCard(BoxLayout):
  """ФИКС: фиксированный размер, pos_hint не конфликтует."""
  def __init__(self, case_id, on_open, **kwargs):
    super().__init__(**kwargs)
    self.orientation = 'vertical'
    self.size_hint_y = None
    self.height = dp(220)
    self.padding = dp(6)
    self.spacing = dp(3)
    self.case_id = case_id
    self.on_open = on_open
    info = CASE_INFO[case_id]
    accent = CASE_ACCENTS[case_id]
    btn_rgba = CASE_BTN_COLORS[case_id]

    with self.canvas.before:
      Color(1, 1, 1, 0.06)
      self.card_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
      Color(*accent)
      self.accent = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
    self.bind(pos=self._update_bg, size=self._update_bg)

    title_lbl = Label(text=info["label"], font_size=dp(13), bold=True,
              size_hint_y=None, height=dp(38),
              color=(1, 1, 1, 1), halign='center', valign='middle')
    title_lbl.bind(size=lambda s, v: setattr(s, 'text_size', (v[0], None)))
    self.add_widget(title_lbl)

    # ФИКС: ChestArt с фиксированным size_hint=(None,None) и полной высотой
    chest_holder = FloatLayout(size_hint_y=None, height=dp(100))
    chest = ChestArt(case_id, dp(95))
    chest_holder.add_widget(chest)
    def _place_chest(*args):
      if chest_holder.width < 5: return
      chest.pos = (chest_holder.x + (chest_holder.width - chest.width) / 2,
             chest_holder.y + (chest_holder.height - chest.height) / 2)
    chest_holder.bind(pos=_place_chest, size=_place_chest)
    self.add_widget(chest_holder)
    Clock.schedule_once(lambda dt: _place_chest(), 0.1)
    Clock.schedule_once(lambda dt: _place_chest(), 0.25)

    buy_btn = Button(text="Купить", font_size=dp(14), bold=True,
             size_hint_y=None, height=dp(40),
             background_normal='', background_down='',
             background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
    with buy_btn.canvas.before:
      Color(*btn_rgba)
      buy_btn._bg = RoundedRectangle(pos=buy_btn.pos, size=buy_btn.size, radius=[dp(18)])
    buy_btn.bind(pos=lambda w, v: setattr(w._bg, 'pos', v),
            size=lambda w, v: setattr(w._bg, 'size', v))
    buy_btn.bind(on_press=lambda x: self.on_open(self.case_id))
    self.add_widget(buy_btn)

  def _update_bg(self, *args):
    self.card_bg.pos = self.pos; self.card_bg.size = self.size
    self.accent.pos = (self.x, self.top - dp(5)); self.accent.size = (self.width, dp(10))


class CasesScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "corners")
    self.add_widget(self.bg_widget)
    root = BoxLayout(orientation='vertical')
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True, bar_width=dp(4))
    content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10), size_hint_y=None)
    content.bind(minimum_height=content.setter('height'))
    content.add_widget(Label(text="Кейсы", font_size=dp(28), bold=True,
                 size_hint_y=None, height=dp(45)))
    self.coins_label = Label(text="", font_size=dp(16), size_hint_y=None, height=dp(28))
    content.add_widget(self.coins_label)
    grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
    grid.bind(minimum_height=grid.setter('height'))
    for case_id in ["cats", "planets", "knives", "spiders", "rainbow", "guns",
             "ice", "fire", "cosmic", "magic",
             "fish", "plants", "fur", "minerals", "mushrooms"]:
      grid.add_widget(CaseMiniCard(case_id, on_open=self._open_case))
    content.add_widget(grid)
    content.add_widget(Label(text="", size_hint_y=None, height=dp(5)))
    btn_back = GlassButton(text="Назад", height=dp(55))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    content.add_widget(btn_back)
    scroll.add_widget(content)
    root.add_widget(scroll)
    self.add_widget(root)

  def _open_case(self, case_id):
    box_screen = self.manager.get_screen('box')
    box_screen.setup_case(case_id)
    self.manager.current = 'box'

  def on_pre_enter(self, *args):
    data = load_data()
    self.coins_label.text = f"Монеты: {data.get('coins', 0)}"


class CaseOpenPopup(FloatLayout):
  def __init__(self, case_id, on_close, on_buy, **kwargs):
    super().__init__(**kwargs)
    self.case_id = case_id; self.on_close = on_close; self.on_buy = on_buy
    with self.canvas.before:
      self.dim_color = Color(0, 0, 0, 0.85)
      self.dim = Rectangle(pos=self.pos, size=self.size)
    self.bind(pos=self._update_dim, size=self._update_dim)
    panel_w = min(Window.width * 0.9, dp(360))
    panel_h = dp(460)
    with self.canvas:
      Color(0.15, 0.15, 0.2, 0.98)
      self.panel = RoundedRectangle(
        pos=(Window.width / 2 - panel_w / 2, Window.height / 2 - panel_h / 2),
        size=(panel_w, panel_h), radius=[dp(30)])
    info = CASE_INFO[case_id]
    title = Label(text=info["label"], font_size=dp(20), bold=True,
            size_hint=(None, None), size=(panel_w, dp(36)),
            pos=(Window.width / 2 - panel_w / 2,
              Window.height / 2 + panel_h / 2 - dp(46)),
            color=(1, 1, 1, 1))
    self.add_widget(title)
    sub = Label(text="Сколько прокрутов купить?", font_size=dp(14),
           size_hint=(None, None), size=(panel_w, dp(24)),
           pos=(Window.width / 2 - panel_w / 2,
             Window.height / 2 + panel_h / 2 - dp(80)),
           color=(0.85, 0.85, 0.9, 1))
    self.add_widget(sub)
    costs = case_prices(case_id)
    options = [(1, costs[0]), (5, costs[1]), (10, costs[2])]
    start_y = Window.height / 2 + panel_h / 2 - dp(140)
    for i, (count, cost) in enumerate(options):
      txt = f"{count} прокрут{'ов' if count > 1 else ''} — {cost} монет"
      btn = Button(text=txt, font_size=dp(16),
             size_hint=(None, None),
             size=(panel_w - dp(60), dp(60)),
             pos=(Window.width / 2 - (panel_w - dp(60)) / 2,
                start_y - i * dp(75)),
             background_normal='', background_down='',
             background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
      with btn.canvas.before:
        Color(*CASE_BTN_COLORS[case_id])
        btn._bg = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(20)])
      btn.bind(pos=lambda w, v: setattr(w._bg, 'pos', v),
           size=lambda w, v: setattr(w._bg, 'size', v))
      btn.bind(on_press=lambda x, c=count, co=cost: self._pick(c, co))
      self.add_widget(btn)
    cancel = GlassButton(text="Отмена")
    cancel.size_hint = (None, None)
    cancel.size = (panel_w - dp(60), dp(50))
    cancel.pos = (Window.width / 2 - (panel_w - dp(60)) / 2,
            Window.height / 2 - panel_h / 2 + dp(20))
    cancel.bind(on_press=self._close)
    self.add_widget(cancel)

  def _pick(self, count, cost):
    self.on_buy(count, cost); self._close()

  def _update_dim(self, *args):
    self.dim.pos = self.pos; self.dim.size = self.size

  def _close(self, *args):
    if self.on_close: self.on_close()


class LightBurst(FloatLayout):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    with self.canvas:
      self.color = Color(1, 0.85, 0.3, 0)
      self.circle = Ellipse(pos=(0, 0), size=(0, 0))
    self._step = 0; self._total = 50
    Clock.schedule_once(self._upd_pos, 0.01)
    Clock.schedule_interval(self._tick, 0.02)

  def _upd_pos(self, dt):
    W = Window.width; H = Window.height
    self.circle.pos = (W/2 - 5, H/2 - 5); self.circle.size = (10, 10)

  def _tick(self, dt):
    self._step += 1
    W = Window.width; H = Window.height
    progress = self._step / self._total
    max_r = max(W, H) * 1.2
    r = max_r * (1 - (1 - progress) ** 3)
    if progress < 0.4: self.color.a = 0.9
    else: self.color.a = 0.9 * (1 - (progress - 0.4) / 0.6)
    self.circle.pos = (W/2 - r, H/2 - r); self.circle.size = (r * 2, r * 2)
    if self._step >= self._total:
      try: self.parent.remove_widget(self)
      except: pass


class CaseScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.case_id = "cats"
    self.spinning = False
    self.popup = None; self.buy_popup = None
    self._bg_widget = None
    self._build_ui()

  def _bg_theme_for_case(self, cid):
    return {
      "cats": ("cat", "particles_up"), "planets": ("sun", "waves"),
      "knives": ("knife", "corners"), "spiders": ("spider", "spiral"),
      "rainbow": ("rainbow", "particles_up"), "guns": ("gun", "corners"),
      "ice": ("ice", "particles_up"), "fire": ("fire", "waves"),
      "cosmic": ("cosmic", "spiral"), "magic": ("magic", "corners"),
      "fish": ("fish", "waves"), "plants": ("plants", "particles_up"),
      "fur": ("fur", "corners"), "minerals": ("minerals", "spiral"),
      "mushrooms": ("mushrooms", "particles_up"),
    }.get(cid, ("sun", "particles_up"))

  def setup_case(self, case_id):
    self.case_id = case_id
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    theme, style = self._bg_theme_for_case(self.case_id)
    self._bg_widget = AnimatedBg(theme, style)
    self.add_widget(self._bg_widget)
    root = BoxLayout(orientation='vertical')
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True, bar_width=dp(4))
    content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8), size_hint_y=None)
    content.bind(minimum_height=content.setter('height'))
    info = CASE_INFO[self.case_id]
    content.add_widget(Label(text=info["label"], font_size=dp(22), bold=True,
                 size_hint_y=None, height=dp(40)))
    self.coins_label = Label(text="", font_size=dp(18), size_hint_y=None, height=dp(30))
    content.add_widget(self.coins_label)
    self.roulette = RouletteWidget(roulette_type=info["roulette"],
                    size_hint_y=None, height=dp(170))
    content.add_widget(self.roulette)
    self.result_label = Label(text="Нажми «Купить», чтобы крутить",
                  font_size=dp(14), size_hint_y=None, height=dp(40),
                  halign='center', valign='middle')
    self.result_label.bind(size=lambda s, v: setattr(s, 'text_size', (v[0], None)))
    content.add_widget(self.result_label)
    buy_btn = Button(text="Купить", font_size=dp(20), bold=True,
             size_hint_y=None, height=dp(60),
             background_normal='', background_down='',
             background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
    with buy_btn.canvas.before:
      Color(*CASE_BTN_COLORS[self.case_id])
      buy_btn._bg = RoundedRectangle(pos=buy_btn.pos, size=buy_btn.size, radius=[dp(28)])
    buy_btn.bind(pos=lambda w, v: setattr(w._bg, 'pos', v),
            size=lambda w, v: setattr(w._bg, 'size', v))
    buy_btn.bind(on_press=self._show_buy_popup)
    content.add_widget(buy_btn)
    content.add_widget(Label(text="Возможные награды", font_size=dp(18), bold=True,
                 size_hint_y=None, height=dp(36)))
    prize_pool, weights = case_prizes(self.case_id)
    item_type = info["item_type"]
    grid = GridLayout(cols=4, spacing=dp(8), padding=dp(4), size_hint_y=None)
    grid.bind(minimum_height=grid.setter('height'))
    for kind in prize_pool:
      grid.add_widget(PrizeCard(item_type, kind))
    content.add_widget(grid)
    content.add_widget(Label(text="", size_hint_y=None, height=dp(5)))
    btn_back = GlassButton(text="Назад", height=dp(55))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'cases'))
    content.add_widget(btn_back)
    scroll.add_widget(content)
    root.add_widget(scroll)
    self.add_widget(root)

  def on_pre_enter(self, *args):
    data = load_data()
    self.coins_label.text = f"Монеты: {data.get('coins', 0)}"
    if hasattr(self, 'roulette'): self.roulette.clear_all()
    self.result_label.text = "Нажми «Купить», чтобы крутить"
    self.spinning = False
    if self.popup:
      self.remove_widget(self.popup); self.popup = None
    if self.buy_popup:
      self.remove_widget(self.buy_popup); self.buy_popup = None

  def _show_buy_popup(self, *args):
    if self.spinning: return
    try:
      p = CaseOpenPopup(self.case_id, on_close=self._close_buy_popup, on_buy=self._do_spin)
      self.add_widget(p)
      self.buy_popup = p
    except: pass

  def _close_buy_popup(self):
    try:
      if self.buy_popup:
        self.remove_widget(self.buy_popup); self.buy_popup = None
    except: pass

  def _do_spin(self, count, cost):
    if self.spinning: return
    data = load_data()
    coins = data.get("coins", 0)
    if coins < cost:
      self.result_label.text = f"Не хватает! Нужно {cost}, есть {coins}"
      return
    coins -= cost
    data["coins"] = coins
    info = CASE_INFO[self.case_id]
    item_type = info["item_type"]
    prize_pool, weights = case_prizes(self.case_id)
    self.spinning = True
    results = [random.choices(prize_pool, weights=weights)[0] for _ in range(count)]
    inventory = data.get("inventory", [])
    for r in results:
      inventory.append({"type": item_type, "kind": r, "case": self.case_id})
    data["inventory"] = inventory
    data["cases_opened"] = data.get("cases_opened", 0) + count
    has_legendary = any(r in LEGENDARY_KINDS for r in results)
    bonus_map = {
      "cats": {"gold": 500}, "planets": {"sun": 1000},
      "knives": {"karambit_talisman": 3000, "karambit_black_pearl": 2500, "karambit_emerald": 2000},
      "spiders": {"galaxy": 5000, "toxic": 3000, "shadow": 2000, "rainbow": 1500},
      "rainbow": {"rainbow_neon": 2000, "rainbow_lava": 1000, "rainbow_ice": 500},
      "guns": {"neon_rider": 4000, "printstream": 3000, "dragon_lore": 2000},
      "ice": {"cosmic_ice": 6000, "eternal_ice": 4000, "absolute_zero": 2500},
      "fire": {"eternal_flame": 6000, "solar_flare": 4000, "dragon_fire": 2500},
      "cosmic": {"multiverse": 8000, "big_bang": 5000, "dark_matter": 3000},
      "magic": {"philosopher_stone": 8000, "arcane_ring": 5000, "crystal_ball": 3000},
      "fish": {"arctic_char": 6000, "discus": 4000, "arowana": 2500},
      "plants": {"eternal_bloom": 6000, "crystal_flower": 4000, "blue_bell": 2500},
      "fur": {"golden_panther": 6000, "polar_bear": 4000, "panda": 2500},
      "minerals": {"meteorite": 6000, "adamantite": 4000, "orichalcum": 2500},
      "mushrooms": {"glow": 6000, "cyan": 4000, "pink": 2500},
    }
    for kind, bonus in bonus_map.get(self.case_id, {}).items():
      cnt = results.count(kind)
      if cnt > 0:
        data["coins"] = data["coins"] + bonus * cnt
    save_data(data)
    self.coins_label.text = f"Монеты: {data['coins']}"
    if has_legendary:
      try:
        burst = LightBurst()
        self.add_widget(burst)
      except: pass
    if count == 1:
      self.result_label.text = "Крутим..."
      self._final = results[0]
      seq = [random.choice(prize_pool) for _ in range(14)]
      seq.append(self._final)
      def on_finish():
        self.result_label.text = f"Выпало: {get_name(item_type, self._final)}"
        self.spinning = False
        popup = PopupResult([self._final], item_type, on_close=self._close_popup,
                            on_sell=self._sell_results, on_spin_again=self._spin_again)
        self.add_widget(popup)
        self.popup = popup
      self.roulette.start_spin(seq, on_finish)
    else:
      try:
        popup = PopupResult(results, item_type, on_close=self._close_popup,
                            on_sell=self._sell_results, on_spin_again=self._spin_again)
        self.add_widget(popup)
        self.popup = popup
      except: pass
      self.result_label.text = f"Выпало {count} предметов"
      self.spinning = False

  def _sell_results(self, results, item_type):
    data = load_data()
    inventory = data.get("inventory", [])
    total = 0
    # Удаляем ровно те предметы, которые показаны в текущем окне, включая дубликаты.
    for kind in results:
      for i, item in enumerate(inventory):
        if item.get("type") == item_type and item.get("kind") == kind:
          inventory.pop(i)
          total += get_price(item_type, kind)
          data["items_sold"] = data.get("items_sold", 0) + 1
          break
    data["inventory"] = inventory
    data["coins"] = data.get("coins", 0) + total
    save_data(data)
    self.coins_label.text = f"Монеты: {data['coins']}"
    self.result_label.text = f"Продано предметов на {total} монет"

  def _spin_again(self):
    self.spinning = False
    self._show_buy_popup()

  def _close_popup(self):
    try:
      if self.popup:
        self.remove_widget(self.popup); self.popup = None
    except: pass


class PrizeCard(BoxLayout):
  def __init__(self, item_type, kind, **kwargs):
    super().__init__(**kwargs)
    self.orientation = 'vertical'
    self.size_hint_y = None; self.height = dp(120)
    self.padding = dp(4); self.spacing = dp(2)
    with self.canvas.before:
      Color(1, 1, 1, 0.08)
      self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
    self.bind(pos=self._update_bg, size=self._update_bg)
    art_holder = FloatLayout(size_hint_y=None, height=dp(70))
    art = make_art(item_type, kind, dp(60))
    if art is not None:
      art.size_hint = (None, None); art.size = (dp(60), dp(60))
      art.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
      art_holder.add_widget(art)
    self.add_widget(art_holder)
    name = get_name(item_type, kind); price = get_price(item_type, kind)
    lbl = Label(text=f"{name}\n{price}", font_size=dp(9),
           size_hint_y=None, height=dp(38),
           color=(1, 1, 1, 1), halign='center', valign='middle')
    lbl.bind(size=lambda s, v: setattr(s, 'text_size', (v[0], None)))
    self.add_widget(lbl)

  def _update_bg(self, *args):
    self.bg.pos = self.pos; self.bg.size = self.size


class RouletteWidget(FloatLayout):
  """Общая рулетка для всех типов кейсов: использует реальные арт-виджеты
  предметов и обрезает их строго по границам панели через StencilView."""
  ROULETTE_ITEM_TYPES = {
    "cats": "cat", "planets": "planet", "knives": "knives",
    "spiders": "spiders", "rainbow": "rainbow", "guns": "guns",
    "ice": "ice", "fire": "fire", "cosmic": "cosmic", "magic": "magic",
    "fish": "fish", "plants": "plants", "fur": "fur",
    "minerals": "minerals", "mushrooms": "mushrooms",
  }

  def __init__(self, roulette_type="cats", **kwargs):
    super().__init__(**kwargs)
    self.roulette_type = roulette_type
    self.items = []
    self._event = None
    self.spinning = False
    self._on_finish = None
    self._step = 0
    self._total = 1
    self._offset = 0
    self._end_offset = 0
    self._spacing = dp(96)
    self._item_size = dp(62)
    with self.canvas.before:
      Color(1, 1, 1, 0.055)
      self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
    # Дочерние изображения обрезаются по прямоугольнику рулетки.
    self.viewport = StencilView(size_hint=(1, 1), pos=self.pos)
    self.add_widget(self.viewport)
    with self.canvas.after:
      self.line2_color = Color(0.82, 0.78, 0.92, 0.55)
      self.line2 = Line(points=[], width=dp(13), cap='round')
      self.line_color = Color(1.0, 0.98, 1.0, 0.95)
      self.line = Line(points=[], width=dp(4), cap='round')
    self.bind(pos=self._update_graphics, size=self._update_graphics)
    Clock.schedule_once(lambda dt: self._update_graphics(), 0.1)

  def _update_graphics(self, *args):
    self.bg.pos = self.pos
    self.bg.size = self.size
    self.viewport.pos = self.pos
    self.viewport.size = self.size
    cx = self.x + self.width / 2
    self.line2.points = [cx, self.y + dp(10), cx, self.y + self.height - dp(10)]
    self.line.points = [cx, self.y + dp(10), cx, self.y + self.height - dp(10)]
    if self.items:
      self._redraw_all()

  def _art_item_type(self):
    return self.ROULETTE_ITEM_TYPES.get(self.roulette_type, "mushrooms")

  def start_spin(self, sequence, on_finish):
    if self.spinning:
      return
    if not sequence:
      if on_finish:
        on_finish()
      return
    if self.width < dp(40) or self.height < dp(40):
      Clock.schedule_once(lambda dt: self.start_spin(sequence, on_finish), 0.1)
      return

    self.spinning = True
    self._on_finish = on_finish
    self.clear_all()
    # Меньше сложных Canvas-виджетов одновременно — заметно легче для Android.
    self._item_size = min(dp(64), self.height * 0.42)
    self._spacing = max(self._item_size + dp(18), dp(82))

    # Короткий хвост после выигрышного предмета: меньше текстурных виджетов.
    display_sequence = list(sequence) + [random.choice(sequence) for _ in range(3)]
    item_type = self._art_item_type()
    for kind in display_sequence:
      try:
        art = make_art(item_type, kind, self._item_size)
        if art is None:
          continue
        art.size_hint = (None, None)
        art.size = (self._item_size, self._item_size)
        self.viewport.add_widget(art)
        self.items.append(art)
      except Exception:
        # Пропускаем повреждённую текстуру, не ломая вращение всей рулетки.
        continue

    if not self.items:
      self.spinning = False
      if on_finish:
        on_finish()
      return

    self._start_x = self.x + self.width + self._item_size
    final_i = min(len(sequence) - 1, len(self.items) - 1)
    final_center_x = self.x + self.width / 2
    final_start_x = self._start_x + final_i * self._spacing
    self._end_offset = final_center_x - final_start_x
    self._offset = 0
    self._redraw_all()
    self._step = 0
    self._total = 78 # ~2.6 sec at 30 FPS; меньше обновлений Canvas на телефоне.
    self._event = Clock.schedule_interval(self._tick, 1.0 / 120.0)

  def _redraw_all(self):
    if not self.items:
      return
    center_y = self.y + self.height / 2
    for i, item in enumerate(self.items):
      cx = self._start_x + i * self._spacing + self._offset
      item.pos = (cx - item.width / 2, center_y - item.height / 2)

  def _tick(self, dt):
    self._step += 1
    progress = min(1.0, self._step / max(1, self._total))
    ease = 1 - (1 - progress) ** 5
    self._offset = self._end_offset * ease
    self._redraw_all()
    if self._step >= self._total:
      if self._event:
        self._event.cancel()
      self._event = None
      self.spinning = False
      callback = self._on_finish
      self._on_finish = None
      if callback:
        callback()

  def clear_all(self):
    if self._event:
      self._event.cancel()
      self._event = None
    for item in list(self.items):
      try:
        self.viewport.remove_widget(item)
      except Exception:
        pass
    self.items = []
    self.spinning = False


class PopupResult(FloatLayout):
  """Окно результата: предметы, продажа выпавшего и повторное открытие."""
  def __init__(self, results, item_type, on_close, on_sell=None, on_spin_again=None, **kwargs):
    super().__init__(**kwargs)
    self.on_close = on_close
    self.on_sell = on_sell
    self.on_spin_again = on_spin_again
    self.results = list(results)
    self.item_type = item_type
    with self.canvas.before:
      self.dim_color = Color(0, 0, 0, 0.86)
      self.dim = Rectangle(pos=self.pos, size=self.size)
    self.bind(pos=self._update_dim, size=self._update_dim)
    panel_w = min(Window.width * 0.92, dp(420))
    panel_h = min(Window.height * 0.82, dp(500))
    px = Window.width / 2 - panel_w / 2
    py = Window.height / 2 - panel_h / 2
    with self.canvas:
      Color(0.10, 0.12, 0.18, 0.98)
      self.panel = RoundedRectangle(pos=(px, py), size=(panel_w, panel_h), radius=[dp(28)])
    title_text = (f"Выпало: {get_name(item_type, results[0])}" if len(results) == 1
                  else f"Ты получил {len(results)} предметов!")
    title = Label(text=title_text, font_size=dp(18 if len(results) == 1 else 20), bold=True,
        size_hint=(None, None), size=(panel_w-dp(24), dp(52)),
        pos=(px+dp(12), py+panel_h-dp(65)), halign='center', valign='middle',
        color=(1, 1, 1, 1))
    title.bind(size=lambda w, v: setattr(w, 'text_size', v))
    self.add_widget(title)
    if len(results) == 1:
      try:
        art = make_art(item_type, results[0], min(dp(150), panel_w*0.42))
        if art is not None:
          art.size = (min(dp(150), panel_w*0.42), min(dp(150), panel_w*0.42))
          art.pos = (Window.width/2-art.width/2, py+panel_h*0.43-art.height/2)
          self.add_widget(art)
      except Exception:
        pass
    else:
      Clock.schedule_once(lambda dt: self._place_items(panel_w, panel_h), 0.05)
    btn_w = (panel_w-dp(54))/2
    btn_h = dp(56)
    btn_y = py+dp(20)
    sell_text = "Продать" if len(results) == 1 else "Продать всех"
    sell_btn = Button(text=sell_text, font_size=dp(16), bold=True,
        size_hint=(None,None), size=(btn_w,btn_h), pos=(px+dp(18),btn_y),
        background_normal='', background_down='', background_color=(0,0,0,0), color=(1,1,1,1))
    with sell_btn.canvas.before:
      Color(0.72, 0.20, 0.22, 1)
      sell_btn._bg = RoundedRectangle(pos=sell_btn.pos,size=sell_btn.size,radius=[dp(18)])
    sell_btn.bind(pos=lambda w,v:setattr(w._bg,'pos',v), size=lambda w,v:setattr(w._bg,'size',v))
    sell_btn.bind(on_press=self._sell)
    self.add_widget(sell_btn)
    again_btn = Button(text="Крутить дальше", font_size=dp(15), bold=True,
        size_hint=(None,None), size=(btn_w,btn_h), pos=(px+dp(36)+btn_w,btn_y),
        background_normal='', background_down='', background_color=(0,0,0,0), color=(1,1,1,1))
    with again_btn.canvas.before:
      Color(0.12, 0.48, 0.32, 1)
      again_btn._bg = RoundedRectangle(pos=again_btn.pos,size=again_btn.size,radius=[dp(18)])
    again_btn.bind(pos=lambda w,v:setattr(w._bg,'pos',v), size=lambda w,v:setattr(w._bg,'size',v))
    again_btn.bind(on_press=self._again)
    self.add_widget(again_btn)

  def _place_items(self, panel_w, panel_h):
    cols = 5; item_size = dp(48); pad = dp(6)
    grid_w = cols*item_size+(cols-1)*pad
    rows = (len(self.results)+cols-1)//cols
    grid_h = rows*item_size+(rows-1)*pad
    start_x = Window.width/2-grid_w/2
    start_y = Window.height/2+panel_h*0.25-grid_h/2
    for i, kind in enumerate(self.results):
      col=i%cols; row=i//cols
      try:
        art=make_art(self.item_type,kind,item_size)
        if art is not None:
          art.size=(item_size,item_size)
          art.pos=(start_x+col*(item_size+pad),start_y-row*(item_size+pad))
          self.add_widget(art)
      except Exception:
        pass

  def _update_dim(self, *args):
    self.dim.pos=self.pos; self.dim.size=self.size

  def _sell(self, *args):
    if self.on_sell: self.on_sell(self.results, self.item_type)
    if self.on_close: self.on_close()

  def _again(self, *args):
    if self.on_close: self.on_close()
    if self.on_spin_again: self.on_spin_again()


# ============================================================
# ИНВЕНТАРЬ
# ============================================================
class InventoryCard(BoxLayout):
  def __init__(self, item_type, kind, case_id=None, on_sell=None, **kwargs):
    super().__init__(**kwargs)
    self.orientation = 'vertical'
    self.size_hint_y = None; self.height = dp(210)
    self.padding = dp(8); self.spacing = dp(4)
    self.item_type = item_type; self.kind = kind
    self.case_id = case_id; self.on_sell = on_sell
    with self.canvas.before:
      Color(1, 1, 1, 0.10)
      self.card_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
    self.bind(pos=self._update_bg, size=self._update_bg)
    art_holder = FloatLayout(size_hint_y=None, height=dp(92))
    art = make_art(item_type, kind, dp(82))
    if art is not None:
      art.size_hint = (None, None); art.size = (dp(82), dp(82))
      art.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
      art_holder.add_widget(art)
    self.add_widget(art_holder)
    name = get_name(item_type, kind); price = get_price(item_type, kind)
    label = Label(text=f"{name}\n{price}м", font_size=dp(12),
            size_hint_y=None, height=dp(44),
            color=(1, 1, 1, 1), halign='center')
    label.bind(size=lambda s, v: setattr(s, 'text_size', (v[0], None)))
    self.add_widget(label)
    sell_btn = Button(text="Продать", font_size=dp(13),
              size_hint_y=None, height=dp(34),
              background_normal='', background_down='',
              background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
    with sell_btn.canvas.before:
      Color(0.3, 0.6, 0.35, 0.85)
      sell_btn._bg = RoundedRectangle(pos=sell_btn.pos, size=sell_btn.size, radius=[dp(10)])
    sell_btn.bind(pos=lambda w, v: setattr(w._bg, 'pos', v),
            size=lambda w, v: setattr(w._bg, 'size', v))
    sell_btn.bind(on_press=self._sell)
    self.add_widget(sell_btn)

  def _sell(self, *args):
    if self.on_sell: self.on_sell(self.item_type, self.kind, self.case_id)

  def _update_bg(self, *args):
    self.card_bg.pos = self.pos; self.card_bg.size = self.size


class InventoryScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.current_filter = "all"
    self.filter_popup = None
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "particles_up")
    self.add_widget(self.bg_widget)
    root_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    root_layout.add_widget(Label(text="Инвентарь", font_size=dp(26),
                   size_hint_y=None, height=dp(40)))
    self.count_label = Label(text="", font_size=dp(14), size_hint_y=None, height=dp(30))
    root_layout.add_widget(self.count_label)
    filter_btn = Button(text="Фильтр", font_size=dp(16),
               size_hint_y=None, height=dp(48),
               background_normal='', background_down='',
               background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
    with filter_btn.canvas.before:
      Color(0.35, 0.5, 0.75, 0.90)
      filter_btn._bg = RoundedRectangle(pos=filter_btn.pos, size=filter_btn.size, radius=[dp(20)])
    filter_btn.bind(pos=lambda w, v: setattr(w._bg, 'pos', v),
             size=lambda w, v: setattr(w._bg, 'size', v))
    filter_btn.bind(on_press=self._show_filter)
    root_layout.add_widget(filter_btn)
    self.filter_label = Label(text="Фильтр: Всё", font_size=dp(13),
                  size_hint_y=None, height=dp(24),
                  color=(0.85, 0.85, 0.9, 1))
    root_layout.add_widget(self.filter_label)
    scroll = ScrollView(size_hint=(1, 1))
    self.grid = GridLayout(cols=2, spacing=dp(10), padding=dp(10), size_hint_y=None)
    self.grid.bind(minimum_height=self.grid.setter('height'))
    scroll.add_widget(self.grid)
    root_layout.add_widget(scroll)
    self.btn_sell_all = Button(text="Продать всех", font_size=dp(16),
                  size_hint_y=None, height=dp(48),
                  background_normal='', background_down='',
                  background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
    with self.btn_sell_all.canvas.before:
      Color(0.7, 0.35, 0.35, 0.90)
      self.btn_sell_all._bg2 = RoundedRectangle(
        pos=self.btn_sell_all.pos, size=self.btn_sell_all.size, radius=[dp(25)])
    self.btn_sell_all.bind(pos=lambda w, v: setattr(w._bg2, 'pos', v),
                size=lambda w, v: setattr(w._bg2, 'size', v))
    self.btn_sell_all.bind(on_press=self._sell_all)
    root_layout.add_widget(self.btn_sell_all)
    btn_back = GlassButton(text="Назад", height=dp(50))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    root_layout.add_widget(btn_back)
    self.add_widget(root_layout)

  def _show_filter(self, *args):
    if self.filter_popup:
      try: self.remove_widget(self.filter_popup)
      except: pass
      self.filter_popup = None
      return
    p = FilterPopup(current=self.current_filter, on_select=self._apply_filter,
             on_close=self._close_filter)
    self.add_widget(p); self.filter_popup = p

  def _close_filter(self):
    try:
      if self.filter_popup:
        self.remove_widget(self.filter_popup); self.filter_popup = None
    except: pass

  def _apply_filter(self, f):
    self.current_filter = f
    labels = {"all": "Всё"}
    for cid, info in CASE_INFO.items():
      labels[cid] = info["label"]
    self.filter_label.text = f"Фильтр: {labels.get(f, f)}"
    self._close_filter(); self.refresh()

  def on_pre_enter(self, *args):
    Clock.schedule_once(lambda dt: self.refresh(), 0.1)

  def _sell_one(self, item_type, kind, case_id=None):
    data = load_data()
    inventory = data.get("inventory", [])
    for i, item in enumerate(inventory):
      if item.get("type") == item_type and item.get("kind") == kind:
        inventory.pop(i)
        price = get_price(item_type, kind)
        data["coins"] = data.get("coins", 0) + price
        data["inventory"] = inventory
        data["items_sold"] = data.get("items_sold", 0) + 1
        save_data(data); break
    self.refresh()

  def _sell_all(self, *args):
    data = load_data()
    inventory = data.get("inventory", [])
    total = 0; new_inventory = []; sold = 0
    for item in inventory:
      if self.current_filter == "all" or item.get("case") == self.current_filter:
        total += get_price(item.get("type"), item.get("kind"))
        sold += 1
      else: new_inventory.append(item)
    data["inventory"] = new_inventory
    data["coins"] = data.get("coins", 0) + total
    data["items_sold"] = data.get("items_sold", 0) + sold
    save_data(data); self.refresh()

  def refresh(self):
    try:
      self.grid.clear_widgets()
      data = load_data()
      inventory = data.get("inventory", [])
      filtered = inventory if self.current_filter == "all" else \
        [it for it in inventory if it.get("case") == self.current_filter]
      self.count_label.text = f"Всего: {len(filtered)}"
      try: filtered = sorted(filtered, key=lambda x: -get_price(x.get("type"), x.get("kind")))
      except: pass
      for item in filtered:
        try:
          card = InventoryCard(item.get("type"), item.get("kind"),
                      item.get("case"), on_sell=self._sell_one)
          self.grid.add_widget(card)
        except: pass
    except: pass


class FilterPopup(FloatLayout):
  def __init__(self, current, on_select, on_close, **kwargs):
    super().__init__(**kwargs)
    self.on_select = on_select; self.on_close = on_close; self.current = current
    with self.canvas.before:
      self.dim_color = Color(0, 0, 0, 0.85)
      self.dim = Rectangle(pos=self.pos, size=self.size)
    self.bind(pos=self._update_dim, size=self._update_dim)
    panel_w = min(Window.width * 0.9, dp(380))
    panel_h = dp(620)
    with self.canvas:
      Color(0.15, 0.15, 0.2, 0.98)
      self.panel = RoundedRectangle(
        pos=(Window.width / 2 - panel_w / 2, Window.height / 2 - panel_h / 2),
        size=(panel_w, panel_h), radius=[dp(30)])
    title = Label(text="Фильтр по кейсам", font_size=dp(18), bold=True,
            size_hint=(None, None), size=(panel_w, dp(36)),
            pos=(Window.width / 2 - panel_w / 2,
              Window.height / 2 + panel_h / 2 - dp(46)),
            color=(1, 1, 1, 1))
    self.add_widget(title)
    scroll = ScrollView(size_hint=(None, None),
               size=(panel_w - dp(20), panel_h - dp(120)),
               pos=(Window.width / 2 - (panel_w - dp(20)) / 2,
                 Window.height / 2 - panel_h / 2 + dp(80)))
    inner = BoxLayout(orientation='vertical', spacing=dp(6),
              size_hint_y=None, padding=dp(4))
    inner.bind(minimum_height=inner.setter('height'))
    options = [("all", "Всё")]
    for cid, info in CASE_INFO.items():
      options.append((cid, info["label"]))
    for key, label in options:
      is_active = (key == current)
      btn = Button(text=label + (" (активно)" if is_active else ""),
             font_size=dp(14), size_hint_y=None, height=dp(46),
             background_normal='', background_down='',
             background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
      with btn.canvas.before:
        Color(0.4, 0.7, 0.5, 0.9) if is_active else Color(0.35, 0.45, 0.6, 0.85)
        btn._bg = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(18)])
      btn.bind(pos=lambda w, v: setattr(w._bg, 'pos', v),
           size=lambda w, v: setattr(w._bg, 'size', v))
      btn.bind(on_press=lambda x, k=key: self.on_select(k))
      inner.add_widget(btn)
    scroll.add_widget(inner); self.add_widget(scroll)
    close_btn = GlassButton(text="Закрыть")
    close_btn.size_hint = (None, None)
    close_btn.size = (panel_w - dp(60), dp(50))
    close_btn.pos = (Window.width / 2 - (panel_w - dp(60)) / 2,
             Window.height / 2 - panel_h / 2 + dp(20))
    close_btn.bind(on_press=self._close)
    self.add_widget(close_btn)

  def _update_dim(self, *args):
    self.dim.pos = self.pos; self.dim.size = self.size

  def _close(self, *args):
    if self.on_close: self.on_close()


# ============================================================
# РАНГИ
# ============================================================
class RanksScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Мелкие частицы вместо крупных угловых орбов: декор не перекрывает
    # карточки рангов и кнопку «Назад» по краям экрана.
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "rank_sticks")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Ранги", font_size=dp(26), bold=True,
                size_hint_y=None, height=dp(45)))
    data = load_data()
    mmr = data.get("mmr", 0)
    rank_idx = rank_index_by_mmr(mmr)
    self.mmr_label = Label(text=f"MMR: {mmr}  |  {RANKS[rank_idx][1]}",
                font_size=dp(16), size_hint_y=None, height=dp(30))
    layout.add_widget(self.mmr_label)
    scroll = ScrollView(size_hint=(1, 1))
    inner = BoxLayout(orientation='vertical', spacing=dp(8),
              size_hint_y=None, padding=dp(6))
    inner.bind(minimum_height=inner.setter('height'))
    for i, (rid, name, c1, c2) in enumerate(RANKS):
      row = BoxLayout(orientation='horizontal', spacing=dp(10),
               size_hint_y=None, height=dp(80), padding=dp(6))
      with row.canvas.before:
        Color(1, 1, 1, 0.06)
        rbg = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(15)])
      row.bind(pos=lambda w, v, r=rbg: setattr(r, 'pos', v),
           size=lambda w, v, r=rbg: setattr(r, 'size', v))
      icon_holder = FloatLayout(size_hint_x=None, width=dp(75))
      icon = RankIcon(i, dp(70))
      icon.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
      icon_holder.add_widget(icon)
      row.add_widget(icon_holder)
      info = BoxLayout(orientation='vertical', spacing=dp(2))
      info.add_widget(Label(text=name, font_size=dp(16), bold=True,
                  color=(1, 1, 1, 1), size_hint_y=None, height=dp(26)))
      need = rank_threshold(i)
      unlocked = rank_idx >= i
      status = "Получен" if unlocked else f"Нужно {need} MMR"
      info.add_widget(Label(text=status, font_size=dp(11),
                  color=(0.85, 0.85, 0.9, 1) if unlocked else (0.7, 0.7, 0.75, 1),
                  size_hint_y=None, height=dp(22)))
      row.add_widget(info)
      inner.add_widget(row)
    scroll.add_widget(inner)
    layout.add_widget(scroll)
    btn_back = GlassButton(text="Назад", height=dp(50))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def on_pre_enter(self, *args):
    data = load_data()
    mmr = data.get("mmr", 0)
    rank_idx = rank_index_by_mmr(mmr)
    self.mmr_label.text = f"MMR: {mmr}  |  {RANKS[rank_idx][1]}"


# ============================================================
# ПРОФИЛЬ
# ============================================================
class ProfileScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "particles_up")
    self.add_widget(self.bg_widget)

    data = load_data()
    mmr = data.get("mmr", 0)
    rank_idx = rank_index_by_mmr(mmr)
    avatar_key = data.get("avatar", "cat_orange")
    frame_key = data.get("frame", "none")
    nickname = data.get("nickname", "Игрок")

    root = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    root.add_widget(Label(text="Профиль", font_size=dp(24), bold=True,
                size_hint_y=None, height=dp(36)))

    top = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(180),
             spacing=dp(10), padding=dp(4))
    av_holder = FloatLayout(size_hint_x=None, width=dp(150))
    frame_art = FrameArt(frame_key, dp(150))
    frame_art.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
    av_holder.add_widget(frame_art)
    avatar_art = avatar_to_art(avatar_key, dp(70))
    if avatar_art is not None:
      avatar_art.size_hint = (None, None)
      avatar_art.size = (dp(70), dp(70))
      avatar_art.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
      av_holder.add_widget(avatar_art)
    displayed_rank_idx = max(0, min(int(data.get("profile_rank", rank_idx)), len(RANKS) - 1))
    rank_badge_holder = FloatLayout(size_hint=(None, None), size=(dp(50), dp(50)))
    rank_badge = RankIcon(displayed_rank_idx, dp(46))
    rank_badge.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
    rank_badge_holder.add_widget(rank_badge)
    rank_badge_holder.pos_hint = {'center_x': 0.78, 'center_y': 0.22}
    av_holder.add_widget(rank_badge_holder)
    top.add_widget(av_holder)

    info = BoxLayout(orientation='vertical', spacing=dp(4))
    info.add_widget(Label(text=nickname, font_size=dp(20), bold=True,
                color=(1, 1, 1, 1), size_hint_y=None, height=dp(28)))
    info.add_widget(Label(text=f"MMR: {mmr}", font_size=dp(15),
                color=(0.9, 0.9, 0.95, 1), size_hint_y=None, height=dp(24)))
    info.add_widget(Label(text=f"Ранг: {RANKS[rank_idx][1]}", font_size=dp(15),
                color=(0.9, 0.9, 0.95, 1), size_hint_y=None, height=dp(24)))
    # Красивый индикатор пути к следующему рангу.
    rank_floor = rank_threshold(rank_idx)
    next_mmr = rank_threshold(rank_idx + 1) if rank_idx + 1 < len(RANKS) else rank_floor
    progress = 1.0 if rank_idx == len(RANKS) - 1 else max(0.0, min(1.0, (mmr - rank_floor) / max(1, next_mmr - rank_floor)))
    info.add_widget(Label(text=f"Путь к следующему рангу: {int(progress * 100)}%",
               font_size=dp(10), color=(0.55, 0.95, 1, 1),
               size_hint_y=None, height=dp(16)))
    progress_bar = ProgressBar(max=100, value=progress * 100,
                  size_hint_y=None, height=dp(8))
    info.add_widget(progress_bar)
    info.add_widget(Label(text=f"Монеты: {data.get('coins', 0)}", font_size=dp(13),
                color=(1, 0.85, 0.4, 1), size_hint_y=None, height=dp(22)))
    nick_btn = Button(text="Сменить ник", font_size=dp(12),
              size_hint_y=None, height=dp(30),
              background_normal='', background_down='',
              background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
    with nick_btn.canvas.before:
      Color(0.5, 0.4, 0.7, 0.9)
      b = RoundedRectangle(pos=nick_btn.pos, size=nick_btn.size, radius=[dp(10)])
    nick_btn.bind(pos=lambda w, v, r=b: setattr(r, 'pos', v),
            size=lambda w, v, r=b: setattr(r, 'size', v))
    nick_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'nickname'))
    info.add_widget(nick_btn)
    top.add_widget(info)
    root.add_widget(top)

    change_av = GlassButton(text="Купить аватарку", height=dp(44))
    change_av.bind(on_press=lambda x: setattr(self.manager, 'current', 'avatar_select'))
    root.add_widget(change_av)
    change_fr = GlassButton(text="Купить рамку", height=dp(44))
    change_fr.bind(on_press=lambda x: setattr(self.manager, 'current', 'frames'))
    root.add_widget(change_fr)

    # Вместо боевых карт — аккуратная панель достижений профиля.
    showcase = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(82), padding=dp(10), spacing=dp(4))
    with showcase.canvas.before:
      Color(0.12, 0.20, 0.38, 0.88)
      showcase_bg = RoundedRectangle(pos=showcase.pos, size=showcase.size, radius=[dp(18)])
    showcase.bind(pos=lambda w, v, r=showcase_bg: setattr(r, 'pos', v),
           size=lambda w, v, r=showcase_bg: setattr(r, 'size', v))
    showcase.add_widget(Label(text="ТВОЙ ПУТЬ К ВЕРШИНЕ", bold=True, font_size=dp(15),
                 color=(0.55, 0.9, 1, 1)))
    showcase.add_widget(Label(text=f"Ранг: {RANKS[rank_idx][1]} | MMR: {mmr}", font_size=dp(12),
                 color=(1, 1, 1, 1)))
    root.add_widget(showcase)
    rank_btn = GlassButton(text="Открыть ранги", height=dp(42))
    rank_btn.bind(on_press=lambda *_: setattr(self.manager, 'current', 'rank_select'))
    root.add_widget(rank_btn)
    match_btn = GlassButton(text="Рейтинговый матч: заработать MMR", height=dp(44))
    match_btn.bind(on_press=lambda *_: setattr(self.manager, 'current', 'shooter'))
    root.add_widget(match_btn)
    shop_btn = GlassButton(text="Магазин бустов и медалей", height=dp(42))
    shop_btn.bind(on_press=lambda *_: setattr(self.manager, 'current', 'shop'))
    root.add_widget(shop_btn)
    daily_btn = GlassButton(text="Ежедневный подарок", height=dp(42))
    daily_btn.bind(on_press=lambda *_: setattr(self.manager, 'current', 'daily_reward'))
    root.add_widget(daily_btn)
    root.add_widget(Label(text="Профиль можно прокручивать вверх и вниз",
               font_size=dp(10), color=(0.55, 0.85, 1, 1),
               size_hint_y=None, height=dp(18)))

    root.add_widget(Label(text="Статистика", font_size=dp(16), bold=True,
                size_hint_y=None, height=dp(26)))
    inv = data.get("inventory", [])
    stats = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(55), spacing=dp(6))
    for label, val in [("Предметов", len(inv)), ("MMR", mmr),
              ("Кейсов", len(set(i.get("case") for i in inv)))]:
      box = BoxLayout(orientation='vertical')
      with box.canvas.before:
        Color(1, 1, 1, 0.08)
        b = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(10)])
      box.bind(pos=lambda w, v, r=b: setattr(r, 'pos', v),
           size=lambda w, v, r=b: setattr(r, 'size', v))
      box.add_widget(Label(text=str(val), font_size=dp(18), bold=True,
                  color=(1, 1, 1, 1), size_hint_y=None, height=dp(26)))
      box.add_widget(Label(text=label, font_size=dp(10),
                  color=(0.85, 0.85, 0.9, 1), size_hint_y=None, height=dp(18)))
      stats.add_widget(box)
    root.add_widget(stats)
    btn_back = GlassButton(text="Назад", height=dp(46))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    root.add_widget(btn_back)
    # Make all direct profile sections participate in vertical scrolling.
    for child in root.children:
      if child.size_hint_y is not None:
        child.size_hint_y = None
    root.bind(minimum_height=root.setter('height'))
    root.size_hint_y = None
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True,
              bar_width=dp(4), scroll_type=['content', 'bars'])
    scroll.add_widget(root)
    self.add_widget(scroll)

  def on_touch_down(self, touch):
    if self.collide_point(*touch.pos):
      touch.ud['profile_swipe_start_x'] = touch.x
      touch.ud['profile_swipe_start_y'] = touch.y
    return super().on_touch_down(touch)

  def on_touch_up(self, touch):
    start_x = touch.ud.get('profile_swipe_start_x')
    start_y = touch.ud.get('profile_swipe_start_y')
    if start_x is not None and start_y is not None and self.manager:
      dx, dy = touch.x - start_x, touch.y - start_y
      if abs(dx) > dp(110) and abs(dx) > abs(dy) * 1.5:
        self.manager.current = 'shop' if dx < 0 else 'rank_select'
        return True
    return super().on_touch_up(touch)

  def on_pre_enter(self, *args):
    self._build_ui()


class DailyRewardScreen(Screen):
  """Ежедневный бесплатный подарок с сохранением даты и серии входов."""
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.build_ui()

  def build_ui(self):
    self.clear_widgets()
    self.add_widget(AnimatedBg(load_data().get("wallpaper_theme", "fire"), "particles_up"))
    root = BoxLayout(orientation='vertical', padding=dp(22), spacing=dp(14))
    root.add_widget(Label(text="ЕЖЕДНЕВНЫЙ ПОДАРОК", font_size=dp(23), bold=True,
               color=(1, .86, .36, 1), size_hint_y=None, height=dp(48)))
    card = BoxLayout(orientation='vertical', padding=dp(18), spacing=dp(10),
             size_hint_y=None, height=dp(230))
    with card.canvas.before:
      Color(.12, .10, .30, .94)
      self.card_bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(24)])
      Color(.25, .8, 1, .75)
      self.card_border = Line(rounded_rectangle=(card.x, card.y, card.width, card.height, dp(24)), width=1.4)
    card.bind(pos=self._update_card, size=self._update_card)
    card.add_widget(Label(text="  ", font_size=dp(42), size_hint_y=None, height=dp(70)))
    card.add_widget(Label(text="250 монет + 15 MMR", font_size=dp(21), bold=True,
               color=(1, .85, .35, 1), size_hint_y=None, height=dp(38)))
    self.status = Label(text="Заглядывай каждый день за наградой!", font_size=dp(14),
              color=(.9, .94, 1, 1))
    card.add_widget(self.status)
    root.add_widget(card)
    self.streak_lbl = Label(text="Серия входов: 0 дней", font_size=dp(16), bold=True,
                color=(.5, .9, 1, 1), size_hint_y=None, height=dp(32))
    root.add_widget(self.streak_lbl)
    self.claim_btn = GlassButton(text="Забрать подарок", height=dp(52))
    self.claim_btn.bind(on_press=self.claim_reward)
    root.add_widget(self.claim_btn)
    back = GlassButton(text="Назад в профиль", height=dp(46))
    back.bind(on_press=lambda *_: setattr(self.manager, 'current', 'profile'))
    root.add_widget(back)
    root.add_widget(Label(text="Подарок обновляется раз в день | прогресс сохраняется",
               font_size=dp(10), color=(.75, .8, .9, 1), size_hint_y=None, height=dp(24)))
    self.add_widget(root)
    self.refresh_state()

  def _update_card(self, widget, *_):
    self.card_bg.pos = widget.pos; self.card_bg.size = widget.size
    self.card_border.rounded_rectangle = (widget.x, widget.y, widget.width, widget.height, dp(24))

  def refresh_state(self):
    data = load_data()
    streak = int(data.get('daily_streak', 0))
    self.streak_lbl.text = f" Серия входов: {streak} дн."
    claimed = data.get('daily_reward_date') == date.today().isoformat()
    self.claim_btn.disabled = claimed
    self.claim_btn.text = "Уже получено сегодня " if claimed else "Забрать подарок"
    self.status.text = "Возвращайся завтра за новым подарком!" if claimed else "Сегодня тебя ждут монеты и MMR!"

  def claim_reward(self, *_):
    data = load_data()
    today = date.today()
    today_s = today.isoformat()
    if data.get('daily_reward_date') == today_s:
      self.refresh_state(); return
    previous = data.get('daily_reward_date', '')
    try:
      previous_day = date.fromisoformat(previous)
      streak = int(data.get('daily_streak', 0)) + 1 if previous_day == today - timedelta(days=1) else 1
    except Exception:
      streak = 1
    data['coins'] = int(data.get('coins', 0)) + 250
    data['mmr'] = int(data.get('mmr', 0)) + 15
    data['daily_streak'] = streak
    data['daily_reward_date'] = today_s
    save_data(data)
    self.refresh_state()
    self.status.text = "Подарок получен! +250 монет и +15 MMR "


class BattleCardArt(FloatLayout):
  """Квадратная анимированная карта профиля с уникальными цветами и медалью."""
  phase = NumericProperty(0)
  PALETTES = {
    "Космический импульс": ((0.12, 0.08, 0.42), (0.05, 0.65, 0.95)),
    "Изумрудный шторм": ((0.02, 0.28, 0.20), (0.25, 0.95, 0.55)),
    "Золотой чемпион": ((0.35, 0.15, 0.02), (1.0, 0.72, 0.12)),
    "Ледяной разлом": ((0.05, 0.2, 0.38), (0.55, 0.9, 1.0)),
  }
  def __init__(self, card_name="Космический импульс", medal="", **kwargs):
    super().__init__(**kwargs); self.card_name=card_name; self.medal=medal
    self.bind(pos=self.redraw, size=self.redraw)
    Clock.schedule_interval(self.animate, 1/30)
    self.redraw()
  def animate(self, dt):
    self.phase = (self.phase + dt) % 6.28
    self.redraw()
  def redraw(self, *args):
    self.canvas.clear()
    c1,c2=self.PALETTES.get(self.card_name, self.PALETTES["Космический импульс"])
    x,y=self.pos; w,h=self.size; pulse=(math.sin(self.phase)+1)/2
    with self.canvas:
      Color(*c1,1); RoundedRectangle(pos=(x,y), size=(w,h), radius=[dp(14)])
      Color(*c2,0.18+0.25*pulse); Ellipse(pos=(x+w*.12,y+h*.25), size=(w*.76,h*.76))
      Color(1,1,1,0.12+0.16*pulse)
      for i in range(5):
        Line(points=[x+w*(.08+i*.18), y+h*.12, x+w*(.35+i*.12), y+h*.92], width=1.2)
      Color(1,0.86,0.3,0.95); Line(points=[x+w*.16,y+h*.78,x+w*.5,y+h*.94,x+w*.84,y+h*.78], width=1.6)
      if self.medal:
        Color(1,0.78,0.15,1); Ellipse(pos=(x+w*.68,y+h*.04), size=(w*.25,h*.25))
        Color(.15,.08,.02,1); Ellipse(pos=(x+w*.735,y+h*.095), size=(w*.14,h*.14))


class ShopItemArt(Widget):
  """Self-contained vector item texture; no external image files required."""
  def __init__(self, kind='boost', **kwargs):
    super().__init__(**kwargs)
    self.kind = kind
    self.bind(pos=self.redraw, size=self.redraw)
    self.redraw()

  def redraw(self, *args):
    self.canvas.clear()
    x, y = self.pos; w, h = self.size
    cx, cy = x + w * .5, y + h * .5
    r = min(w, h) * .43
    with self.canvas:
      # dark translucent glass tile and thin neutral border
      Color(.12, .13, .15, .96); RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(13)])
      Color(.68, .71, .76, .78); Line(rounded_rectangle=(x, y, w, h, dp(13)), width=1)
      Color(.9, .91, .93, .10); Ellipse(pos=(cx-r*.75, cy+r*.1), size=(r*1.5, r*1.5))
      if self.kind == 'boost':
        Color(.78, .81, .85, 1)
        # metallic hex core with inner bars
        pts=[cx,cy+r, cx+r*.78,cy+r*.45, cx+r*.78,cy-r*.45, cx,cy-r, cx-r*.78,cy-r*.45, cx-r*.78,cy+r*.45]
        Line(points=pts+[pts[0],pts[1]], close=True, width=1.5)
        Color(.9,.92,.95,.9); Line(points=[cx-r*.42,cy-r*.25,cx-r*.42,cy+r*.25,cx+r*.42,cy+r*.25,cx+r*.42,cy-r*.25], width=2)
      else:
        Color(.78,.81,.85,1); Ellipse(pos=(cx-r*.62,cy-r*.62),size=(r*1.24,r*1.24))
        Color(.25,.27,.30,1); Ellipse(pos=(cx-r*.42,cy-r*.42),size=(r*.84,r*.84))
        Color(.94,.95,.97,1); Line(points=[cx,cy+r*.47,cx+r*.12,cy+r*.12,cx+r*.46,cy,cx+r*.12,cy-r*.12,cx,cy-r*.46,cx-r*.12,cy-r*.12,cx-r*.46,cy,cx-r*.12,cy+r*.12,cx,cy+r*.47],width=1.4)


class ShopScreen(Screen):
  BOOSTS = [(2, 5000), (4, 25000), (6, 100000)]
  MEDALS = [("Золотая звезда", 12000), ("Лунная медаль", 30000), ("Королевский знак", 75000)]

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.build_ui()

  def _item_card(self, title, description, price, action, accent=(0.25, 0.72, 1.0, 1), owned=False):
    card = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(104), spacing=dp(10), padding=dp(10))
    with card.canvas.before:
      Color(0.12, 0.13, 0.15, 0.90)
      card_bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(16)])
      Color(0.68, 0.71, 0.76, 0.78)
      card_line = Line(rounded_rectangle=(card.x, card.y, card.width, card.height, dp(16)), width=1.0)
    def update_card(widget, *_):
      card_bg.pos = widget.pos; card_bg.size = widget.size
      card_line.rounded_rectangle = (widget.x, widget.y, widget.width, widget.height, dp(16))
    card.bind(pos=update_card, size=update_card)

    icon_box = BoxLayout(size_hint_x=None, width=dp(76), padding=dp(1))
    art = ShopItemArt('boost' if "Буст" in title else 'medal', size_hint=(1, 1))
    icon_box.add_widget(art)
    card.add_widget(icon_box)

    details = BoxLayout(orientation='vertical', spacing=dp(3), size_hint_x=1)
    title_lbl = Label(text=title, font_size=dp(13), bold=True,
                 halign='left', valign='middle', color=(0.96, 0.96, 0.97, 1),
                 size_hint_y=None, height=dp(28), shorten=True, shorten_from='right')
    title_lbl.bind(size=lambda w, _v: setattr(w, 'text_size', (max(dp(30), w.width), None)))
    details.add_widget(title_lbl)
    desc_lbl = Label(text=description, font_size=dp(10), halign='left', valign='top',
                 color=(0.82, 0.83, 0.85, 1), size_hint_y=1, text_size=(0, None),
                 shorten=True, shorten_from='right')
    desc_lbl.bind(size=lambda w, _v: setattr(w, 'text_size', (max(dp(30), w.width), None)))
    details.add_widget(desc_lbl)
    card.add_widget(details)

    buy = GlassButton(text=("Установлено" if owned else f"{price:,} монет".replace(',', ' ')), height=dp(42))
    buy.size_hint_x = None
    buy.width = dp(104)
    buy.font_size = dp(11)
    buy.disabled = owned
    buy.bind(on_press=action)
    card.add_widget(buy)
    return card

  def build_ui(self):
    self.clear_widgets()
    self.add_widget(AnimatedBg(load_data().get("wallpaper_theme", "fire"), "particles_up"))
    root = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(7))
    root.add_widget(Label(text="МАГАЗИН", font_size=dp(25), bold=True, size_hint_y=None, height=dp(42)))
    data = load_data()
    root.add_widget(Label(text=f"Баланс: {data.get('coins', 0)} монет", size_hint_y=None, height=dp(26),
               color=(1, .85, .35, 1)))
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True, bar_width=dp(4))
    items = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(9), padding=dp(4))
    items.bind(minimum_height=items.setter('height'))
    current = int(data.get('tap_boost', 1))
    items.add_widget(Label(text=f"УЛУЧШЕНИЕ ТАПА | Текущий множитель: x{current}",
                size_hint_y=None, height=dp(34), bold=True))
    for mult, price in self.BOOSTS:
      card = self._item_card(f"Буст тапалки x{mult}", "Увеличивает награду за нажатие", price,
                  lambda _b, m=mult, p=price: self.buy_boost(m, p),
                  accent=(0.2, 0.72, 1.0, 1), owned=(current == mult))
      items.add_widget(card)
    items.add_widget(Label(text="КОЛЛЕКЦИОННЫЕ МЕДАЛИ", size_hint_y=None, height=dp(34), bold=True))
    owned_medals = data.get('medals_owned', [])
    for name, price in self.MEDALS:
      card = self._item_card(name, "Коллекционная награда для профиля", price,
                  lambda _b, n=name, p=price: self.buy_medal(n, p),
                  accent=(1.0, 0.69, 0.18, 1), owned=(name in owned_medals and data.get('medal') == name))
      items.add_widget(card)
    scroll.add_widget(items)
    root.add_widget(scroll)
    self.status = Label(text="Покупки сохраняются в профиле", size_hint_y=None, height=dp(28), color=(.7, 1, .8, 1))
    root.add_widget(self.status)
    back = GlassButton(text="Назад", height=dp(44))
    back.bind(on_press=lambda *_: setattr(self.manager, 'current', 'main'))
    root.add_widget(back)
    self.add_widget(root)

  def buy_boost(self, mult, price):
    data = load_data(); coins = int(data.get('coins', 0))
    if coins < price:
      self.status.text = "Не хватает монет"
      return
    data['coins'] = coins - price; data['tap_boost'] = mult; save_data(data)
    self.build_ui()
    self.status.text = f"Куплен буст x{mult}"

  def buy_medal(self, name, price):
    data = load_data(); coins = int(data.get('coins', 0)); owned = data.get('medals_owned', [])
    if name in owned:
      data['medal'] = name; save_data(data); self.build_ui(); self.status.text = f"Медаль {name} установлена"; return
    if coins < price:
      self.status.text = "Не хватает монет"
      return
    data['coins'] = coins - price; owned.append(name); data['medals_owned'] = owned; data['medal'] = name
    save_data(data); self.build_ui(); self.status.text = f"Куплена и установлена: {name}"

class BattleCardsScreen(Screen):
  CARDS = ["Космический импульс", "Изумрудный шторм", "Золотой чемпион", "Ледяной разлом"]
  def __init__(self, **kwargs): super().__init__(**kwargs); self.build_ui()
  def build_ui(self):
    self.clear_widgets(); self.add_widget(AnimatedBg(load_data().get("wallpaper_theme", "fire"), "waves"))
    root=BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
    root.add_widget(Label(text="БОЕВЫЕ КАРТЫ", font_size=dp(23), bold=True, size_hint_y=None, height=dp(40)))
    data=load_data(); current=data.get('battle_card', self.CARDS[0])
    scroll=ScrollView(); grid=GridLayout(cols=2, spacing=dp(10), size_hint_y=None, padding=dp(4)); grid.bind(minimum_height=grid.setter('height'))
    for name in self.CARDS:
      cell=BoxLayout(orientation='vertical', size_hint_y=None, height=dp(175), spacing=dp(4))
      cell.add_widget(BattleCardArt(name, data.get('medal',''), size_hint=(None,None), size=(dp(112),dp(112)), pos_hint={'center_x':.5}))
      cell.add_widget(Label(text=name + (" " if name==current else ""), size_hint_y=None, height=dp(24), font_size=dp(11)))
      b=GlassButton(text="Применить", height=dp(32)); b.bind(on_press=lambda _b,n=name:self.apply_card(n)); cell.add_widget(b); grid.add_widget(cell)
    scroll.add_widget(grid); root.add_widget(scroll)
    back=GlassButton(text="Назад в профиль", height=dp(44)); back.bind(on_press=lambda *_: setattr(self.manager,'current','profile')); root.add_widget(back); self.add_widget(root)
  def apply_card(self,name):
    d=load_data(); d['battle_card']=name; save_data(d); self.build_ui()

class RankSelectScreen(Screen):
  def __init__(self, **kwargs): super().__init__(**kwargs); self.build_ui()
  def build_ui(self):
    self.clear_widgets(); self.add_widget(AnimatedBg(load_data().get("wallpaper_theme", "fire"), "rank_sticks"))
    root=BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(6)); root.add_widget(Label(text="ВЫБОР РАНГА ПРОФИЛЯ", font_size=dp(22), bold=True, size_hint_y=None, height=dp(42)))
    d=load_data(); mmr=int(d.get('mmr',0)); unlocked=(rank_index_by_mmr(mmr) if mmr >= 1000 else -1); chosen=int(d.get('profile_rank',max(0,unlocked)))
    scroll=ScrollView(); grid=GridLayout(cols=2, spacing=dp(6), size_hint_y=None); grid.bind(minimum_height=grid.setter('height'))
    for i,r in enumerate(RANKS[:unlocked+1]):
      cell=BoxLayout(orientation='vertical', size_hint_y=None, height=dp(148), spacing=dp(3), padding=(dp(6),dp(6)))
      # Subtle outline around each rank card, with a slightly brighter selected state.
      with cell.canvas.before:
        Color(0.72, 0.65, 0.9, 0.34 if i != chosen else 0.82)
        card_outline = Line(rounded_rectangle=(cell.x, cell.y, cell.width, cell.height, dp(13)), width=1.05 if i != chosen else 1.5)
      cell.bind(pos=lambda w, *_args, outline=card_outline: setattr(outline, 'rounded_rectangle', (w.x, w.y, w.width, w.height, dp(13))),
                size=lambda w, *_args, outline=card_outline: setattr(outline, 'rounded_rectangle', (w.x, w.y, w.width, w.height, dp(13))))
      icon_holder=AnchorLayout(anchor_x='center', anchor_y='bottom', size_hint_y=None, height=dp(76))
      icon_holder.add_widget(RankIcon(i,dp(64),size_hint=(None,None),size=(dp(64),dp(64))))
      cell.add_widget(icon_holder)
      cell.add_widget(Label(text=f"Открывается: {rank_threshold(i)} MMR", font_size=dp(9), size_hint_y=None, height=dp(16), color=(.7,.82,1,1), halign='center', valign='middle'))
      b=GlassButton(text=r[1]+(" [ВЫБРАН]" if i==chosen else ""), height=dp(34)); b.bind(on_press=lambda _b,idx=i:self.apply_rank(idx)); cell.add_widget(b); grid.add_widget(cell)
    scroll.add_widget(grid); root.add_widget(scroll)
    back=GlassButton(text="Назад в профиль", height=dp(44)); back.bind(on_press=lambda *_:setattr(self.manager,'current','profile')); root.add_widget(back); self.add_widget(root)
  def apply_rank(self,idx):
    d=load_data(); d['profile_rank']=idx; save_data(d); self.build_ui()


class NicknameScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "waves")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
    layout.add_widget(Label(text="Смена ника", font_size=dp(24), bold=True,
                size_hint_y=None, height=dp(40)))
    layout.add_widget(Label(text="Введи свой ник (2-16 символов)",
                font_size=dp(14), size_hint_y=None, height=dp(30)))
    self.text_input = TextInput(
      text=load_data().get("nickname", "Игрок"),
      multiline=False, font_size=dp(20),
      size_hint_y=None, height=dp(60),
      background_color=(1, 1, 1, 0.15),
      foreground_color=(1, 1, 1, 1),
      cursor_color=(1, 1, 1, 1),
      padding=[dp(12), dp(14)])
    layout.add_widget(self.text_input)
    self.result_lbl = Label(text="", font_size=dp(14),
                 size_hint_y=None, height=dp(28),
                 color=(1, 0.6, 0.6, 1))
    layout.add_widget(self.result_lbl)
    save_btn = GlassButton(text="Сохранить", height=dp(55))
    save_btn.bind(on_press=self._save)
    layout.add_widget(save_btn)
    btn_back = GlassButton(text="Назад", height=dp(50))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'profile'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def _save(self, *args):
    nick = self.text_input.text.strip()
    if len(nick) < 2:
      self.result_lbl.text = "Слишком короткий ник (мин. 2)"; return
    if len(nick) > 16:
      self.result_lbl.text = "Слишком длинный ник (макс. 16)"; return
    data = load_data()
    data["nickname"] = nick
    save_data(data)
    self.manager.current = 'profile'


# ============================================================
# АВАТАРЫ
# ============================================================
class AvatarSelectScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "corners")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Выбор аватара", font_size=dp(22), bold=True,
                size_hint_y=None, height=dp(40)))
    scroll = ScrollView(size_hint=(1, 1))
    grid = GridLayout(cols=3, spacing=dp(10), padding=dp(8), size_hint_y=None)
    grid.bind(minimum_height=grid.setter('height'))
    data = load_data()
    owned = data.get("owned_avatars", [av[0] for av in AVATARS[:6]])
    for av_key, av_name in AVATARS:
      is_owned = av_key in owned
      card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(160),
               padding=dp(4), spacing=dp(2))
      with card.canvas.before:
        Color(1, 1, 1, 0.10 if is_owned else 0.05)
        bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
      card.bind(pos=lambda w, v, r=bg: setattr(r, 'pos', v),
           size=lambda w, v, r=bg: setattr(r, 'size', v))
      art_holder = FloatLayout(size_hint_y=None, height=dp(90))
      art = avatar_to_art(av_key, dp(70))
      if art is not None:
        art.size_hint = (None, None); art.size = (dp(70), dp(70))
        art.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        art_holder.add_widget(art)
      card.add_widget(art_holder)
      card.add_widget(Label(text=av_name, font_size=dp(10),
                  color=(1, 1, 1, 1), size_hint_y=None, height=dp(20)))
      if is_owned:
        btn = Button(text="Куплено", font_size=dp(12),
               size_hint_y=None, height=dp(28), disabled=True,
               background_normal='', background_down='',
               background_color=(0, 0, 0, 0), color=(0.55, 0.95, 0.65, 1))
        card.add_widget(btn)
      else:
        btn = Button(text="Купить 1000м", font_size=dp(11),
               size_hint_y=None, height=dp(28),
               background_normal='', background_down='',
               background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
        with btn.canvas.before:
          Color(0.9, 0.6, 0.2, 0.9)
          b = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(10)])
        btn.bind(pos=lambda w, v, r=b: setattr(r, 'pos', v),
             size=lambda w, v, r=b: setattr(r, 'size', v))
        btn.bind(on_press=lambda x, k=av_key: self._buy_avatar(k))
        card.add_widget(btn)
      grid.add_widget(card)
    scroll.add_widget(grid)
    layout.add_widget(scroll)
    btn_back = GlassButton(text="Назад", height=dp(50))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'profile'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def on_pre_enter(self, *args):
    self._build_ui()

  def _select(self, key):
    data = load_data()
    data["avatar"] = key
    save_data(data)
    self.manager.current = 'profile'

  def _buy_avatar(self, key):
    data = load_data()
    if data.get("coins", 0) < 1000: return
    data["coins"] -= 1000
    owned = data.get("owned_avatars", [av[0] for av in AVATARS[:6]])
    if key not in owned: owned.append(key)
    data["owned_avatars"] = owned
    save_data(data)
    self._build_ui()


# ============================================================
# РАМКИ
# ============================================================
class FramesScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "waves")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Рамки профиля", font_size=dp(22), bold=True,
                size_hint_y=None, height=dp(40)))
    data = load_data()
    self.coins_label = Label(text=f"Монеты: {data.get('coins', 0)}",
                  font_size=dp(14), size_hint_y=None, height=dp(24))
    layout.add_widget(self.coins_label)
    scroll = ScrollView(size_hint=(1, 1))
    inner = BoxLayout(orientation='vertical', spacing=dp(8),
              size_hint_y=None, padding=dp(6))
    inner.bind(minimum_height=inner.setter('height'))
    owned = data.get("owned_frames", ["none"])
    current = data.get("frame", "none")
    for fk, fn, price, color, shape in FRAMES:
      row = BoxLayout(orientation='horizontal', spacing=dp(8),
               size_hint_y=None, height=dp(80), padding=dp(6))
      with row.canvas.before:
        Color(1, 1, 1, 0.06)
        rbg = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(12)])
      row.bind(pos=lambda w, v, r=rbg: setattr(r, 'pos', v),
           size=lambda w, v, r=rbg: setattr(r, 'size', v))
      fr_holder = FloatLayout(size_hint_x=None, width=dp(80))
      fr_preview = FrameArt(fk, dp(75))
      fr_preview.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
      fr_holder.add_widget(fr_preview)
      row.add_widget(fr_holder)
      info = BoxLayout(orientation='vertical', spacing=dp(2))
      info.add_widget(Label(text=fn, font_size=dp(14), bold=True,
                  color=(1, 1, 1, 1), size_hint_y=None, height=dp(24)))
      status = "Куплено" if fk in owned else f"Цена: {price}м"
      info.add_widget(Label(text=status, font_size=dp(11),
                  color=(0.85, 0.85, 0.9, 1), size_hint_y=None, height=dp(20)))
      row.add_widget(info)
      if fk not in owned:
        buy = Button(text="Купить", font_size=dp(12),
               size_hint=(None, None), size=(dp(80), dp(40)),
               background_normal='', background_down='',
               background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
        with buy.canvas.before:
          Color(0.7, 0.5, 0.2, 0.9)
          b = RoundedRectangle(pos=buy.pos, size=buy.size, radius=[dp(12)])
        buy.bind(pos=lambda w, v, r=b: setattr(r, 'pos', v),
             size=lambda w, v, r=b: setattr(r, 'size', v))
        buy.bind(on_press=lambda x, k=fk, p=price: self._buy(k, p))
        row.add_widget(buy)
      else:
        purchased = Label(text="Куплено", font_size=dp(11),
                          color=(0.55, 0.95, 0.65, 1),
                          size_hint=(None, None), size=(dp(80), dp(40)))
        row.add_widget(purchased)
      inner.add_widget(row)
    scroll.add_widget(inner)
    layout.add_widget(scroll)
    btn_back = GlassButton(text="Назад", height=dp(50))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'profile'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def on_pre_enter(self, *args):
    self._build_ui()

  def _buy(self, fk, price):
    data = load_data()
    if data.get("coins", 0) < price: return
    data["coins"] -= price
    owned = data.get("owned_frames", ["none"])
    if fk not in owned: owned.append(fk)
    data["owned_frames"] = owned
    save_data(data)
    self._build_ui()

  def _equip(self, fk):
    data = load_data()
    data["frame"] = fk
    save_data(data)
    self._build_ui()


# ============================================================
# ИНВЕНТАРЬ АВАТАРОК (здесь можно применять купленные аватары)
# ============================================================
class AvatarsInventoryScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.add_widget(AnimatedBg(load_data().get("wallpaper_theme", "fire"), "corners"))
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Инвентарь аватарок", font_size=dp(22), bold=True,
                            size_hint_y=None, height=dp(42)))
    scroll = ScrollView(size_hint=(1, 1))
    grid = GridLayout(cols=3, spacing=dp(10), padding=dp(8), size_hint_y=None)
    grid.bind(minimum_height=grid.setter('height'))
    data = load_data()
    owned = data.get("owned_avatars", [av[0] for av in AVATARS[:6]])
    current = data.get("avatar", AVATARS[0][0])
    for key, name in AVATARS:
      if key not in owned:
        continue
      card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150),
                       padding=dp(4), spacing=dp(3))
      art_holder = FloatLayout(size_hint_y=None, height=dp(85))
      art = avatar_to_art(key, dp(68))
      if art is not None:
        art.size_hint = (None, None); art.size = (dp(68), dp(68))
        art.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        art_holder.add_widget(art)
      card.add_widget(art_holder)
      card.add_widget(Label(text=name, font_size=dp(10), size_hint_y=None, height=dp(20)))
      is_current = key == current
      btn = Button(text="Используется" if is_current else "Применить",
                   font_size=dp(11), size_hint_y=None, height=dp(30),
                   disabled=is_current, background_normal='', background_down='',
                   background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
      with btn.canvas.before:
        Color(0.35, 0.65, 0.45, 0.9)
        bg = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(10)])
      btn.bind(pos=lambda w, v, r=bg: setattr(r, 'pos', v),
               size=lambda w, v, r=bg: setattr(r, 'size', v))
      btn.bind(on_press=lambda _btn, k=key: self._apply(k))
      card.add_widget(btn)
      grid.add_widget(card)
    scroll.add_widget(grid); layout.add_widget(scroll)
    back = GlassButton(text="Назад", height=dp(50))
    back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    layout.add_widget(back); self.add_widget(layout)

  def on_pre_enter(self, *args):
    self._build_ui()

  def _apply(self, key):
    data = load_data(); data["avatar"] = key; save_data(data)
    self._build_ui()


# ============================================================
# ИНВЕНТАРЬ РАМОК (здесь можно применять купленные рамки)
# ============================================================
class FramesInventoryScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.add_widget(AnimatedBg(load_data().get("wallpaper_theme", "fire"), "waves"))
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Инвентарь рамок", font_size=dp(22), bold=True,
                            size_hint_y=None, height=dp(42)))
    scroll = ScrollView(size_hint=(1, 1))
    inner = BoxLayout(orientation='vertical', spacing=dp(8),
                      size_hint_y=None, padding=dp(6))
    inner.bind(minimum_height=inner.setter('height'))
    data = load_data()
    owned = data.get("owned_frames", ["none"])
    current = data.get("frame", "none")
    for key, name, price, color, shape in FRAMES:
      if key not in owned:
        continue
      row = BoxLayout(orientation='horizontal', spacing=dp(8),
                      size_hint_y=None, height=dp(76), padding=dp(6))
      holder = FloatLayout(size_hint_x=None, width=dp(76))
      art = FrameArt(key, dp(68)); art.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
      holder.add_widget(art); row.add_widget(holder)
      info = BoxLayout(orientation='vertical', spacing=dp(2))
      info.add_widget(Label(text=name, font_size=dp(14), bold=True,
                            size_hint_y=None, height=dp(25)))
      info.add_widget(Label(text="Используется" if key == current else "Куплено",
                            font_size=dp(11), color=(0.65, 0.95, 0.7, 1),
                            size_hint_y=None, height=dp(20)))
      row.add_widget(info)
      btn = Button(text="Надето" if key == current else "Применить",
                   font_size=dp(12), size_hint=(None, None), size=(dp(92), dp(40)),
                   disabled=(key == current), background_normal='', background_down='',
                   background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
      with btn.canvas.before:
        Color(0.4, 0.7, 0.5, 0.9)
        bg = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])
      btn.bind(pos=lambda w, v, r=bg: setattr(r, 'pos', v),
               size=lambda w, v, r=bg: setattr(r, 'size', v))
      btn.bind(on_press=lambda _btn, k=key: self._apply(k))
      row.add_widget(btn); inner.add_widget(row)
    scroll.add_widget(inner); layout.add_widget(scroll)
    back = GlassButton(text="Назад", height=dp(50))
    back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    layout.add_widget(back); self.add_widget(layout)

  def on_pre_enter(self, *args):
    self._build_ui()

  def _apply(self, key):
    data = load_data(); data["frame"] = key; save_data(data)
    self._build_ui()


# ============================================================
# ТИР
# ============================================================
class TargetWidget(FloatLayout):
  def __init__(self, size_t=dp(90), **kwargs):
    super().__init__(**kwargs)
    self.size_hint = (None, None); self.size = (size_t, size_t)
    self.hit = False
    with self.canvas:
      self.outer_color = Color(0.9, 0.2, 0.2, 1); self.outer = Ellipse()
      self.mid_color = Color(1, 1, 1, 1); self.mid = Ellipse()
      self.inner_color = Color(0.9, 0.2, 0.2, 1); self.inner = Ellipse()
      self.core_color = Color(0.1, 0.1, 0.1, 1); self.core = Ellipse()
      self.cross_color = Color(1, 1, 1, 0.9)
      self.cross_h = Line(points=[], width=dp(2))
      self.cross_v = Line(points=[], width=dp(2))
    self.bind(pos=self.redraw, size=self.redraw)
    Clock.schedule_once(lambda dt: self.redraw(), 0.05)

  def redraw(self, *args):
    s = self.width
    if s < 5: return
    cx = self.x + s / 2; cy = self.y + s / 2
    r = s * 0.48
    self.outer.pos = (cx - r, cy - r); self.outer.size = (r * 2, r * 2)
    r2 = r * 0.7
    self.mid.pos = (cx - r2, cy - r2); self.mid.size = (r2 * 2, r2 * 2)
    r3 = r * 0.42
    self.inner.pos = (cx - r3, cy - r3); self.inner.size = (r3 * 2, r3 * 2)
    r4 = r * 0.18
    self.core.pos = (cx - r4, cy - r4); self.core.size = (r4 * 2, r4 * 2)
    self.cross_h.points = [cx - r * 0.7, cy, cx + r * 0.7, cy]
    self.cross_v.points = [cx, cy - r * 0.7, cx, cy + r * 0.7]

  def mark_hit(self):
    self.hit = True
    self.outer_color.rgba = (0.2, 0.8, 0.3, 1)
    self.inner_color.rgba = (0.2, 0.8, 0.3, 1)


class TargetShooterScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "corners")
    self.add_widget(self.bg_widget)
    self.targets = []; self.hits = 0; self.shots_left = 5; self.finished = False
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Тир", font_size=dp(26), bold=True,
                size_hint_y=None, height=dp(36)))
    self.info_lbl = Label(text="Попади в 5 мишеней! Осталось выстрелов: 5",
                font_size=dp(14), size_hint_y=None, height=dp(28),
                color=(1, 1, 1, 1))
    layout.add_widget(self.info_lbl)
    self.score_lbl = Label(text="Попаданий: 0 / 5", font_size=dp(16), bold=True,
                size_hint_y=None, height=dp(28),
                color=(1, 0.9, 0.4, 1))
    layout.add_widget(self.score_lbl)
    self.field = FloatLayout(size_hint=(1, 1))
    self.field.bind(on_touch_down=self._on_tap)
    layout.add_widget(self.field)
    self.result_lbl = Label(text="", font_size=dp(16), bold=True,
                 size_hint_y=None, height=dp(34),
                 color=(1, 0.85, 0.4, 1))
    layout.add_widget(self.result_lbl)
    restart_btn = GlassButton(text="Начать заново", height=dp(46))
    restart_btn.bind(on_press=self._reset)
    layout.add_widget(restart_btn)
    btn_back = GlassButton(text="Назад", height=dp(46))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    layout.add_widget(btn_back)
    self.add_widget(layout)
    Clock.schedule_once(self._spawn_targets, 0.3)

  def _spawn_targets(self, dt):
    if self.field.width < 50:
      Clock.schedule_once(self._spawn_targets, 0.2); return
    for t in self.targets:
      try: self.field.remove_widget(t)
      except: pass
    self.targets = []
    positions = []
    attempts = 0
    while len(positions) < 5 and attempts < 200:
      attempts += 1
      x = random.uniform(0.05, 0.80); y = random.uniform(0.05, 0.75)
      ok = True
      for (px, py) in positions:
        if abs(x - px) < 0.18 and abs(y - py) < 0.14:
          ok = False; break
      if ok: positions.append((x, y))
    for (x, y) in positions:
      t = TargetWidget(dp(80))
      t.pos_hint = {'x': x, 'y': y}
      t.size_hint = (None, None); t.size = (dp(80), dp(80))
      self.field.add_widget(t)
      self.targets.append(t)

  def _on_tap(self, widget, touch):
    if self.finished: return False
    if not self.field.collide_point(*touch.pos): return False
    for t in self.targets:
      if t.hit: continue
      if t.collide_point(*touch.pos):
        t.mark_hit()
        self.hits += 1; self.shots_left -= 1
        self.score_lbl.text = f"Попаданий: {self.hits} / 5"
        self.info_lbl.text = f"Осталось выстрелов: {self.shots_left}"
        if self.hits >= 3: self._finish(win=True)
        elif self.shots_left <= 0: self._finish(win=False)
        return True
    self.shots_left -= 1
    self.info_lbl.text = f"Мимо! Осталось: {self.shots_left}"
    if self.shots_left <= 0: self._finish(win=False)
    return True

  def _finish(self, win):
    self.finished = True
    if win:
      data = load_data()
      reward = 50 if self.hits >= 5 else 25
      data["mmr"] = max(0, int(data.get("mmr", 0)) + reward)
      data["targets_hit"] = int(data.get("targets_hit", 0)) + self.hits
      data["ranked_matches"] = int(data.get("ranked_matches", 0)) + 1
      data["ranked_wins"] = int(data.get("ranked_wins", 0)) + 1
      save_data(data)
      self.result_lbl.text = f"ПОБЕДА! +{reward} MMR"
      self.result_lbl.color = (0.92, 0.93, 0.95, 1)
    else:
      data = load_data()
      data["ranked_matches"] = int(data.get("ranked_matches", 0)) + 1
      data["ranked_losses"] = int(data.get("ranked_losses", 0)) + 1
      old_mmr = int(data.get("mmr", 0))
      loss = min(10, old_mmr)
      data["mmr"] = old_mmr - loss
      save_data(data)
      self.result_lbl.text = f"ПОРАЖЕНИЕ: -{loss} MMR. Попробуй ещё раз"
      self.result_lbl.color = (0.88, 0.89, 0.92, 1)

  def _reset(self, *args):
    self.finished = False; self.hits = 0; self.shots_left = 5
    self.info_lbl.text = "Попади в 5 мишеней! Осталось выстрелов: 5"
    self.score_lbl.text = "Попаданий: 0 / 5"
    self.result_lbl.text = ""
    self._spawn_targets(0)

  def on_pre_enter(self, *args):
    self._reset()


# ============================================================
# КАЗИНО (скруглённые кнопки)
# ============================================================
class CasinoScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "waves")
    self.add_widget(self.bg_widget)
    self.spinning = False
    self.history = []
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Казино", font_size=dp(26), bold=True,
                size_hint_y=None, height=dp(36)))
    self.coins_lbl = Label(text="", font_size=dp(15), size_hint_y=None, height=dp(26))
    layout.add_widget(self.coins_lbl)
    self.result_lbl = Label(text="Выбери ставку", font_size=dp(16), bold=True,
                 size_hint_y=None, height=dp(40),
                 color=(1, 0.85, 0.4, 1))
    layout.add_widget(self.result_lbl)

    # КРАСНОЕ/ЧЁРНОЕ со скруглением
    field = BoxLayout(orientation='horizontal', spacing=dp(6),
              size_hint_y=None, height=dp(100))
    red_btn = Button(text="КРАСНОЕ\nx2", font_size=dp(18), bold=True,
             background_normal='', background_down='',
             background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
    with red_btn.canvas.before:
      Color(0.85, 0.15, 0.15, 0.95)
      rb = RoundedRectangle(pos=red_btn.pos, size=red_btn.size, radius=[dp(20)])
    red_btn.bind(pos=lambda w, v, r=rb: setattr(r, 'pos', v),
           size=lambda w, v, r=rb: setattr(r, 'size', v))
    red_btn.bind(on_press=lambda x: self._bet("red"))
    field.add_widget(red_btn)
    black_btn = Button(text="ЧЁРНОЕ\nx2", font_size=dp(18), bold=True,
              background_normal='', background_down='',
              background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
    with black_btn.canvas.before:
      Color(0.1, 0.1, 0.15, 0.98)
      bb = RoundedRectangle(pos=black_btn.pos, size=black_btn.size, radius=[dp(20)])
    black_btn.bind(pos=lambda w, v, r=bb: setattr(r, 'pos', v),
            size=lambda w, v, r=bb: setattr(r, 'size', v))
    black_btn.bind(on_press=lambda x: self._bet("black"))
    field.add_widget(black_btn)
    layout.add_widget(field)

    # ЗЕЛЁНОЕ
    green_btn = Button(text="ЗЕЛЁНОЕ x14 (шанс 1/14)", font_size=dp(15), bold=True,
              size_hint_y=None, height=dp(60),
              background_normal='', background_down='',
              background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
    with green_btn.canvas.before:
      Color(0.15, 0.7, 0.25, 0.95)
      gb = RoundedRectangle(pos=green_btn.pos, size=green_btn.size, radius=[dp(20)])
    green_btn.bind(pos=lambda w, v, r=gb: setattr(r, 'pos', v),
            size=lambda w, v, r=gb: setattr(r, 'size', v))
    green_btn.bind(on_press=lambda x: self._bet("green"))
    layout.add_widget(green_btn)

    layout.add_widget(Label(text="Ставка: 100 монет", font_size=dp(12),
                size_hint_y=None, height=dp(24),
                color=(0.85, 0.85, 0.9, 1)))
    self.history_lbl = Label(text="История: —", font_size=dp(12),
                  size_hint_y=None, height=dp(50),
                  color=(0.85, 0.85, 0.9, 1),
                  halign='center', valign='middle')
    self.history_lbl.bind(size=lambda s, v: setattr(s, 'text_size', (v[0], None)))
    layout.add_widget(self.history_lbl)
    btn_back = GlassButton(text="Назад", height=dp(46))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'fun'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def _bet(self, color):
    if self.spinning: return
    data = load_data()
    coins = data.get("coins", 0)
    BET = 100
    if coins < BET:
      self.result_lbl.text = "Не хватает монет (нужно 100)"
      self.result_lbl.color = (1, 0.4, 0.4, 1); return
    data["coins"] = coins - BET
    save_data(data)
    self.coins_lbl.text = f"Монеты: {data['coins']}"
    roll = random.random()
    if roll < 1/14: result_color = "green"
    elif roll < 1/14 + 7/14: result_color = "red"
    else: result_color = "black"
    self.spinning = True
    if result_color == color:
      win = BET * 14 if color == "green" else BET * 2
      data = load_data()
      data["coins"] = data.get("coins", 0) + win
      data["casino_wins"] = data.get("casino_wins", 0) + 1
      save_data(data)
      self.coins_lbl.text = f"Монеты: {data['coins']}"
      self.result_lbl.text = f"ВЫПАЛО: {self._ru(result_color)} — ВЫИГРЫШ +{win}!"
      self.result_lbl.color = (0.3, 1, 0.4, 1)
    else:
      self.result_lbl.text = f"ВЫПАЛО: {self._ru(result_color)} — Проигрыш -{BET}"
      self.result_lbl.color = (1, 0.4, 0.4, 1)
    self.spinning = False
    self.history.append(self._ru(result_color))
    if len(self.history) > 8: self.history = self.history[-8:]
    self.history_lbl.text = "История: " + " | ".join(self.history)

  def _ru(self, c):
    return {"red": "КРАСНОЕ", "black": "ЧЁРНОЕ", "green": "ЗЕЛЁНОЕ"}.get(c, "?")

  def on_pre_enter(self, *args):
    data = load_data()
    self.coins_lbl.text = f"Монеты: {data.get('coins', 0)}"


# ============================================================
# ОХОТА ЗА СОКРОВИЩАМИ (ФИКС интерфейса)
# ============================================================
class TreasureHuntScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "spiral")
    self.add_widget(self.bg_widget)
    self.treasures = []; self.opened = 0

    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(6))
    layout.add_widget(Label(text="Охота за сокровищами", font_size=dp(20), bold=True,
                size_hint_y=None, height=dp(32)))
    self.info_lbl = Label(text="Открывай сундуки!",
                font_size=dp(12), size_hint_y=None, height=dp(22))
    layout.add_widget(self.info_lbl)
    self.coins_lbl = Label(text="", font_size=dp(14), bold=True,
                size_hint_y=None, height=dp(24),
                color=(1, 0.85, 0.4, 1))
    layout.add_widget(self.coins_lbl)
    self.result_lbl = Label(text="", font_size=dp(13), bold=True,
                 size_hint_y=None, height=dp(26),
                 color=(1, 1, 1, 1), halign='center', valign='middle')
    self.result_lbl.bind(size=lambda s, v: setattr(s, 'text_size', (v[0], None)))
    layout.add_widget(self.result_lbl)

    # ФИКС: фиксированная высота поля, кнопка Назад снизу
    self.grid_holder = FloatLayout(size_hint_y=None, height=dp(320))
    layout.add_widget(self.grid_holder)
    layout.add_widget(Label(text="", size_hint_y=None, height=dp(4)))
    btn_back = GlassButton(text="Назад", height=dp(46))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'fun'))
    layout.add_widget(btn_back)
    self.add_widget(layout)
    Clock.schedule_once(self._start_game, 0.3)

  def _start_game(self, dt):
    if self.grid_holder.width < 50:
      Clock.schedule_once(self._start_game, 0.2); return
    data = load_data()
    data["coins"] = data.get("coins", 0) - 500
    save_data(data)
    self.coins_lbl.text = f"Монеты: {data.get('coins', 0)}"
    self.opened = 0
    for b in self.treasures:
      try: self.grid_holder.remove_widget(b)
      except: pass
    self.treasures = []
    cols, rows = 5, 4
    pad = dp(5)
    W = self.grid_holder.width; H = self.grid_holder.height
    cell_w = (W - pad * (cols + 1)) / cols
    cell_h = (H - pad * (rows + 1)) / rows
    cell_size = min(cell_w, cell_h)
    positions = list(range(20)); random.shuffle(positions)
    prize_positions = set(positions[:10])
    prizes = [50, 80, 120, 200, 350, 500, 800, 1200, 1500, 2000]
    random.shuffle(prizes)
    for r in range(rows):
      for c in range(cols):
        idx = r * cols + c
        btn = Button(text="?", font_size=dp(18), bold=True,
               size_hint=(None, None), size=(cell_size, cell_size),
               background_normal='', background_down='',
               background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
        with btn.canvas.before:
          Color(0.4, 0.3, 0.15, 0.9)
          b = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(8)])
        btn.bind(pos=lambda w, v, r=b: setattr(r, 'pos', v),
             size=lambda w, v, r=b: setattr(r, 'size', v))
        btn.x = pad + c * (cell_w + pad) + (cell_w - cell_size) / 2
        btn.y = H - pad - (r + 1) * (cell_h + pad) + (cell_h - cell_size) / 2 + pad
        btn._is_prize = idx in prize_positions
        btn._prize_amount = prizes.pop() if btn._is_prize else 0
        btn._opened = False
        btn.bind(on_press=lambda x: self._open(x))
        self.grid_holder.add_widget(btn)
        self.treasures.append(btn)
    self.result_lbl.text = "Открывай сундуки!"

  def _open(self, btn):
    if getattr(btn, "_opened", False): return
    btn._opened = True
    self.opened += 1
    if btn._is_prize:
      btn.text = f"+{btn._prize_amount}"
      for c in btn.canvas.before.children:
        if isinstance(c, Color): c.rgba = (0.2, 0.8, 0.3, 0.95)
      data = load_data()
      data["coins"] = data.get("coins", 0) + btn._prize_amount
      save_data(data)
      self.coins_lbl.text = f"Монеты: {data.get('coins', 0)}"
      self.result_lbl.text = f"Нашёл {btn._prize_amount} монет!"
    else:
      btn.text = "X"
      for c in btn.canvas.before.children:
        if isinstance(c, Color): c.rgba = (0.3, 0.15, 0.1, 0.9)
      self.result_lbl.text = "Пусто..."
    if self.opened >= 20:
      self.result_lbl.text = "Игра окончена! Нажми «Начать заново»"
      self._show_restart()

  def _show_restart(self):
    if hasattr(self, '_restart_btn'): return
    btn = Button(text="Начать заново (500 монет)", font_size=dp(14), bold=True,
           size_hint=(None, None), size=(dp(280), dp(46)),
           pos_hint={'center_x': 0.5, 'y': 0.06},
           background_normal='', background_down='',
           background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
    with btn.canvas.before:
      Color(0.4, 0.7, 0.5, 0.95)
      b = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(20)])
    btn.bind(pos=lambda w, v, r=b: setattr(r, 'pos', v),
         size=lambda w, v, r=b: setattr(r, 'size', v))
    btn.bind(on_press=self._restart)
    self.add_widget(btn)
    self._restart_btn = btn

  def _restart(self, *args):
    if hasattr(self, '_restart_btn'):
      try: self.remove_widget(self._restart_btn)
      except: pass
      delattr(self, '_restart_btn')
    self._start_game(0)

  def on_pre_enter(self, *args):
    data = load_data()
    self.coins_lbl.text = f"Монеты: {data.get('coins', 0)}"


# ============================================================
# ЕЖЕДНЕВНЫЕ ЗАДАНИЯ (новый способ MMR и монет)
# ============================================================
class QuestsScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "corners")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Ежедневные задания", font_size=dp(22), bold=True,
                size_hint_y=None, height=dp(36)))
    data = load_data()
    self.coins_lbl = Label(text=f"Монеты: {data.get('coins', 0)}",
                font_size=dp(14), size_hint_y=None, height=dp(24))
    layout.add_widget(self.coins_lbl)
    scroll = ScrollView(size_hint=(1, 1))
    inner = BoxLayout(orientation='vertical', spacing=dp(10),
              size_hint_y=None, padding=dp(6))
    inner.bind(minimum_height=inner.setter('height'))
    claimed = data.get("claimed_quests", [])

    for q in DAILY_QUESTS:
      current = data.get(q["progress_key"], 0)
      target = q["target"]
      done = current >= target
      is_claimed = q["id"] in claimed

      card = BoxLayout(orientation='vertical', size_hint_y=None,
               height=dp(120), padding=dp(10), spacing=dp(4))
      with card.canvas.before:
        Color(1, 1, 1, 0.08)
        bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(15)])
      card.bind(pos=lambda w, v, r=bg: setattr(r, 'pos', v),
           size=lambda w, v, r=bg: setattr(r, 'size', v))

      card.add_widget(Label(text=q["label"], font_size=dp(15), bold=True,
                  color=(1, 1, 1, 1), size_hint_y=None, height=dp(24)))
      card.add_widget(Label(text=f"Прогресс: {min(current, target)}/{target}",
                  font_size=dp(13), color=(0.85, 0.85, 0.9, 1),
                  size_hint_y=None, height=dp(20)))
      card.add_widget(Label(text=f"Награда: {q['reward_coins']} монет + {q['reward_mmr']} MMR",
                  font_size=dp(12), color=(1, 0.85, 0.4, 1),
                  size_hint_y=None, height=dp(20)))

      if is_claimed:
        card.add_widget(Label(text=" Получено", font_size=dp(13), bold=True,
                    color=(0.4, 0.9, 0.5, 1), size_hint_y=None, height=dp(26)))
      elif done:
        btn = Button(text="Забрать награду", font_size=dp(13), bold=True,
               size_hint_y=None, height=dp(30),
               background_normal='', background_down='',
               background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
        with btn.canvas.before:
          Color(0.4, 0.75, 0.45, 0.95)
          b = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])
        btn.bind(pos=lambda w, v, r=b: setattr(r, 'pos', v),
             size=lambda w, v, r=b: setattr(r, 'size', v))
        btn.bind(on_press=lambda x, qq=q: self._claim(qq))
        card.add_widget(btn)
      else:
        card.add_widget(Label(text="Не выполнено", font_size=dp(12),
                    color=(0.7, 0.7, 0.75, 1),
                    size_hint_y=None, height=dp(26)))
      inner.add_widget(card)

    scroll.add_widget(inner)
    layout.add_widget(scroll)
    btn_back = GlassButton(text="Назад", height=dp(50))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def _claim(self, q):
    data = load_data()
    claimed = data.get("claimed_quests", [])
    if q["id"] in claimed: return
    current = data.get(q["progress_key"], 0)
    if current < q["target"]: return
    data["coins"] = data.get("coins", 0) + q["reward_coins"]
    data["mmr"] = data.get("mmr", 0) + q["reward_mmr"]
    claimed.append(q["id"])
    data["claimed_quests"] = claimed
    save_data(data)
    self._build_ui()

  def on_pre_enter(self, *args):
    self._build_ui()


# ============================================================
# РЫНОК (продажа/покупка скинов)
# ============================================================
class MarketScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "waves")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Рынок скинов", font_size=dp(22), bold=True,
                size_hint_y=None, height=dp(36)))
    data = load_data()
    self.coins_lbl = Label(text=f"Монеты: {data.get('coins', 0)}",
                font_size=dp(14), size_hint_y=None, height=dp(24))
    layout.add_widget(self.coins_lbl)
    layout.add_widget(Label(text="Случайные лоты — 500 монет за 1",
                font_size=dp(12), size_hint_y=None, height=dp(20),
                color=(0.85, 0.85, 0.9, 1)))

    scroll = ScrollView(size_hint=(1, 1))
    inner = BoxLayout(orientation='vertical', spacing=dp(8),
              size_hint_y=None, padding=dp(4))
    inner.bind(minimum_height=inner.setter('height'))

    # 6 лотов — случайные предметы за 500 монет
    lot_pool = [
      ("cat", "gold"), ("knives", "karambit_ruby"), ("spiders", "galaxy"),
      ("guns", "dragon_lore"), ("rainbow", "rainbow_neon"),
      ("fish", "arctic_char"), ("fur", "golden_panther"),
      ("minerals", "meteorite"), ("mushrooms", "glow"),
    ]
    seed = data.get("market_seed", random.randint(0, 9999))
    rng = random.Random(seed)
    lots = rng.sample(lot_pool, 6)
    for item_type, kind in lots:
      price = int(get_price(item_type, kind) * 1.5)
      card = BoxLayout(orientation='horizontal', size_hint_y=None,
               height=dp(90), padding=dp(8), spacing=dp(8))
      with card.canvas.before:
        Color(1, 1, 1, 0.08)
        bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
      card.bind(pos=lambda w, v, r=bg: setattr(r, 'pos', v),
           size=lambda w, v, r=bg: setattr(r, 'size', v))
      art_holder = FloatLayout(size_hint_x=None, width=dp(70))
      art = make_art(item_type, kind, dp(60))
      if art is not None:
        art.size_hint = (None, None); art.size = (dp(60), dp(60))
        art.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        art_holder.add_widget(art)
      card.add_widget(art_holder)
      info = BoxLayout(orientation='vertical', spacing=dp(2))
      info.add_widget(Label(text=get_name(item_type, kind), font_size=dp(13), bold=True,
                  color=(1, 1, 1, 1), size_hint_y=None, height=dp(22)))
      info.add_widget(Label(text=f"Цена: {price}м", font_size=dp(11),
                  color=(1, 0.85, 0.4, 1), size_hint_y=None, height=dp(20)))
      card.add_widget(info)
      buy = Button(text="Купить", font_size=dp(12), bold=True,
             size_hint=(None, None), size=(dp(80), dp(40)),
             background_normal='', background_down='',
             background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
      with buy.canvas.before:
        Color(0.4, 0.7, 0.5, 0.95)
        b = RoundedRectangle(pos=buy.pos, size=buy.size, radius=[dp(12)])
      buy.bind(pos=lambda w, v, r=b: setattr(r, 'pos', v),
           size=lambda w, v, r=b: setattr(r, 'size', v))
      buy.bind(on_press=lambda x, t=item_type, k=kind, p=price: self._buy(t, k, p))
      card.add_widget(buy)
      inner.add_widget(card)

    scroll.add_widget(inner)
    layout.add_widget(scroll)

    refresh = GlassButton(text="Обновить лоты", height=dp(44))
    refresh.bind(on_press=self._refresh)
    layout.add_widget(refresh)
    btn_back = GlassButton(text="Назад", height=dp(46))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def _refresh(self, *args):
    data = load_data()
    data["market_seed"] = random.randint(0, 9999)
    save_data(data)
    self._build_ui()

  def _buy(self, item_type, kind, price):
    data = load_data()
    if data.get("coins", 0) < price: return
    data["coins"] -= price
    inv = data.get("inventory", [])
    inv.append({"type": item_type, "kind": kind, "case": "market"})
    data["inventory"] = inv
    save_data(data)
    self._build_ui()

  def on_pre_enter(self, *args):
    self._build_ui()


# ============================================================
# РАЗВЛЕЧЕНИЯ
# ============================================================
class FunScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = AnimatedBg(load_data().get("wallpaper_theme", "fire"), "corners")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
    layout.add_widget(Label(text="Развлечения", font_size=dp(26), bold=True,
                size_hint_y=None, height=dp(40)))
    self.coins_lbl = Label(text="", font_size=dp(14), size_hint_y=None, height=dp(26))
    layout.add_widget(self.coins_lbl)
    layout.add_widget(Label(text="", size_hint_y=None, height=dp(10)))
    for text, target, sub in [
      ("Тир", "shooter", "Попади в 5 мишеней → +50 MMR"),
      ("Казино", "casino", "Красно-чёрное и зелёное x14"),
      ("Охота за сокровищами", "treasure", "500 монет → ищи клад в сундуках"),
      ("Задания", "quests", "Ежедневные квесты — монеты + MMR"),
      ("Рынок скинов", "market", "Покупай редкие скины за монеты"),
    ]:
      btn = GlassButton(text=text, height=dp(56))
      btn.bind(on_press=lambda x, t=target: setattr(self.manager, 'current', t))
      layout.add_widget(btn)
      layout.add_widget(Label(text=sub, font_size=dp(11),
                   size_hint_y=None, height=dp(18),
                   color=(0.85, 0.85, 0.9, 1)))
    layout.add_widget(Label(text="", size_hint_y=None, height=dp(10)))
    btn_back = GlassButton(text="Назад", height=dp(50))
    btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def on_pre_enter(self, *args):
    data = load_data()
    self.coins_lbl.text = f"Монеты: {data.get('coins', 0)}"


# ============================================================
# ИГРА
# ============================================================
class GamesApp(App):
  def build(self):
    root = FloatLayout()
    sm = ScreenManager()
    sm.transition = FadeTransition(duration=0.3)
    sm.size_hint = (1, 1); sm.pos_hint = {'x': 0, 'y': 0}
    sm.add_widget(MainMenuScreen(name='main'))
    sm.add_widget(ClickerScreen(name='clicker'))
    sm.add_widget(ThemeSelectScreen(name='theme'))
    sm.add_widget(WallpaperSelectScreen(name='wallpaper'))
    sm.add_widget(CasesScreen(name='cases'))
    sm.add_widget(CaseScreen(name='box'))
    sm.add_widget(InventoryScreen(name='inventory'))
    sm.add_widget(RanksScreen(name='ranks'))
    sm.add_widget(ProfileScreen(name='profile'))
    sm.add_widget(DailyRewardScreen(name='daily_reward'))
    sm.add_widget(ShopScreen(name='shop'))
    sm.add_widget(RankSelectScreen(name='rank_select'))
    sm.add_widget(AvatarSelectScreen(name='avatar_select'))
    sm.add_widget(FramesScreen(name='frames'))
    sm.add_widget(FramesInventoryScreen(name='frames_inventory'))
    sm.add_widget(AvatarsInventoryScreen(name='avatars_inventory'))
    sm.add_widget(NicknameScreen(name='nickname'))
    sm.add_widget(TargetShooterScreen(name='shooter'))
    sm.add_widget(CasinoScreen(name='casino'))
    sm.add_widget(TreasureHuntScreen(name='treasure'))
    sm.add_widget(FunScreen(name='fun'))
    sm.add_widget(QuestsScreen(name='quests'))
    sm.add_widget(MarketScreen(name='market'))
    root.add_widget(sm)
    return root


if __name__ == "__main__":
  GamesApp().run()
