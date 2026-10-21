import kivy
from kivy.config import Config
# Лимит кадров: 60 FPS (реальная частота зависит от устройства).
Config.set("graphics", "maxfps", "60")
kivy.require('2.0.0')

import os
import sys
import uuid
import wave, struct
import math
import random
import colorsys
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
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse, Line, Triangle, PushMatrix, PopMatrix, Scale, StencilPush, StencilUse, StencilUnUse, StencilPop
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition

# Версия приложения (показывается в плашке рядом с названием).
APP_VERSION = "release'3.0.0"


def _data_dir():
  """Папка для сохранений. На Android это постоянное хранилище приложения,
  которое не затирается при обновлении APK; на ПК - папка рядом со скриптом."""
  try:
    from kivy.utils import platform as _platform
    if _platform == 'android':
      from android.storage import app_storage_path
      path = app_storage_path()
      os.makedirs(path, exist_ok=True)
      return path
  except Exception:
    pass
  return os.path.dirname(os.path.abspath(__file__))

DATA_DIR = _data_dir()


# Оригинальные синтезированные звуки CataBox. Не используют чужую музыку/семплы.
class GameAudio:
  _sounds = {}
  _music = None
  _music_started = False
  _base = DATA_DIR

  @classmethod
  def _write_wav(cls, name, samples, rate=22050):
    path = os.path.join(cls._base, name + '.wav')
    if not os.path.exists(path):
      with wave.open(path, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate)
        payload = bytearray()
        for sample in samples:
          payload.extend(struct.pack('<h', max(-32767, min(32767, int(sample)))))
        wf.writeframes(bytes(payload))
    return path

  @classmethod
  def _ensure(cls):
    if cls._sounds:
      return
    rate = 22050
    # Opening: short airy electronic chime.
    n = int(rate * 0.24); vals=[]
    for i in range(n):
      t=i/rate; env=(1-i/n)**2
      vals.append(7600*env*(math.sin(2*math.pi*(520+900*t)*t)+0.38*math.sin(2*math.pi*(1040+1200*t)*t)))
    open_path=cls._write_wav('catabox_case_open', vals)
    # Spin: soft low whoosh with a rising pitch.
    n = int(rate * 0.62); vals=[]
    for i in range(n):
      t=i/rate; env=min(1,t*8)*(1-t/(n/rate))
      freq=100+420*t
      vals.append(6500*env*(0.7*math.sin(2*math.pi*freq*t)+0.3*math.sin(2*math.pi*freq*1.51*t)))
    spin_path=cls._write_wav('catabox_case_spin', vals)
    # Reveal: warm, short two-note sparkle.
    n = int(rate * 0.34); vals=[]
    for i in range(n):
      t=i/rate; env=math.exp(-t*8)
      f=880 if t<0.13 else 1320
      vals.append(8200*env*(math.sin(2*math.pi*f*t)+0.25*math.sin(2*math.pi*f*2*t)))
    reveal_path=cls._write_wav('catabox_case_reveal', vals)
    for key,path,volume in [('case_open',open_path,0.42),('case_spin',spin_path,0.32),('case_reveal',reveal_path,0.42)]:
      try:
        snd=SoundLoader.load(path)
        if snd: snd.volume=volume
        cls._sounds[key]=snd
      except Exception:
        cls._sounds[key]=None


  @classmethod
  def play(cls, key):
    try:
      cls._ensure(); snd=cls._sounds.get(key)
      if snd:
        snd.stop(); snd.play()
    except Exception:
      pass

  @classmethod
  def start_music(cls):
    # Фоновая музыка отключена по запросу.
    return


# Диагностика вылетов: сохраняем полную ошибку в crash_log.txt.
import traceback

def _save_crash_log(exc_type, exc_value, exc_tb):
    report = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        log_path = os.path.join(DATA_DIR, "crash_log.txt")
        with open(log_path, "w", encoding="utf-8") as log_file:
            log_file.write(report)
    except Exception:
        pass
    print(report, file=sys.stderr)

sys.excepthook = _save_crash_log



BG_FILE = "bg.jpg"
HAS_BG = os.path.exists(BG_FILE)
Window.clearcolor = (0, 0, 0, 1) if HAS_BG else (0.05, 0.05, 0.1, 1)
try:
  Window.softinput_mode = 'below_target'
except Exception:
  pass

try:
  SAVE_FILE = os.path.join(DATA_DIR, "scores.json")
except:
  SAVE_FILE = "scores.json"


# Локальная база аккаунтов SQLite (на этом устройстве, не онлайн-сервер).
import sqlite3, hashlib, json, re
DB_FILE = os.path.join(DATA_DIR, "players.db")
SESSION_FILE = os.path.join(DATA_DIR, "session.json")
ACTIVE_USER = None
# Пароль администратора в коде не хранится - только соленый хэш (PBKDF2).
# Чтобы сменить пароль, выполните в терминале и подставьте результат ниже:
#   python -c "import hashlib,os;s=os.urandom(16);print(s.hex(),hashlib.pbkdf2_hmac('sha256',b'НОВЫЙ_ПАРОЛЬ',s,120000).hex())"
_ADMIN_SALT = bytes.fromhex("a55d2d0a3a93dae474fddf2e5e3f500e")
_ADMIN_HASH = bytes.fromhex("d444a5359029ceaa6846f585c4eed3450f20fb6d18d8e986884fb48c971659f9")
_ADMIN_ITERATIONS = 120000

def _check_admin_password(candidate):
  import hmac
  calc = hashlib.pbkdf2_hmac('sha256', str(candidate).encode('utf-8'), _ADMIN_SALT, _ADMIN_ITERATIONS)
  return hmac.compare_digest(calc, _ADMIN_HASH)

def _ensure_account_ids():
  """Assign stable public IDs to existing local accounts without replacing account data."""
  try:
    c=sqlite3.connect(DB_FILE)
    rows=c.execute("SELECT username,data_json FROM players").fetchall()
    for username, raw in rows:
      try: data=json.loads(raw or "{}")
      except Exception: data={}
      if not data.get("account_id"):
        data["account_id"]=uuid.uuid4().hex[:12].upper()
        c.execute("UPDATE players SET data_json=? WHERE username=?",(json.dumps(data,ensure_ascii=False),username))
    c.commit(); c.close()
  except Exception as e: print("ACCOUNT ID MIGRATION ERROR:",e)

ADMIN_SETTINGS_FILE = os.path.join(DATA_DIR, "admin_settings.json")
DEFAULT_OFFERS = [
  {"id":"winter_avatar", "title":"Зимняя аватарка-подарок", "description":"Уникальная праздничная аватарка для профиля", "emoji":"", "reward_type":"avatar", "reward_kind":"winter_cat"},
  {"id":"snow_case", "title":"Снежный кейс", "description":"Зимняя акция на тематический кейс", "emoji":"", "reward_type":"case", "reward_kind":"ice"},
  {"id":"double_coins", "title":"Двойные монеты", "description":"Праздничный бонус монет", "emoji":"", "reward_type":"coins", "reward_amount":2000},
  {"id":"cat_bundle", "title":"Набор кота-праздника", "description":"Праздничный набор оформления профиля", "emoji":"", "reward_type":"avatar", "reward_kind":"holiday_cat"},
]
def _load_admin_settings():
  try:
    with open(ADMIN_SETTINGS_FILE, encoding="utf-8") as f: data=json.load(f)
    if not isinstance(data, dict): data={}
  except Exception: data={}
  data.setdefault("global_wallpaper", "default")
  if data.get("global_wallpaper") == "newyear": data["global_wallpaper"] = "default"
  data.setdefault("offers", [])
  if not isinstance(data["offers"], list): data["offers"]=[]
  return data
def _save_admin_settings(data):
  try:
    with open(ADMIN_SETTINGS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    return True
  except Exception as e:
    print("ADMIN SETTINGS SAVE ERROR:", e); return False

def _glass_card(widget, color=(0.09,0.12,0.24,0.96), edge=(0.48,0.68,1.0,0.65), radius=dp(22)):
  with widget.canvas.before:
    Color(*color); widget._glass_bg=RoundedRectangle(pos=widget.pos,size=widget.size,radius=[radius])
    Color(*edge); widget._glass_edge=Line(rounded_rectangle=(widget.x,widget.y,widget.width,widget.height,radius),width=dp(1))
  def _sync(*_):
    widget._glass_bg.pos=widget.pos; widget._glass_bg.size=widget.size
    widget._glass_edge.rounded_rectangle=(widget.x,widget.y,widget.width,widget.height,radius)
  widget.bind(pos=_sync,size=_sync)
  return widget

def _open_glass_popup(title, body, size_hint=(.92,.82)):
  from kivy.uix.popup import Popup
  shell=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(8))
  _glass_card(shell)
  heading=Label(text=title,bold=True,font_size=dp(19),size_hint_y=None,height=dp(38),color=(0.95,0.97,1,1))
  shell.add_widget(heading); shell.add_widget(body)
  close=GlassButton(text="Закрыть",height=dp(42)); shell.add_widget(close)
  pop=Popup(title="",content=shell,size_hint=size_hint,background="",background_color=(0,0,0,0),separator_height=0,auto_dismiss=True)
  close.bind(on_press=lambda *_: pop.dismiss())
  pop.open(); pop.opacity=0.0
  Animation(opacity=1.0,duration=.22,t="out_cubic").start(pop)
  return pop

def _admin_tables():
  c = _db()
  c.execute("CREATE TABLE IF NOT EXISTS local_bans (username TEXT PRIMARY KEY COLLATE NOCASE, reason TEXT DEFAULT '', banned_at TEXT DEFAULT CURRENT_TIMESTAMP)")
  c.execute("CREATE TABLE IF NOT EXISTS admin_log (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
  c.commit(); c.close()

def _admin_log(action):
  try:
    _admin_tables()
    c=sqlite3.connect(DB_FILE); c.execute("INSERT INTO admin_log(action) VALUES(?)", (str(action)[:500],)); c.commit(); c.close()
  except Exception as e: print("ADMIN LOG ERROR:", e)

def _is_banned(username):
  try:
    _admin_tables(); c=sqlite3.connect(DB_FILE)
    row=c.execute("SELECT reason FROM local_bans WHERE username=?", (username,)).fetchone(); c.close()
    return row
  except Exception: return None
def _db():
  conn=sqlite3.connect(DB_FILE)
  conn.execute("CREATE TABLE IF NOT EXISTS players (username TEXT PRIMARY KEY COLLATE NOCASE, password_hash TEXT NOT NULL, data_json TEXT NOT NULL DEFAULT '{}', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
  conn.commit(); return conn
def _hash_password(password, salt=None):
  salt=salt or os.urandom(16).hex()
  return salt+"$"+hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),150000).hex()
def _verify_password(password, stored):
  try: return _hash_password(password,stored.split("$",1)[0]).split("$",1)[1] == stored.split("$",1)[1]
  except Exception: return False
def _session_user():
  global ACTIVE_USER
  try:
    with open(SESSION_FILE,encoding="utf-8") as f: ACTIVE_USER=json.load(f).get("username")
  except Exception: ACTIVE_USER=None
  if ACTIVE_USER:
    c=_db(); row=c.execute("SELECT username FROM players WHERE username=?",(ACTIVE_USER,)).fetchone(); c.close()
    if not row: ACTIVE_USER=None
  return ACTIVE_USER
def _set_session(username):
  global ACTIVE_USER; ACTIVE_USER=username
  try:
    with open(SESSION_FILE,"w",encoding="utf-8") as f: json.dump({"username":username},f)
  except Exception: pass
def create_account(username,password):
  username=username.strip()
  if not re.fullmatch(r"[A-Za-zА-Яа-яЁё0-9_]{3,16}",username): return False,"Ник: 3–16 символов, буквы/цифры/_"
  if len(password)<6: return False,"Пароль должен быть не короче 6 символов"
  c=_db()
  try:
    legacy={}
    if os.path.exists(SAVE_FILE):
      try:
        with open(SAVE_FILE,encoding="utf-8") as f: legacy=json.load(f)
      except Exception: pass
    initial=legacy if c.execute("SELECT COUNT(*) FROM players").fetchone()[0]==0 else {}
    initial.setdefault("account_id", uuid.uuid4().hex[:12].upper())
    c.execute("INSERT INTO players(username,password_hash,data_json) VALUES(?,?,?)",(username,_hash_password(password),json.dumps(initial,ensure_ascii=False))); c.commit(); _set_session(username); return True,"Аккаунт создан!"
  except sqlite3.IntegrityError: return False,"Такой аккаунт уже существует"
  finally: c.close()
def login_account(username,password):
  c=_db(); row=c.execute("SELECT username,password_hash FROM players WHERE username=?",(username.strip(),)).fetchone(); c.close()
  if not row or not _verify_password(password,row[1]): return False,"Неверный ник или пароль"
  ban = _is_banned(row[0])
  if ban is not None: return False, "Аккаунт заблокирован" + (": " + ban[0] if ban[0] else "")
  _set_session(row[0]); return True,"Вход выполнен!"
def logout_account(): _set_session(None)
def load_data():
  username=ACTIVE_USER or _session_user()
  if not username: return {}
  c=_db(); row=c.execute("SELECT data_json FROM players WHERE username=?",(username,)).fetchone(); c.close()
  try: return json.loads(row[0] or "{}") if row else {}
  except Exception: return {}
def save_data(data):
  username=ACTIVE_USER or _session_user()
  if not username: return
  try:
    c=_db(); c.execute("UPDATE players SET data_json=? WHERE username=?",(json.dumps(data,ensure_ascii=False),username)); c.commit(); c.close()
  except Exception as e: print("DATABASE SAVE ERROR:",e)


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
# РАНГИ (22 штуки)
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
  # Новые ранги после PRO: каждый следующий требует ещё 1000 MMR.
  ("pro_2", "PRO II", (0.2, 0.9, 1.0), (0.65, 1.0, 1.0)),
  ("pro_3", "PRO III", (0.25, 0.65, 1.0), (0.65, 0.85, 1.0)),
  ("ultra_pro", "ULTRA PRO", (0.65, 0.35, 1.0), (0.85, 0.7, 1.0)),
  ("supreme", "SUPREME", (1.0, 0.25, 0.75), (1.0, 0.65, 0.9)),
  ("godlike", "GODLIKE", (1.0, 0.85, 0.2), (1.0, 1.0, 0.65)),
]


def rank_threshold(index):
  """Порог рангов: Элита открывается на 10000 MMR, далее шаг 1500."""
  index = max(0, int(index))
  elite_index = next(i for i, rank in enumerate(RANKS) if rank[0] == "elite")
  if index < elite_index:
    # Ранги до Элиты постепенно доходят до 10000 MMR.
    return int(round(10000 * index / elite_index)) if index else 0
  if index == elite_index:
    return 10000
  return 10000 + (index - elite_index) * 1500


def rank_index_by_mmr(mmr):
  mmr = max(0, int(mmr))
  current = 0
  for i in range(1, len(RANKS)):
    if mmr >= rank_threshold(i):
      current = i
    else:
      break
  return current


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
  ("neon_frame", "Неоновая", 18000, (0.2, 1.0, 0.85), "diamond"),
  ("shadow_frame", "Теневая", 24000, (0.35, 0.3, 0.55), "legend"),
  ("crystal_frame", "Кристальная", 32000, (0.65, 0.9, 1.0), "diamond"),
  ("toxic_frame", "Токсичная", 38000, (0.55, 1.0, 0.1), "flame"),
  ("void_frame", "Пустотная", 45000, (0.3, 0.1, 0.65), "rainbow"),
  ("aurora_frame", "Северное сияние", 60000, (0.2, 1.0, 0.65), "rainbow"),
  ("dragon_frame", "Драконья", 75000, (1.0, 0.25, 0.12), "legend"),
  ("diamond_frame", "Алмазная", 90000, (0.75, 0.95, 1.0), "legend"),
  ("phantom_frame", "Фантомная", 110000, (0.55, 0.45, 0.9), "flame"),
  ("creator_frame", "Создатель", 150000, (1.0, 0.55, 0.9), "legend"),
]



# ============================================================
# АВАТАРЫ
# ============================================================
AVATARS = [
  ("winter_cat", "Зимний кот в шапке"),
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
  ("comet", "Комета"), ("crystal", "Кристалл"), ("ninja", "Ниндзя"),
]


class WinterAvatarArt(FloatLayout):
  """A simple winter cat avatar with a drawn red winter hat; no emoji fonts."""
  def __init__(self, size, **kwargs):
    super().__init__(size_hint=(None, None), size=(size, size), **kwargs)
    cat = CatArt("orange", size * 0.88)
    cat.size_hint = (None, None); cat.size = (size * 0.88, size * 0.88)
    cat.pos_hint = {"center_x": 0.5, "center_y": 0.43}
    self.add_widget(cat)
    with self.canvas:
      Color(0.82, 0.12, 0.18, 1)
      self.hat = Triangle(points=[])
      Color(0.94, 0.96, 1, 1)
      self.trim = Line(points=[], width=max(2, size * 0.07), cap="round", joint="round")
      self.pom = Ellipse(pos=(0,0), size=(size*0.15,size*0.15))
    self.bind(pos=self._layout_hat, size=self._layout_hat)
    self._layout_hat()
  def _layout_hat(self, *_):
    x,y,w,h=self.x,self.y,self.width,self.height
    self.hat.points=[x+w*.22,y+h*.68, x+w*.72,y+h*.68, x+w*.60,y+h*.92]
    self.trim.points=[x+w*.20,y+h*.68, x+w*.73,y+h*.68]
    self.pom.pos=(x+w*.53,y+h*.86)

def avatar_to_art(av_key, size):
  if av_key == "winter_cat":
    return WinterAvatarArt(size)
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
  # Keep catalog avatars visually distinct; unknown keys get a neutral icon, not an orange cat.
  if av_key in ("moon", "comet", "crystal", "phoenix", "ninja", "samurai", "cyber_cat", "shark", "octopus", "raccoon", "owl", "ghost", "dragon", "unicorn", "robot", "alien", "slime"):
    return EmojiAvatarArt(av_key, size)
  return EmojiAvatarArt(av_key, size)


class EmojiAvatarArt(Label):
  # No emoji glyphs: these fallback catalog icons use short text labels so Android
  # devices without emoji fonts do not substitute the same unrelated cat texture.
  LABELS = {"moon":"MO", "comet":"CO", "crystal":"CR", "phoenix":"PH", "ninja":"NJ", "samurai":"SA", "cyber_cat":"CC", "shark":"SH", "octopus":"OC", "raccoon":"RA", "owl":"OW", "ghost":"GH", "dragon":"DR", "unicorn":"UN", "robot":"RB", "alien":"AL", "slime":"SL", "fox":"FX", "wolf":"WF", "tiger":"TG", "panda":"PD", "rose":"RS", "sunflower":"SF", "lotus":"LT", "gold_mineral":"AU", "meteorite":"MT", "glow":"GL"}
  COLORS = {"moon":(0.55,0.62,0.95,1), "comet":(0.35,0.82,0.95,1), "crystal":(0.45,0.9,0.95,1), "phoenix":(0.98,0.52,0.22,1), "ninja":(0.65,0.5,0.95,1), "samurai":(0.95,0.4,0.35,1), "cyber_cat":(0.4,0.85,0.9,1), "shark":(0.35,0.65,0.85,1), "octopus":(0.75,0.45,0.85,1), "raccoon":(0.65,0.7,0.78,1), "owl":(0.85,0.65,0.3,1), "ghost":(0.7,0.8,0.95,1), "dragon":(0.35,0.8,0.55,1), "unicorn":(0.9,0.55,0.8,1), "robot":(0.6,0.7,0.8,1), "alien":(0.4,0.85,0.5,1), "slime":(0.45,0.8,0.45,1)}
  def __init__(self, key, size, **kwargs):
    self.key = key
    super().__init__(text=self.LABELS.get(key, str(key[:2]).upper()), font_size=size*0.27, bold=True, color=(1,1,1,1), halign="center", valign="middle", **kwargs)
    self.size_hint=(None,None); self.size=(size,size)
    self.bind(size=lambda w,v:setattr(w,"text_size",v))
    with self.canvas.before:
      from kivy.graphics import Color, Ellipse
      Color(*self.COLORS.get(key, (0.42,0.48,0.72,1)))
      self._avatar_disc = Ellipse(pos=self.pos, size=self.size)
    self.bind(pos=self._sync_disc, size=self._sync_disc)
  def _sync_disc(self, *_):
    self._avatar_disc.pos = self.pos
    self._avatar_disc.size = self.size

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
    try:
      _global_theme = _load_admin_settings().get("global_wallpaper", "default")
      if _global_theme != "default": theme = _global_theme
    except Exception: pass
    # Новогодняя тема удалена; старые сохранённые значения заменяем стандартными.
    if theme == "newyear": theme = "sun"
    self.theme = theme; self.style = style
    self.time = 0.0
    self.stars = []; self.orbs = []; self.particles = []; self.lines = []; self.mushroom_particles = []
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
        # Плавающие мини-символы для каждой темы: цвет и форма подстраиваются под обои.
        # Грибы сохраняют отдельную узнаваемую анимацию; другим темам добавляем
        # мягкие светящиеся лепестки/осколки вместо одинаковых круглых точек.
        if theme == "mushrooms":
          cap_palette = [(0.95, 0.28, 0.48), (0.68, 0.35, 0.95), (0.95, 0.55, 0.22), (0.35, 0.75, 0.95)]
          for i in range(17):
            cap_rgb = cap_palette[i % len(cap_palette)]
            cap_c = Color(cap_rgb[0], cap_rgb[1], cap_rgb[2], 0.85)
            cap = Ellipse(pos=(0, 0), size=(0, 0))
            stem_c = Color(0.95, 0.86, 0.78, 0.88)
            stem = RoundedRectangle(pos=(0, 0), size=(0, 0), radius=[dp(2)])
            spot_c = Color(1, 0.94, 0.88, 0.8)
            spot = Ellipse(pos=(0, 0), size=(0, 0))
            self.mushroom_particles.append([cap_c, cap, stem_c, stem, spot_c, spot,
                random.uniform(0.04, 0.96), random.random(), random.uniform(0.55, 1.05),
                random.uniform(0.025, 0.065), random.random() * 6.28])
        else:
          for i in range(25):
            pc = self.orb_colors[i % len(self.orb_colors)]
            c = Color(pc[0], pc[1], pc[2], 0.0)
            # Чередуем вытянутые искры и мягкие световые частицы.
            if i % 3 == 0:
              shape = RoundedRectangle(pos=(0, 0), size=(0, 0), radius=[dp(3)])
              shape_type = "spark"
            else:
              shape = Ellipse(pos=(0, 0), size=(0, 0))
              shape_type = "orb"
            self.particles.append([c, shape, random.uniform(0.03, 0.97), random.random(),
                random.uniform(0.3, 1.5), random.random() * 6.28, shape_type])
      elif style == "particles_up":
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

    self._holiday_snow=[]
    if self.theme == "newyear":
      with self.canvas.before:
        Color(0.10,0.43,0.26,0.98); self._tree1=Triangle(points=[])
        Color(0.08,0.35,0.21,0.99); self._tree2=Triangle(points=[])
        Color(0.05,0.26,0.15,1); self._tree3=Triangle(points=[])
        Color(0.43,0.22,0.10,1); self._tree_trunk=Rectangle(pos=(0,0),size=(0,0))
        Color(1.0,0.78,0.18,1); self._tree_star=Ellipse(pos=(0,0),size=(0,0))
        Color(0.92,0.17,0.28,1); self._gift1=RoundedRectangle(pos=(0,0),size=(0,0),radius=[dp(4)])
        Color(0.18,0.56,0.96,1); self._gift2=RoundedRectangle(pos=(0,0),size=(0,0),radius=[dp(4)])
        Color(1.0,0.73,0.16,1); self._gift3=RoundedRectangle(pos=(0,0),size=(0,0),radius=[dp(4)])
        # Детализированные снежинки: мягкая основа и шесть тонких лучей.
        for i in range(18):
          size=dp(random.uniform(2.5,4.0))
          Color(0.88,0.95,1.0,random.uniform(0.65,0.98))
          flake=Ellipse(pos=(0,0),size=(size,size))
          Color(0.98,1.0,1.0,0.9)
          rays=[]
          for j in range(2):
            ray=Line(points=[],width=dp(0.55),cap='round')
            rays.append(ray)
          self._holiday_snow.append([flake,rays,random.random(),random.random(),random.uniform(.035,.10),size])
    self.bind(pos=self._upd, size=self._upd)
    self._ev = Clock.schedule_interval(self._tick, 1.0 / 30.0)
    Clock.schedule_once(lambda dt:self._upd(),0)

  def _upd(self, *args):
    self.bg_rect.pos = self.pos; self.bg_rect.size = self.size
    # Облегчённые новогодние обои: только небольшое количество снежинок.
    W, H = self.width, self.height
    if W < 10 or H < 10: return
    if self.theme == "mushrooms" and self.style == "particles_up":
      for cap_c, cap, stem_c, stem, spot_c, spot, x_f, y_f, scale, speed, phase in self.mushroom_particles:
        y_floating = (y_f - self.time * speed) % 1.08 - 0.04
        x = x_f * W + math.sin(self.time * 0.65 + phase) * W * 0.025
        bob = math.sin(self.time * 1.7 + phase) * dp(2)
        w = dp(28) * scale
        h = dp(17) * scale
        stem_w = w * 0.25
        stem_h = h * 0.78
        base_y = y_floating * H + bob
        stem.pos = (x - stem_w / 2, base_y - stem_h * 0.65)
        stem.size = (stem_w, stem_h)
        cap.pos = (x - w / 2, base_y + stem_h * 0.05)
        cap.size = (w, h)
        spot.pos = (x - w * 0.18, base_y + h * 0.38)
        spot.size = (max(dp(2), w * 0.13), max(dp(2), h * 0.18))
        alpha = 0.65 + 0.25 * math.sin(self.time * 1.2 + phase)
        cap_c.a = alpha
        stem_c.a = min(0.95, alpha + 0.1)
        spot_c.a = alpha
    elif self.style == "particles_up":
      for p in self.particles:
        c, e, x_f, y_f, speed, phase, *extra = p
        y = (y_f - self.time * speed * 0.08) % 1.0
        x = x_f + 0.025 * math.sin(self.time * 0.55 + phase)
        pulse = 0.5 + 0.5 * math.sin(self.time * 1.3 + phase)
        c.a = 0.22 + 0.42 * pulse
        if extra and extra[0] == "spark":
          w = dp(3.0 + 1.8 * pulse); h = dp(8.0 + 4.0 * pulse)
          e.pos = (x * W - w / 2, y * H - h / 2); e.size = (w, h)
        else:
          r = dp(2.0 + 2.0 * pulse)
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
        c.rgba = (pc[0], pc[1], pc[2], 0.4)

  def _tick(self, dt):
    """Обновление анимированного фона и облегчённого новогоднего снега."""
    self.time += min(dt, 0.08)
    if self.theme == "newyear" and self._holiday_snow:
      W, H = self.width, self.height
      if W > 1 and H > 1:
        for item in self._holiday_snow:
          flake, rays, fx, fy, speed, size = item
          fy -= speed * dt
          fx += math.sin(self.time * 1.2 + fy * 7) * dt * 0.012
          if fy < -0.03:
            fy = 1.03
            fx = random.random()
          if fx < -0.02:
            fx = 1.02
          elif fx > 1.02:
            fx = -0.02
          item[2] = fx
          item[3] = fy
          cx, cy = self.x + fx * W, self.y + fy * H
          flake.pos = (cx - size / 2, cy - size / 2)
          # Две пересекающиеся линии дают простую форму снежинки.
          arm = size * 1.8
          rays[0].points = [cx - arm, cy, cx + arm, cy]
          rays[1].points = [cx, cy - arm, cx, cy + arm]
    self._upd()

# ============================================================
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
      self.texture_lines = [Line(points=[], 
