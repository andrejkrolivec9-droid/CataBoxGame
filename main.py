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
import time
import weakref
import colorsys
import threading
import urllib.request
import urllib.error
import urllib.parse
import ssl
try:
  import certifi
  SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
  SSL_CTX = ssl.create_default_context()
from datetime import date, timedelta, datetime
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

# У всех Popup отключаем стандартную текстуру-плашку Kivy: она часто видна
# прямоугольником под кнопками/контентом. Оформление задаётся содержимым окна.
try:
  from kivy.uix.popup import Popup as _KivyPopup
  _popup_init_original = _KivyPopup.__init__
  def _theme_popup_init(self, **kwargs):
    kwargs.setdefault("background", "")
    kwargs.setdefault("background_color", (0, 0, 0, 0))
    kwargs.setdefault("separator_height", 0)
    _popup_init_original(self, **kwargs)
  _KivyPopup.__init__ = _theme_popup_init
except Exception:
  pass

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
    # Дуэль памяти: у каждого цвета свой тон (до-ми-соль-до), плюс сигналы ошибки, победы и монет.
    def tone(name, freq, dur=0.30, vol=7000, decay=7.0):
      n = int(rate * dur); out = []
      for i in range(n):
        t = i / rate; env = min(1.0, t * 60) * math.exp(-t * decay)
        out.append(vol * env * (math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * freq * 2 * t)))
      return cls._write_wav(name, out)
    pad_paths = [tone('catabox_pad%d' % i, f) for i, f in enumerate((262, 330, 392, 523))]
    n = int(rate * 0.45); vals = []
    for i in range(n):
      t = i / rate; env = (1 - i / n) ** 1.5
      vals.append(6800 * env * (math.sin(2 * math.pi * 110 * t) + 0.6 * math.sin(2 * math.pi * 117 * t) + 0.3 * math.sin(2 * math.pi * 220 * t)))
    wrong_path = cls._write_wav('catabox_wrong', vals)
    vals = []
    for note in (523, 659, 784, 1047):
      m = int(rate * 0.11)
      for i in range(m):
        t = i / rate; vals.append(7600 * math.exp(-t * 9) * math.sin(2 * math.pi * note * t))
    win_path = cls._write_wav('catabox_win', vals)
    coin_path = tone('catabox_coin', 1175, dur=0.26, vol=6800, decay=9.0)
    extra_sounds = [('pad%d' % i, pad_paths[i], 0.55) for i in range(4)] + [('wrong', wrong_path, 0.45), ('win', win_path, 0.45), ('coin', coin_path, 0.4)]
    for key,path,volume in [('case_open',open_path,0.42),('case_spin',spin_path,0.32),('case_reveal',reveal_path,0.42)] + extra_sounds:
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


# CataBox Online — безопасный клиент Supabase.
# Здесь разрешён только публичный publishable key. НИКОГДА не добавляйте service_role/secret key в APK.
SUPABASE_URL = "https://hphszmnahbicgjnqyuhk.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_5lfKDpp6mYndIz-M-EAoXg_1BAvWM3W"
SUPABASE_PROFILES_TABLE = "player_profiles"
SUPABASE_AUTH_SESSION_FILE = os.path.join(DATA_DIR, "supabase_session.json")


def _supabase_request(path, payload=None, access_token=None, timeout=8):
  """Small stdlib-only Supabase REST/Auth client; compatible with Android/Kivy."""
  url = SUPABASE_URL.rstrip("/") + path
  headers = {"apikey": SUPABASE_PUBLISHABLE_KEY, "Accept": "application/json"}
  if payload is not None:
    headers["Content-Type"] = "application/json"
  if access_token:
    headers["Authorization"] = "Bearer " + access_token
  else:
    headers["Authorization"] = "Bearer " + SUPABASE_PUBLISHABLE_KEY
  body = json.dumps(payload).encode("utf-8") if payload is not None else None
  req = urllib.request.Request(url, data=body, headers=headers, method="POST" if body is not None else "GET")
  try:
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as response:
      raw = response.read().decode("utf-8", "replace")
      return (json.loads(raw) if raw else {}), None
  except urllib.error.HTTPError as exc:
    try: detail = json.loads(exc.read().decode("utf-8", "replace"))
    except Exception: detail = {}
    msg = detail.get("msg") or detail.get("message") or detail.get("error_description") or detail.get("error") or ("HTTP " + str(exc.code))
    return None, str(msg)[:220]
  except Exception as exc:
    if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower():
      return None, "Сервер не ответил за 8 секунд. Проверь интернет и повтори попытку."
    return None, "Не удалось связаться с Supabase: " + type(exc).__name__ + " " + str(exc)[:160]


def _jwt_exp(token):
  """Время истечения токена (unix), 0 если не удалось прочитать."""
  try:
    import base64
    part = str(token).split(".")[1]
    part += "=" * (-len(part) % 4)
    return int(json.loads(base64.urlsafe_b64decode(part.encode())).get("exp", 0))
  except Exception:
    return 0


def _supabase_session(force_refresh=False):
  """Возвращает (token, user_id). Если токен скоро истекает, обновляет его по refresh_token."""
  try:
    with open(SUPABASE_AUTH_SESSION_FILE, encoding="utf-8") as f: session = json.load(f)
  except Exception:
    return None, None
  token = session.get("access_token"); user_id = session.get("user_id")
  if not token or not user_id: return None, None
  if force_refresh or _jwt_exp(token) - time.time() < 120:
    refresh = session.get("refresh_token")
    if not refresh: return None, None
    result, error = _supabase_request("/auth/v1/token?grant_type=refresh_token", {"refresh_token": refresh})
    if error or not isinstance(result, dict) or not result.get("access_token"):
      return None, None
    session["access_token"] = result["access_token"]
    session["refresh_token"] = result.get("refresh_token", refresh)
    try:
      with open(SUPABASE_AUTH_SESSION_FILE, "w", encoding="utf-8") as f: json.dump(session, f)
    except Exception: pass
    token = session["access_token"]
  return token, user_id


def _clear_online_session():
  try: os.remove(SUPABASE_AUTH_SESSION_FILE)
  except Exception: pass


def _supabase_account_status(timeout=6):
  """Читает с сервера свой статус: VIP и бан. Возвращает (status, error)."""
  token, user_id = _supabase_session()
  if not token: return None, "Нет активной онлайн-сессии"
  url = (SUPABASE_URL.rstrip("/") + "/rest/v1/" + SUPABASE_PROFILES_TABLE
         + "?select=vip,banned,ban_reason&user_id=eq." + urllib.parse.quote(str(user_id)))
  req = urllib.request.Request(url, headers={"apikey": SUPABASE_PUBLISHABLE_KEY,
    "Authorization": "Bearer " + token, "Accept": "application/json"}, method="GET")
  try:
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as response:
      rows = json.loads(response.read().decode("utf-8"))
  except urllib.error.HTTPError as exc:
    if exc.code in (400, 404): return None, "В таблице нет колонок vip/banned/ban_reason"
    return None, "HTTP " + str(exc.code)
  except Exception as exc:
    return None, "Нет связи: " + str(exc)[:100]
  row = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else {}
  return {"vip": bool(row.get("vip", False)), "banned": bool(row.get("banned", False)),
          "reason": str(row.get("ban_reason") or "")[:120]}, None


def _apply_account_status(status):
  """VIP, выданный на сервере, включается и в локальном сохранении. Возвращает True, если что-то изменилось."""
  try:
    if not status or not status.get("vip"): return False
    d = load_data()
    if not d: return False
    if d.get("vip") and int(d.get("tap_boost", 1) or 1) >= 5: return False
    d["vip"] = True
    d["tap_boost"] = max(5, int(d.get("tap_boost", 1) or 1))
    save_data(d)
    return True
  except Exception:
    return False


def _recheck_account_status(screen):
  """Фоновая проверка на главном экране: если игрока забанили, выкидываем на экран входа."""
  def worker():
    status, error = _supabase_account_status()
    if not status: return
    def apply(_dt):
      try:
        if status["banned"]:
          _clear_online_session(); logout_account()
          manager = screen.manager
          manager.current = "auth"
          manager.get_screen("auth").status.text = "Аккаунт заблокирован" + (": " + status["reason"] if status["reason"] else "")
        elif _apply_account_status(status):
          screen._build_ui()
      except Exception as exc:
        print("ACCOUNT STATUS ERROR:", exc)
    Clock.schedule_once(apply, 0)
  threading.Thread(target=worker, daemon=True).start()


def _supabase_auth(action, email, password, nickname=None):
  email = str(email or "").strip().lower()
  if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
    return None, "Введи корректный email"
  if len(password or "") < 6:
    return None, "Пароль должен быть не короче 6 символов"
  if action == "signup":
    chosen = str(nickname or "").strip()
    meta = {"nickname": (chosen or "Игрок" + str(random.randint(1000, 9999)))[:16]}
    if chosen: meta["nick_chosen"] = True
    payload = {"email": email, "password": password, "data": meta}
    result, error = _supabase_request("/auth/v1/signup", payload)
  else:
    result, error = _supabase_request("/auth/v1/token?grant_type=password", {"email": email, "password": password})
  if error:
    low = error.lower()
    if "already registered" in low or "already exists" in low: return None, "Этот email уже зарегистрирован. Нажми «Войти»."
    if "invalid login credentials" in low: return None, "Неверный email или пароль"
    return None, error
  if not isinstance(result, dict): return None, "Неожиданный ответ Supabase"
  session = result.get("session") or result
  token = session.get("access_token") if isinstance(session, dict) else None
  user = result.get("user") or (session.get("user") if isinstance(session, dict) else None)
  if token:
    try:
      with open(SUPABASE_AUTH_SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({"access_token": token, "refresh_token": session.get("refresh_token", ""),
                   "user_id": (user or {}).get("id", ""), "email": email}, f)
    except Exception: pass
  return {"email": email, "token": token, "user": user or {}}, None


def _safe_int(value, default=0, low=0):
  try: return max(low, int(value or default))
  except Exception: return max(low, default)


def _supabase_sync_profile(username, data, timeout=8, expected_user_id=None):
  """Публикует профиль игрока (ник, MMR, монеты, аватар, рамка, шахта, снимок сохранения) под его собственным входом."""
  try:
    token, user_id = _supabase_session()
    if not token or not user_id: return False
    if expected_user_id and expected_user_id != user_id: return False  # игрок успел сменить аккаунт
    base = {"mmr": _safe_int(data.get("mmr")), "coins": _safe_int(data.get("coins")),
            "avatar": str(data.get("avatar", "") or "")[:200], "updated_at": datetime.utcnow().isoformat() + "Z"}
    nick = str(data.get("nickname") or "").strip()
    if len(nick) >= 2: base["nickname"] = nick[:16]
    extra = {"frame": str(data.get("frame", "none") or "none")[:40],
             "mine_level": _safe_int(data.get("mine_level", 1), 1, 1),
             "mine_prestige": _safe_int(data.get("mine_prestige")),
             "cases_opened": _safe_int(data.get("cases_opened")),
             "items_count": len(data.get("inventory", []) or [])}
    snapshot = {k: v for k, v in data.items() if k != "custom_avatar_photo"}
    try:
      if len(json.dumps(snapshot, ensure_ascii=False)) < 900000: extra["save_data"] = snapshot
    except Exception: pass
    url = SUPABASE_URL.rstrip("/") + "/rest/v1/" + SUPABASE_PROFILES_TABLE + "?user_id=eq." + urllib.parse.quote(str(user_id))
    headers = {"apikey": SUPABASE_PUBLISHABLE_KEY, "Authorization": "Bearer " + token,
               "Content-Type": "application/json", "Prefer": "return=minimal"}
    for payload in (dict(base, **extra), base):  # если новых колонок ещё нет, хотя бы базовое уйдёт
      req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="PATCH")
      try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as response: return response.status in (200, 204)
      except urllib.error.HTTPError as exc:
        if exc.code == 400 and payload is not base: continue
        raise
  except Exception as exc:
    print("SUPABASE PROFILE SYNC ERROR:", str(exc)[:180])
    return False


_SYNC_LOCK = threading.Lock()
_SYNC_STATE = {"last": 0.0, "timer": None, "args": None}
SYNC_MIN_INTERVAL = 15  # не чаще одного раза в 15 секунд, чтобы не нагружать сервер


def _session_user_id():
  try:
    with open(SUPABASE_AUTH_SESSION_FILE, encoding="utf-8") as f: return json.load(f).get("user_id")
  except Exception:
    return None


def _fire_profile_sync():
  with _SYNC_LOCK:
    args = _SYNC_STATE["args"]
    _SYNC_STATE["args"] = None; _SYNC_STATE["timer"] = None; _SYNC_STATE["last"] = time.time()
  if args:
    try: _supabase_sync_profile(args[0], json.loads(args[1]), expected_user_id=args[2])
    except Exception as exc: print("SYNC FIRE ERROR:", exc)


def _queue_profile_sync(username, data):
  """Откладывает отправку профиля: самое свежее состояние уходит не чаще раза в 15 секунд."""
  try: raw = json.dumps(data, ensure_ascii=False)
  except Exception: return
  uid = _session_user_id()
  if not uid: return
  with _SYNC_LOCK:
    _SYNC_STATE["args"] = (username, raw, uid)
    if _SYNC_STATE["timer"] is not None: return
    delay = max(0.0, SYNC_MIN_INTERVAL - (time.time() - _SYNC_STATE["last"]))
    timer = threading.Timer(delay, _fire_profile_sync); timer.daemon = True
    _SYNC_STATE["timer"] = timer; timer.start()


def _supabase_fetch_save(timeout=8):
  """Скачивает сохранённый на сервере прогресс (save_data) для восстановления на новом телефоне."""
  token, user_id = _supabase_session()
  if not token: return None
  url = (SUPABASE_URL.rstrip("/") + "/rest/v1/" + SUPABASE_PROFILES_TABLE
         + "?select=save_data&user_id=eq." + urllib.parse.quote(str(user_id)))
  req = urllib.request.Request(url, headers={"apikey": SUPABASE_PUBLISHABLE_KEY,
    "Authorization": "Bearer " + token, "Accept": "application/json"}, method="GET")
  try:
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as response:
      rows = json.loads(response.read().decode("utf-8"))
    if isinstance(rows, list) and rows and isinstance(rows[0], dict) and isinstance(rows[0].get("save_data"), dict):
      return rows[0]["save_data"]
  except Exception as exc:
    print("SUPABASE FETCH SAVE ERROR:", str(exc)[:160])
  return None


def _supabase_get_profiles(timeout=5):
  """Read public leaderboard rows. Returns (rows, error); never blocks the UI caller."""
  url = SUPABASE_URL.rstrip("/") + "/rest/v1/" + SUPABASE_PROFILES_TABLE + "?select=nickname,mmr,avatar&banned=eq.false&order=mmr.desc&limit=100"
  req = urllib.request.Request(url, headers={
    "apikey": SUPABASE_PUBLISHABLE_KEY,
    "Authorization": "Bearer " + SUPABASE_PUBLISHABLE_KEY,
    "Accept": "application/json",
  }, method="GET")
  try:
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as response:
      payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
      return None, "Ответ сервера имеет неожиданный формат"
    return payload, None
  except urllib.error.HTTPError as exc:
    if exc.code == 404 or exc.code == 400:
      return None, "Таблица player_profiles ещё не создана или её структура отличается"
    if exc.code in (401, 403):
      return None, "Supabase отклонил ключ или права чтения"
    return None, "Ошибка Supabase HTTP " + str(exc.code)
  except Exception as exc:
    return None, "Нет соединения: " + str(exc)[:120]

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
  data.setdefault("global_theme", "halloween")
  data.setdefault("promos", [])
  if not isinstance(data["promos"], list): data["promos"] = []
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
    try: _queue_profile_sync(username, data)
    except Exception: pass
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



# Android system image picker and persistent custom photo avatar.
PHOTO_AVATAR_KEY = "custom_photo"

def _copy_android_content_uri(uri_string):
  """Copy a selected Android content:// image into app-private storage."""
  stream = None
  try:
    from jnius import autoclass
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    activity = PythonActivity.mActivity
    uri = autoclass("android.net.Uri").parse(str(uri_string))
    stream = activity.getContentResolver().openInputStream(uri)
    if stream is None:
      raise IOError("Не удалось открыть выбранное изображение")

    target = os.path.join(DATA_DIR, "profile_avatar_photo")
    # Read via InputStream.read() to avoid PyJNIus byte-array overload issues
    # that can silently fail on some Android/Java combinations.
    with open(target, "wb") as out:
      while True:
        value = int(stream.read())
        if value < 0:
          break
        out.write(bytes((value & 0xff,)))
    if not os.path.isfile(target) or os.path.getsize(target) == 0:
      raise IOError("Выбранный файл пуст")
    return target
  except Exception as exc:
    print("AVATAR PHOTO COPY ERROR:", exc)
    return None
  finally:
    try:
      if stream is not None:
        stream.close()
    except Exception:
      pass

def _open_android_photo_picker(callback):
  """Open Android image picker, with a compatibility fallback for providers."""
  try:
    from jnius import autoclass
    from android import activity

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    mActivity = PythonActivity.mActivity
    Intent = autoclass("android.content.Intent")
    Activity = autoclass("android.app.Activity")

    request_code = 7351
    state = {"finished": False}

    def _on_result(request, result, data):
      try:
        req = int(request)
      except Exception:
        return
      if req != request_code or state["finished"]:
        return
      state["finished"] = True
      try:
        activity.unbind(on_activity_result=_on_result)
      except Exception:
        pass

      path = None
      try:
        if int(result) == int(Activity.RESULT_OK) and data is not None:
          uri = data.getData()
          if uri is not None:
            path = _copy_android_content_uri(uri.toString())
      except Exception as exc:
        print("AVATAR PICKER RESULT ERROR:", repr(exc))
      try:
        Clock.schedule_once(lambda *_: callback(path), 0)
      except Exception as exc:
        print("AVATAR PICKER CALLBACK ERROR:", repr(exc))

    # Register the result callback before launching the external activity.
    activity.bind(on_activity_result=_on_result)

    # ACTION_GET_CONTENT is supported by more gallery apps and Android builds
    # than ACTION_OPEN_DOCUMENT on some devices. Try both actions if needed.
    intents = []
    for action_name in ("ACTION_GET_CONTENT", "ACTION_OPEN_DOCUMENT"):
      try:
        action = getattr(Intent, action_name)
        intent = Intent(action)
        intent.setType("image/*")
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intents.append(intent)
      except Exception as exc:
        print("AVATAR PICKER INTENT BUILD ERROR:", action_name, repr(exc))

    last_error = None
    for intent in intents:
      try:
        chooser = Intent.createChooser(intent, "Выбрать фото для аватара")
        mActivity.startActivityForResult(chooser, request_code)
        return True
      except Exception as exc:
        last_error = exc
        print("AVATAR PICKER LAUNCH ERROR:", repr(exc))

    try:
      activity.unbind(on_activity_result=_on_result)
    except Exception:
      pass
    print("AVATAR PICKER ERROR: no supported picker intent", repr(last_error))
    return False
  except Exception as exc:
    print("AVATAR PICKER ERROR:", repr(exc))
    return False


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
  (PHOTO_AVATAR_KEY, "Фото из галереи"),
]


# Секретные аватарки: их нет в магазине, они выдаются только по промокодам.
SECRET_AVATARS = [
  ("fy_crown", "Fy с короной (секретная)"),
  ("alienkok_avatar", "ALIENKOK (секретная)"),
  ("yroxik_avatar", "Yroxik (секретная)"),
]

# Встроенные промокоды: код (в верхнем регистре) -> награда.
# Остальные промокоды администратор создаёт прямо в админ-панели (Управление -> Промокоды).
BUILTIN_PROMOS = {
  "FISHKAOVNER1638": {"type": "avatar", "kind": "fy_crown"},
  "ALIENKOK": {"type": "bundle", "kind": "alienkok_avatar", "amount": 10000},
  "YROXIK": {"type": "bundle", "kind": "yroxik_avatar", "amount": 10000},
}
PROMO_TYPE_LABELS = {"coins": "Монеты", "case": "Кейс", "frame": "Рамка", "avatar": "Аватарка"}


def _norm_promo(raw):
  return re.sub(r"\s+", "", str(raw or "")).upper()


def _all_promos():
  promos = {k: dict(v) for k, v in BUILTIN_PROMOS.items()}
  try:
    for item in _load_admin_settings().get("promos", []):
      code = _norm_promo(item.get("code"))
      if code:
        promos[code] = dict(item, code=code)
  except Exception:
    pass
  return promos


def promo_kind_is_valid(ptype, kind):
  if ptype == "avatar":
    return kind in [a[0] for a in AVATARS] + [a[0] for a in SECRET_AVATARS]
  if ptype == "case":
    return kind in CASE_INFO
  if ptype == "frame":
    return kind in [f[0] for f in FRAMES] and kind != "none"
  return False


def redeem_promo(raw_code):
  """Активирует промокод для текущего аккаунта. Возвращает (успех, сообщение, ключ_аватарки_или_None)."""
  code = _norm_promo(raw_code)
  if not code:
    return False, "Введи промокод", None
  promo = _all_promos().get(code)
  if promo is None:
    return False, "Такого промокода не существует", None
  data = load_data()
  if not data:
    return False, "Сначала войди в аккаунт", None
  used = list(data.get("used_promos", []))
  if code in used:
    return False, "Ты уже активировал этот промокод", None
  expires = str(promo.get("expires", "") or "")
  if expires:
    try:
      if date.today() > date.fromisoformat(expires):
        return False, "Срок действия промокода истёк", None
    except ValueError:
      pass
  try:
    max_uses = int(promo.get("max_uses", 0) or 0)
    uses = int(promo.get("uses", 0) or 0)
  except (TypeError, ValueError):
    max_uses, uses = 0, 0
  if max_uses and uses >= max_uses:
    return False, "Лимит активаций этого промокода исчерпан", None
  ptype = str(promo.get("type", "coins"))
  kind = str(promo.get("kind", ""))
  avatar_key = None
  if ptype == "bundle":
    try:
      amount = int(promo.get("amount", 10000) or 10000)
    except (TypeError, ValueError):
      amount = 10000
    if amount <= 0 or not promo_kind_is_valid("avatar", kind):
      return False, "Промокод настроен неверно", None
    data["coins"] = int(data.get("coins", 0) or 0) + amount
    owned = list(data.get("owned_avatars", [av[0] for av in AVATARS[:6]]))
    if kind not in owned:
      owned.append(kind)
    data["owned_avatars"] = owned
    data["vip"] = True
    avatar_key = kind
    message = f"Промокод активирован! +{amount} монет, VIP-статус и эксклюзивная аватарка."
  elif ptype == "coins":
    try:
      amount = int(promo.get("amount", 0) or 0)
    except (TypeError, ValueError):
      amount = 0
    if amount <= 0:
      return False, "Промокод настроен неверно", None
    data["coins"] = int(data.get("coins", 0) or 0) + amount
    message = f"Промокод активирован! +{amount} монет"
  elif not promo_kind_is_valid(ptype, kind):
    return False, "Промокод настроен неверно", None
  elif ptype == "avatar":
    owned = list(data.get("owned_avatars", [av[0] for av in AVATARS[:6]]))
    if kind not in owned:
      owned.append(kind)
    data["owned_avatars"] = owned
    avatar_key = kind
    message = "Промокод активирован! Аватарка добавлена в инвентарь аватарок."
  elif ptype == "case":
    inv = list(data.get("inventory", []))
    inv.append({"type": "case", "kind": kind, "case": kind})
    data["inventory"] = inv
    message = f"Промокод активирован! Кейс «{CASE_INFO[kind]['label']}» добавлен в инвентарь кейсов."
  elif ptype == "frame":
    frames = list(data.get("owned_frames", ["none"]))
    if kind not in frames:
      frames.append(kind)
    data["owned_frames"] = frames
    message = "Промокод активирован! Рамка добавлена в инвентарь рамок."
  else:
    return False, "Промокод настроен неверно", None
  used.append(code)
  data["used_promos"] = used
  save_data(data)
  if code not in BUILTIN_PROMOS:  # счётчик активаций для промокодов администратора
    try:
      settings = _load_admin_settings()
      for item in settings.get("promos", []):
        if _norm_promo(item.get("code")) == code:
          item["uses"] = int(item.get("uses", 0) or 0) + 1
      _save_admin_settings(settings)
    except Exception:
      pass
  return True, message, avatar_key


class FyCrownAvatarArt(FloatLayout):
  """Секретная аватарка: буква Fy с короной на золотом фоне (всё нарисовано векторно)."""
  def __init__(self, size, **kwargs):
    super().__init__(size_hint=(None, None), size=(size, size), **kwargs)
    self.letters = Label(text="Fy", bold=True, color=(0.30, 0.14, 0.02, 1),
                         halign="center", valign="middle", size_hint=(None, None))
    self.add_widget(self.letters)
    self.bind(pos=self._redraw, size=self._redraw)
    self._redraw()

  def _redraw(self, *_):
    x, y = self.pos
    w, h = self.size
    s = min(w, h)
    cx, cy = x + w / 2, y + h / 2
    self.canvas.before.clear()
    with self.canvas.before:
      # Золотой фон: тёмный ободок, яркий диск и мягкий блик.
      Color(0.78, 0.50, 0.04, 1); Ellipse(pos=(x, y), size=(w, h))
      Color(1.0, 0.80, 0.18, 1); Ellipse(pos=(x + s * .04, y + s * .04), size=(s * .92, s * .92))
      Color(1.0, 0.92, 0.50, 0.55); Ellipse(pos=(x + s * .14, y + s * .30), size=(s * .52, s * .52))
      # Лучи за буквами.
      Color(1.0, 0.96, 0.62, 0.38)
      for i in range(12):
        a = 2 * math.pi * i / 12
        Line(points=[cx + math.cos(a) * s * .16, cy - s * .10 + math.sin(a) * s * .16,
                     cx + math.cos(a) * s * .43, cy - s * .10 + math.sin(a) * s * .43], width=max(1, s * .025))
      Color(1.0, 0.96, 0.62, 1); Line(circle=(cx, cy, s * .46), width=max(1, s * .022))
      # Корона: основание, три зубца и камни.
      Color(1.0, 0.97, 0.66, 1)
      Rectangle(pos=(x + s * .25, y + s * .58), size=(s * .50, s * .08))
      Triangle(points=[x + s * .25, y + s * .64, x + s * .44, y + s * .64, x + s * .335, y + s * .84])
      Triangle(points=[x + s * .37, y + s * .64, x + s * .63, y + s * .64, x + s * .50, y + s * .91])
      Triangle(points=[x + s * .56, y + s * .64, x + s * .75, y + s * .64, x + s * .665, y + s * .84])
      Color(0.45, 0.25, 0.02, 1)
      Line(points=[x + s * .25, y + s * .58, x + s * .75, y + s * .58, x + s * .75, y + s * .66,
                   x + s * .665, y + s * .84, x + s * .60, y + s * .70, x + s * .50, y + s * .91,
                   x + s * .40, y + s * .70, x + s * .335, y + s * .84, x + s * .25, y + s * .66],
           width=max(1, s * .02), close=True)
      for jx, jy, col in [(.335, .85, (0.9, 0.12, 0.2)), (.50, .92, (0.2, 0.55, 1.0)), (.665, .85, (0.9, 0.12, 0.2))]:
        Color(*col, 1); Ellipse(pos=(x + s * (jx - .028), y + s * (jy - .028)), size=(s * .056, s * .056))
    self.letters.size = (s * .80, s * .34)
    self.letters.text_size = self.letters.size
    self.letters.font_size = s * .31
    self.letters.pos = (cx - s * .40, y + s * .22)


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
  if av_key == PHOTO_AVATAR_KEY:
    photo_path = os.path.join(DATA_DIR, "profile_avatar_photo.jpg")
    if os.path.isfile(photo_path):
      from kivy.uix.image import Image as KivyImage
      return KivyImage(source=photo_path, allow_stretch=True, keep_ratio=True)
    return EmojiAvatarArt("cat_orange", size)
  if av_key in ("alienkok_avatar", "yroxik_avatar"):
    holder = FloatLayout(size_hint=(None, None), size=(size, size))
    bg = (0.08, 0.65, 0.22, 1) if av_key == "alienkok_avatar" else (0.12, 0.12, 0.16, 1)
    with holder.canvas.before:
      Color(*bg)
      holder._avatar_bg = RoundedRectangle(pos=holder.pos, size=holder.size, radius=[size * .12])
    holder.bind(pos=lambda w, v: setattr(w._avatar_bg, "pos", v),
                size=lambda w, v: setattr(w._avatar_bg, "size", v))
    label_text = "A L I E N" if av_key == "alienkok_avatar" else "YROXIK"
    label = Label(text=label_text, font_size=max(dp(8), size * .16), bold=True,
                  color=(1,1,1,1), halign="center", valign="middle")
    label.bind(size=lambda w, v: setattr(w, "text_size", v))
    holder.add_widget(label)
    return holder
  if av_key == "fy_crown":
    return FyCrownAvatarArt(size)
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


# ============================================================
# ЕЖЕДНЕВНЫЕ ЗАДАНИЯ
# ============================================================
DAILY_QUESTS = [
  {"id": "mine_3", "label": "Собери добычу в шахте 3 раза", "target": 3, "reward_coins": 500, "reward_mmr": 0, "progress_key": "mine_claims"},
  {"id": "open_5", "label": "Открой 5 кейсов", "target": 5, "reward_coins": 800, "reward_mmr": 10, "progress_key": "cases_opened"},
  {"id": "win_casino_3", "label": "Выиграй 3 раза в казино", "target": 3, "reward_coins": 1200, "reward_mmr": 15, "progress_key": "casino_wins"},
  {"id": "duel_win_3", "label": "Выиграй 3 рейтинговые дуэли", "target": 3, "reward_coins": 1000, "reward_mmr": 50, "progress_key": "duel_wins"},
  {"id": "sell_3", "label": "Продай 3 предмета", "target": 3, "reward_coins": 300, "reward_mmr": 5, "progress_key": "items_sold"},
]


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
      self.shadow = Line(points=[], width=dp(4), cap='round', joint='round', close=True)
      self.edge_color = Color(0.72, 0.76, 0.84, 1)
      self.edge = Line(points=[], width=dp(3), cap='round', joint='round', close=True)
      self.shield_color = Color(0.2, 0.22, 0.28, 1)
      self.shield = Line(points=[], width=dp(1.8), cap='round', joint='round', close=True)
      self.inner_color = Color(0.95, 0.96, 1.0, 1)
      self.inner = Line(points=[], width=dp(1.2), cap='round', joint='round', close=True)
      self.wing_color = Color(1, 1, 1, 1)
      self.wings = [Line(points=[], width=dp(2), cap='round', joint='round') for _ in range(2)]
      self.wing_feather_colors = [Color(1, 1, 1, 0) for _ in range(6)]
      self.wing_feathers = [Line(points=[], width=dp(0.75), cap='round', joint='round') for _ in range(6)]
      self.crown_color = Color(1, 0.88, 0.32, 1)
      self.crown = Line(points=[], width=dp(1.8), cap='round', joint='round', close=True)
      # Деления ранга рисуем короткими палочками, а не круглыми точками.
      self.gem_colors = []
      self.gems = []
      for _ in range(3):
        self.gem_colors.append(Color(1, 1, 1, 1))
        self.gems.append(Rectangle(pos=(-5000, -5000), size=(0, 0)))
      self.glint_color = Color(1, 1, 1, 0.72)
      self.glint = Line(points=[], width=dp(0.9), cap='round')
      # Elite badge: a small world medallion with feather-like wings.
      self.elite_globe_color = Color(0.15, 0.55, 0.95, 0.0)
      self.elite_globe = Ellipse(pos=(-5000, -5000), size=(0, 0))
      self.elite_globe_edge_color = Color(0.75, 0.95, 1.0, 0.0)
      self.elite_globe_edge = Line(circle=(-5000, -5000, 1), width=dp(1.0))
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
      # Layered inner feather lines make the wings look etched and metallic.
      feather_paths = [
        [cx-s*.31,cy+s*.035,cx-s*.40,cy+s*.13],
        [cx-s*.32,cy-s*.005,cx-s*.43,cy+s*.065],
        [cx-s*.33,cy-s*.045,cx-s*.42,cy-s*.035],
        [cx+s*.31,cy+s*.035,cx+s*.40,cy+s*.13],
        [cx+s*.32,cy-s*.005,cx+s*.43,cy+s*.065],
        [cx+s*.33,cy-s*.045,cx+s*.42,cy-s*.035],
      ]
      for fc, feather, path in zip(self.wing_feather_colors, self.wing_feathers, feather_paths):
        fc.rgba = (min(1, light[0]*1.15+.08), min(1, light[1]*1.15+.08), min(1, light[2]*1.15+.08), .95)
        feather.points = path
    else:
      self.wings[0].points = []; self.wings[1].points = []
      for feather in self.wing_feathers: feather.points = []
      for fc in self.wing_feather_colors: fc.rgba = (1, 1, 1, 0)
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
    globe_rank_ids = {"elite", "champion", "legend", "pro", "pro_2", "pro_3", "ultra_pro", "supreme", "godlike"}
    if rank_id in globe_rank_ids:
      # У каждого высокого ранга свой глобус: уникальная палитра и рисунок.
      gr = s * 0.17
      self.elite_globe.pos = (cx-gr, cy-gr*0.62)
      self.elite_globe.size = (2*gr, 1.24*gr)
      globe_palette = {
        "elite": ((0.08, 0.34, 0.78, 1), (0.72, 0.95, 1.0, 1)),
        "champion": ((0.95, 0.48, 0.06, 1), (1.0, 0.84, 0.32, 1)),
        "legend": ((0.72, 0.12, 0.28, 1), (1.0, 0.62, 0.72, 1)),
        "pro": ((0.12, 0.42, 0.12, 1), (1.0, 0.92, 0.08, 1)),
        "pro_2": ((0.08, 0.32, 0.62, 1), (0.25, 0.95, 1.0, 1)),
        "pro_3": ((0.16, 0.18, 0.58, 1), (0.58, 0.72, 1.0, 1)),
        "ultra_pro": ((0.32, 0.08, 0.62, 1), (0.88, 0.55, 1.0, 1)),
        "supreme": ((0.62, 0.08, 0.30, 1), (1.0, 0.48, 0.78, 1)),
        "godlike": ((0.42, 0.25, 0.04, 1), (1.0, 0.94, 0.42, 1)),
      }
      globe_fill, globe_edge = globe_palette[rank_id]
      self.elite_globe_color.rgba = globe_fill
      self.elite_globe_edge_color.rgba = globe_edge
      self.elite_globe_edge.circle = (cx, cy, gr*0.92)
      pattern = ["elite", "champion", "legend", "pro", "pro_2", "pro_3", "ultra_pro", "supreme", "godlike"].index(rank_id)
      if pattern % 3 == 0:
        self.elite_meridians[0].points = [cx,cy-gr*.60,cx-gr*.12,cy-gr*.25,cx-gr*.12,cy+gr*.25,cx,cy+gr*.60]
        self.elite_meridians[1].points = [cx,cy-gr*.60,cx+gr*.12,cy-gr*.25,cx+gr*.12,cy+gr*.25,cx,cy+gr*.60]
        self.elite_meridians[2].points = [cx-gr*.42,cy,cx+gr*.42,cy]
        self.elite_latitudes[0].points = [cx-gr*.78,cy-gr*.22,cx,cy-gr*.30,cx+gr*.78,cy-gr*.22]
        self.elite_latitudes[1].points = [cx-gr*.78,cy+gr*.22,cx,cy+gr*.30,cx+gr*.78,cy+gr*.22]
      elif pattern % 3 == 1:
        self.elite_meridians[0].points = [cx-gr*.2,cy-gr*.6,cx-gr*.32,cy,cx-gr*.2,cy+gr*.6]
        self.elite_meridians[1].points = [cx+gr*.2,cy-gr*.6,cx+gr*.32,cy,cx+gr*.2,cy+gr*.6]
        self.elite_meridians[2].points = [cx-gr*.48,cy,cx+gr*.48,cy]
        self.elite_latitudes[0].points = [cx-gr*.72,cy-gr*.18,cx,cy-gr*.38,cx+gr*.72,cy-gr*.18]
        self.elite_latitudes[1].points = [cx-gr*.72,cy+gr*.18,cx,cy+gr*.38,cx+gr*.72,cy+gr*.18]
      else:
        self.elite_meridians[0].points = [cx,cy-gr*.6,cx-gr*.25,cy-gr*.2,cx-gr*.25,cy+gr*.2,cx,cy+gr*.6]
        self.elite_meridians[1].points = [cx,cy-gr*.6,cx+gr*.25,cy-gr*.2,cx+gr*.25,cy+gr*.2,cx,cy+gr*.6]
        self.elite_meridians[2].points = [cx-gr*.38,cy-gr*.12,cx+gr*.38,cy+gr*.12]
        self.elite_latitudes[0].points = [cx-gr*.75,cy-gr*.25,cx,cy-gr*.18,cx+gr*.75,cy-gr*.25]
        self.elite_latitudes[1].points = [cx-gr*.75,cy+gr*.25,cx,cy+gr*.18,cx+gr*.75,cy+gr*.25]
      for line in self.elite_meridians + self.elite_latitudes:
        line.width = dp(0.75)
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
class JellyButton(Button):
  """Jelly press feedback applied to ordinary and glass buttons."""
  _click_sound = None
  _click_sound_attempted = False
  @classmethod
  def _load_click_sound(cls):
    if cls._click_sound_attempted:
      return cls._click_sound
    cls._click_sound_attempted = True
    try:
      sound_path = os.path.join(DATA_DIR, "catabox_click.wav")
      if not os.path.exists(sound_path):
        rate = 22050
        with wave.open(sound_path, "wb") as wav:
          wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate)
          frames = bytearray()
          for i in range(int(rate * 0.045)):
            t = i / rate
            amp = int(5000 * math.exp(-t * 85) * math.sin(2 * math.pi * (1150 - 500 * t) * t))
            frames.extend(struct.pack('<h', amp))
          wav.writeframes(bytes(frames))
      cls._click_sound = SoundLoader.load(sound_path)
      if cls._click_sound:
        cls._click_sound.volume = 0.28
    except Exception:
      cls._click_sound = None
    return cls._click_sound
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Без масштабирования/пружинной анимации: меньше лишней работы на каждом нажатии.
    self.bind(on_press=self._play_click_sound)
  def _play_click_sound(self, *args):
    try:
      sound = type(self)._load_click_sound()
      if sound:
        sound.stop(); sound.play()
    except Exception:
      pass

# Все кнопки, создаваемые ниже через Button(...), получают общий эффект нажатия.
Button = JellyButton

def _theme_button_palette():
  """Accent colors shared by buttons and profile UI for every global theme."""
  key = current_theme_key() if 'current_theme_key' in globals() else 'halloween'
  palettes = {
    'halloween': ((0.27, 0.095, 0.025, 0.94), (1.0, 0.43, 0.08, 0.98), (1.0, 0.63, 0.16, 0.75), (0.10, 0.025, 0.08, 0.94)),
    'newyear': ((0.025, 0.12, 0.27, 0.94), (0.20, 0.72, 1.0, 0.98), (0.65, 0.90, 1.0, 0.75), (0.015, 0.055, 0.16, 0.94)),
    'birthday': ((0.22, 0.055, 0.25, 0.94), (1.0, 0.35, 0.72, 0.98), (1.0, 0.72, 0.92, 0.75), (0.10, 0.025, 0.16, 0.94)),
    'mushrooms': ((0.035, 0.15, 0.105, 0.94), (0.30, 0.95, 0.48, 0.98), (0.65, 1.0, 0.52, 0.75), (0.015, 0.065, 0.055, 0.94)),
    'default': ((0.055, 0.095, 0.25, 0.94), (0.38, 0.62, 1.0, 0.98), (0.66, 0.78, 1.0, 0.75), (0.02, 0.035, 0.12, 0.94)),
  }
  return palettes.get(key, palettes['default'])

class GlassButton(Button):
  """Theme-aware glass button with accent outline and seasonal decoration."""
  radius = NumericProperty(dp(12))
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.background_normal = ''; self.background_down = ''; self.background_disabled_normal = ''
    self.background_color = (0, 0, 0, 0); self.color = (0.99, 0.98, 0.96, 1)
    self.font_size = dp(16); self.size_hint_y = None; self.height = dp(54)
    self._palette_key = None
    with self.canvas.before:
      fill, edge, glow, shadow = _theme_button_palette()
      self.fill_color = Color(*fill)
      self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
      self.glow_color = Color(*glow)
      self.glow = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius), width=dp(0.45))
      self.edge_color = Color(*edge)
      self.outline = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius), width=dp(0.65))
      self.glint_color = Color(1, 1, 1, 0.14)
      self.glint = Line(points=[self.x + dp(22), self.y + self.height - dp(3), self.x + self.width - dp(22), self.y + self.height - dp(3)], width=dp(0.5))
      # Без тематических рисунков на кнопках: только заливка и тонкий контур.
      self.web_color = Color(0, 0, 0, 0)
      self.web_lines = []
    self.bind(pos=self.update_rect, size=self.update_rect, state=self.update_state)
    self._apply_theme_style()

  def _apply_theme_style(self):
    key = current_theme_key() if 'current_theme_key' in globals() else 'halloween'
    fill, edge, glow, shadow = _theme_button_palette()
    self.fill_color.rgba = fill
    self.edge_color.rgba = edge
    self.glow_color.rgba = glow
    self.web_color.rgba = (0, 0, 0, 0)
    self._palette_key = key
    self.update_rect()

  def update_rect(self, *args):
    self.rect.pos = self.pos; self.rect.size = self.size; self.rect.radius = [self.radius]
    self.outline.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius)
    self.glow.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius)
    self.glint.points = [self.x + dp(22), self.y + self.height - dp(3), self.x + self.width - dp(22), self.y + self.height - dp(3)]
    # При смене темы обновляем только палитру — никаких паутин, лучей и узоров.
    if getattr(self, '_palette_key', None) != (current_theme_key() if 'current_theme_key' in globals() else 'halloween'):
      self._apply_theme_style()

  def update_state(self, *args):
    if self.state == 'down':
      fill, edge, glow, shadow = _theme_button_palette()
      self.fill_color.rgba = (min(1, fill[0]*1.25), min(1, fill[1]*1.25), min(1, fill[2]*1.25), 1)
      self.edge_color.rgba = (edge[0], edge[1], edge[2], 1)
      self.glow_color.rgba = (glow[0], glow[1], glow[2], 0.95)
    else:
      self._apply_theme_style()

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


RAINBOW_NICK_STYLES = {
  "classic": ("Классическая", ((1.0, 0.18, 0.24), (1.0, 0.72, 0.12), (0.25, 0.95, 0.42), (0.15, 0.62, 1.0), (0.72, 0.25, 1.0))),
  "sunset": ("Закатная", ((1.0, 0.22, 0.12), (1.0, 0.28, 0.48), (0.78, 0.22, 0.82), (1.0, 0.55, 0.18))),
  "ice": ("Ледяная", ((0.18, 0.95, 1.0), (0.25, 0.62, 1.0), (0.62, 0.72, 1.0), (0.92, 0.98, 1.0))),
  "neon": ("Неоновая", ((1.0, 0.12, 0.82), (0.25, 1.0, 0.86), (0.72, 1.0, 0.12), (0.4, 0.25, 1.0))),
  "forest": ("Лесная", ((0.12, 1.0, 0.36), (0.72, 1.0, 0.12), (0.08, 0.72, 0.58), (0.18, 0.52, 1.0))),
  "lava": ("Лавовая", ((1.0, 0.08, 0.04), (1.0, 0.28, 0.02), (1.0, 0.68, 0.08), (0.72, 0.04, 0.02))),
}

class RainbowNickLabel(Label):
  """Плавно меняющий цвет VIP-ник с выбираемой цветовой анимацией."""
  def __init__(self, **kwargs):
    self.rainbow_style = kwargs.pop("rainbow_style", "classic")
    if self.rainbow_style not in RAINBOW_NICK_STYLES:
      self.rainbow_style = "classic"
    kwargs.setdefault("color", (1, 0.2, 0.2, 1))
    super().__init__(**kwargs)
    self._rainbow_phase = random.random() * len(RAINBOW_NICK_STYLES[self.rainbow_style][1])
    self._rainbow_event = Clock.schedule_interval(self._animate_rainbow, 1.0 / 12.0)

  def _animate_rainbow(self, dt):
    palette = RAINBOW_NICK_STYLES.get(self.rainbow_style, RAINBOW_NICK_STYLES["classic"])[1]
    self._rainbow_phase = (self._rainbow_phase + max(0.001, dt) * 0.8) % len(palette)
    i = int(self._rainbow_phase)
    t = self._rainbow_phase - i
    a, b = palette[i], palette[(i + 1) % len(palette)]
    self.color = tuple(a[j] + (b[j] - a[j]) * t for j in range(3)) + (1,)

  def stop_animation(self):
    if getattr(self, "_rainbow_event", None):
      self._rainbow_event.cancel()
      self._rainbow_event = None


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================
class MainMenuScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _show_notice(self, title, text):
    body = Label(text=text, font_size=dp(15), halign="center", valign="middle")
    body.bind(size=lambda w, v: setattr(w, "text_size", (max(0, v[0] - dp(12)), None)))
    _open_glass_popup(title, body, (.90, .62))

  def on_pre_enter(self, *args):
    try:
      data = load_data()
      if data:
        changed = apply_season_rollover(data)
        notice = data.pop("season_notice", None)
        if changed or notice:
          save_data(data)
        if notice:
          Clock.schedule_once(lambda dt, n=notice: self._show_notice("НОВЫЙ СЕЗОН", n), .4)
    except Exception: pass
    try:
      theme = current_theme_key()
      mode = load_data().get("interface_mode", "mobile")
      if getattr(self, "_theme_applied", None) != theme or getattr(self, "_mode_applied", None) != mode: self._build_ui()
    except Exception: pass

  def _build_ui(self):
    self.clear_widgets()
    self._theme_applied = current_theme_key()
    data = load_data()
    self._mode_applied = data.get("interface_mode", "mobile")
    self.bg_widget = make_game_background()
    self.add_widget(self.bg_widget)

    coins = data.get("coins", 0)
    nick = str(data.get("nickname", "Игрок"))
    mmr = data.get("mmr", 0)
    rank_idx = rank_index_by_mmr(mmr)

    # Полноценный desktop-интерфейс главного экрана для ПК/ноутбуков.
    if data.get("interface_mode", "mobile") == "desktop" and Window.width >= dp(700):
      self._build_desktop_main(data, coins, nick, mmr, rank_idx)
      return

    outer = FloatLayout()
    # Центрируем весь блок главного меню по горизонтали и вертикали.
    # Высота рассчитана по сумме фиксированных высот элементов и промежутков.
    main = BoxLayout(orientation='vertical',
             size_hint=(1, None),
             spacing=dp(4), padding=(dp(6), dp(4)))
    main.bind(minimum_height=main.setter('height'))
    menu_scroll = ScrollView(size_hint=(0.96, 0.96), do_scroll_x=False,
                 do_scroll_y=True, bar_width=dp(3),
                 pos_hint={'center_x': 0.5, 'center_y': 0.5},
                 scroll_type=['content', 'bars'])
    menu_scroll.add_widget(main)

    # Компактная шапка заполняет пустое место сверху и задаёт меню законченный вид.
    header = BoxLayout(orientation='vertical', size_hint_y=None,
               height=dp(72), spacing=dp(1), padding=(dp(4), dp(2)))
    title_row = BoxLayout(orientation='horizontal', size_hint=(None, None),
                width=dp(222), height=dp(42), spacing=dp(4),
                pos_hint={'center_x': 0.5})
    header_title = Label(text="CataBox", font_size=dp(29), bold=True,
               color=(1, 1, 1, 1), halign='right', valign='middle',
               size_hint_x=None, width=dp(130))
    header_title.bind(size=lambda w, v: setattr(w, 'text_size', v))
    # Тонкая золотая плашка версии — как в макете: тёмное стекло, один аккуратный контур.
    version_badge = BoxLayout(orientation='vertical', size_hint=(None, None),
                size=(dp(88), dp(24)), pos_hint={'center_y': 0.5}, padding=(dp(2), dp(0)))
    with version_badge.canvas.before:
      Color(0.10, 0.085, 0.055, 0.96)
      version_bg = RoundedRectangle(pos=version_badge.pos, size=version_badge.size, radius=[dp(10)])
      Color(0.78, 0.60, 0.25, 0.28)
      version_glow = Line(rounded_rectangle=(version_badge.x, version_badge.y, version_badge.width, version_badge.height, dp(10)), width=dp(2.4))
      Color(0.78, 0.60, 0.25, 0.94)
      version_border = Line(rounded_rectangle=(version_badge.x, version_badge.y, version_badge.width, version_badge.height, dp(10)), width=dp(0.9))
    def update_version_badge(widget, *_):
      version_bg.pos = widget.pos; version_bg.size = widget.size
      version_glow.rounded_rectangle = (widget.x, widget.y, widget.width, widget.height, dp(10))
      version_border.rounded_rectangle = (widget.x, widget.y, widget.width, widget.height, dp(10))
    version_badge.bind(pos=update_version_badge, size=update_version_badge)
    version_badge.add_widget(Label(text=APP_VERSION, font_size=dp(10), bold=True,
                       color=(0.91, 0.78, 0.48, 1), halign='center', valign='middle'))
    title_row.add_widget(header_title)
    title_row.add_widget(version_badge)
    header_subtitle = Label(text="СОБИРАЙ  •  ПРОКАЧИВАЙСЯ  •  ПОБЕЖДАЙ",
               font_size=dp(9), bold=True, color=(0.78, 0.84, 0.94, 1),
               halign='center', valign='middle', size_hint_y=None, height=dp(18))
    header_subtitle.bind(size=lambda w, v: setattr(w, 'text_size', v))
    header.add_widget(title_row)
    header.add_widget(header_subtitle)
    main.add_widget(header)

    top_card = BoxLayout(orientation='horizontal', size_hint_y=None,
               height=dp(166), padding=(dp(20), dp(8)), spacing=dp(12))
    with top_card.canvas.before:
      _tfill, _tedge, _tglow, _tshadow = _theme_button_palette()
      Color(*_tshadow)
      tc = RoundedRectangle(pos=top_card.pos, size=top_card.size, radius=[dp(24)])
      Color(*_tedge)
      tc_edge = Line(rounded_rectangle=(top_card.x, top_card.y, top_card.width, top_card.height, dp(24)), width=dp(1.2))
      Color(*_tglow)
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
    rank_holder = FloatLayout(size_hint_x=None, width=dp(82))

    frame_art = FrameArt(frame_key, dp(106))
    frame_art.pos_hint = {"center_x": 0.5, "center_y": 0.5}
    rank_holder.add_widget(frame_art)

    avatar_art = avatar_to_art(avatar_key, dp(70))
    if avatar_art is not None:
      avatar_art.size_hint = (None, None)
      avatar_art.size = (dp(48), dp(48))
      avatar_art.pos_hint = {"center_x": 0.5, "center_y": 0.5}
      rank_holder.add_widget(avatar_art)
    else:
      # Надёжный простой fallback, если выбранный ключ аватарки неизвестен.
      fallback = Label(text="?", font_size=dp(24), bold=True,
                       color=(1, 1, 1, 1), size_hint=(None, None),
                       size=(dp(48), dp(48)), pos_hint={"center_x": 0.5, "center_y": 0.5})
      rank_holder.add_widget(fallback)

    rank_badge_holder = FloatLayout(size_hint=(None, None), size=(dp(40), dp(40)),
                                    pos_hint={"center_x": 0.80, "center_y": 0.20})
    rank_badge = RankIcon(max(0, min(int(data.get("profile_rank", rank_idx)), len(RANKS) - 1)), dp(34))
    rank_badge.size_hint = (None, None)
    rank_badge.size = (dp(34), dp(34))
    rank_badge.pos_hint = {"center_x": 0.5, "center_y": 0.5}
    rank_badge_holder.add_widget(rank_badge)
    rank_holder.add_widget(rank_badge_holder)
    top_card.add_widget(rank_holder)

    # Информация разбита на две ровные колонки:
    # слева ник и ранг, справа количество монет и подпись.
    info_box = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=1,
                         height=dp(58))
    left_info = BoxLayout(orientation='vertical', spacing=dp(3),
                          size_hint_x=0.52, size_hint_y=None, height=dp(54))
    NickLabel = RainbowNickLabel if data.get('vip', False) else Label
    nick_label_kwargs = {"rainbow_style": data.get("rainbow_nick_style", "classic")} if data.get("vip", False) else {}
    nick_label = NickLabel(**nick_label_kwargs, text=nick, font_size=dp(14), bold=True,
                  shorten=True, shorten_from='right', color=(0.55, 0.72, 1, 1),
                  size_hint_y=None, height=dp(26), halign='center', valign='middle')
    nick_label.bind(size=lambda w, v: setattr(w, 'text_size', v))
    left_info.add_widget(nick_label)
    rank_label = Label(text=RANKS[rank_idx][1], font_size=dp(11),
                  color=(0.85, 0.88, 0.96, 1), size_hint_y=None, height=dp(22),
                  halign='center', valign='middle', shorten=True)
    rank_label.bind(size=lambda w, v: setattr(w, 'text_size', v))
    left_info.add_widget(rank_label)
    info_box.add_widget(left_info)

    coins_box = BoxLayout(orientation='vertical', spacing=dp(3),
                          size_hint_x=0.48, size_hint_y=None, height=dp(54))
    coins_value = Label(text=f"{coins}", font_size=dp(17), bold=True,
                   color=(1, 0.85, 0.4, 1), size_hint_y=None, height=dp(26),
                   halign='center', valign='middle', shorten=True)
    coins_value.bind(size=lambda w, v: setattr(w, 'text_size', v))
    coins_box.add_widget(coins_value)
    coins_caption = Label(text="монет", font_size=dp(9),
                   color=(0.85, 0.85, 0.9, 1), size_hint_y=None, height=dp(22),
                   halign='center', valign='middle')
    coins_caption.bind(size=lambda w, v: setattr(w, 'text_size', v))
    coins_box.add_widget(coins_caption)
    info_box.add_widget(coins_box)
    # Центрируем обе колонки по вертикали относительно всей карточки,
    # а не прижимаем их к нижнему краю.
    info_anchor = AnchorLayout(anchor_x='center', anchor_y='center',
                               size_hint=(1, 1), padding=(0, 0))
    info_box.size_hint = (1, None)
    info_box.height = dp(58)
    info_anchor.add_widget(info_box)
    top_card.add_widget(info_anchor)
    main.add_widget(top_card)

    tap_btn = GlassButton(text="ШАХТА", height=dp(80))
    tap_btn.font_size = dp(23)
    tap_btn.bold = True
    tap_btn.bind(on_press=lambda x: self.manager.go_to('mine'))
    main.add_widget(tap_btn)

    # Все пункты меню используют один нейтральный Liquid Glass стиль.
    menu_items = [
      ("Кейсы", "cases"),
      ("Инвентарь", "inventory"),
      ("Ранги", "ranks"),
      ("Профиль", "profile"),
      ("Магазин", "shop"),
      ("Рейтинговый матч", "ranked"),
      ("ADMIN", "admin_gate"),
      ("Лидерборд", "leaderboard"),
      ("Рынок кейсов", "market"),
      ("Задания", "quests"),
    ]
    # Основная сетка из двух колонок; инвентарь кейсов занимает всю ширину ниже.
    grid = GridLayout(cols=2, spacing=dp(5), size_hint_y=None,
              row_default_height=dp(62), row_force_default=True, padding=(0, dp(2)))
    grid.bind(minimum_height=grid.setter('height'))
    for label, target in menu_items:
      btn = GlassButton(text=label, height=dp(70))
      btn.font_size = dp(13 if label.startswith("Инвентарь ") else 14)
      btn.bind(on_press=lambda _btn, t=target: self.manager.go_to(t))
      grid.add_widget(btn)
    main.add_widget(grid)
    achievements_btn = GlassButton(text="Достижения", height=dp(62))
    achievements_btn.font_size = dp(14)
    achievements_btn.bind(on_press=lambda _btn: self.manager.go_to("achievements"))
    main.add_widget(achievements_btn)
    outer.add_widget(menu_scroll)
    self.add_widget(outer)

  def on_pre_enter(self, *args):
    self._build_ui()
    _recheck_account_status(self)


  def _build_desktop_main(self, data, coins, nick, mmr, rank_idx):
    """Desktop workspace with persistent navigation and an in-window right pane."""
    from kivy.uix.image import Image

    root = BoxLayout(orientation="horizontal", padding=dp(16), spacing=dp(14))
    root_layer = FloatLayout()
    root_layer.add_widget(root)
    self.add_widget(root_layer)

    # Left navigation stays visible while the workspace changes.
    sidebar = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(208),
                        spacing=dp(8), padding=(dp(2), dp(4)))
    brand = Label(text="[b]CataBox[/b]", markup=True, font_size=dp(30),
                  color=(0.65, 0.82, 1, 1), size_hint_y=None, height=dp(58))
    sidebar.add_widget(brand)
    sidebar.add_widget(Label(text="DESKTOP", font_size=dp(10),
        color=(0.48, 0.75, 1, 1), size_hint_y=None, height=dp(20)))

    workspace = BoxLayout(orientation="vertical", spacing=dp(8), padding=(dp(2), 0))
    nav_items = [
      ("Главная", "home"), ("Шахта", "mine"), ("Кейсы", "cases"),
      ("Рынок кейсов и предметов", "market"), ("Инвентарь предметов", "inventory"),
      ("Ранги", "ranks"), ("Профиль", "profile"),
      ("Магазин", "shop"), ("Задания", "quests"), ("Достижения", "achievements"),
      ("Рейтинговый матч", "ranked"), ("Лидерборд", "leaderboard"),
      ("Администрирование", "admin_gate"),
    ]

    def show_workspace(target, title=None):
      workspace.clear_widgets()
      heading = Label(text=title or next((label for label, key in nav_items if key == target), target.title()),
                      font_size=dp(23), bold=True, color=(0.9, 0.95, 1, 1),
                      size_hint_y=None, height=dp(46), halign="left", valign="middle")
      heading.bind(size=lambda w, v: setattr(w, "text_size", v))
      workspace.add_widget(heading)

      if target == "home":
        panel = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(20))
        _glass_card(panel, color=(0.035, 0.065, 0.15, 0.96),
                    edge=(0.15, 0.37, 0.85, 0.88), radius=dp(18))
        panel.add_widget(Label(text="Обзор аккаунта", font_size=dp(18), bold=True,
                               color=(0.72, 0.84, 1, 1), size_hint_y=None, height=dp(34)))
        panel.add_widget(Label(text=f"{nick}\nMMR: {mmr}\nРанг: {RANKS[rank_idx][1]}\nМонеты: {coins:,}".replace(",", " "),
                               font_size=dp(17), color=(0.9, 0.94, 1, 1),
                               halign="left", valign="top"))
        workspace.add_widget(panel)
        return

      # Keep the desktop frame visible and render the chosen section in the right workspace.
      # Section controls are placed in this pane; the full-screen mobile navigation is not used.
      panel = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(20))
      _glass_card(panel, color=(0.035, 0.065, 0.15, 0.96),
                  edge=(0.15, 0.37, 0.85, 0.88), radius=dp(18))
      descriptions = {
        "mine": "Шахта приносит монеты, даже пока тебя нет в игре.",
        "cases": "Открывай кейсы и получай предметы.",
        "inventory": "Просматривай собранные предметы.",
        "ranks": "Информация о ранге и рейтинге.",
        "profile": "Аватар, рамка, имя и параметры аккаунта.",
        "quests": "Ежедневные задания обновляются каждый день.",
        "achievements": "Выполняй цели и получай награды.",
        "shop": "Предметы и улучшения магазина.",
        "ranked": "Рейтинговая дуэль памяти и MMR.",
        "leaderboard": "Сравнение результатов игроков.",
        "admin_gate": "Инструменты управления аккаунтом.",
      }
      panel.add_widget(Label(text=descriptions.get(target, "Раздел CataBox"),
                             font_size=dp(17), color=(0.7, 0.8, 0.94, 1),
                             halign="left", valign="top"))
      open_btn = GlassButton(text="Открыть раздел", height=dp(48), size_hint_y=None)
      open_btn.bind(on_press=lambda *_: self.manager.go_to(target))
      panel.add_widget(open_btn)
      panel.add_widget(Widget())
      workspace.add_widget(panel)

    nav_list = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
    nav_list.bind(minimum_height=nav_list.setter("height"))
    for label, target in nav_items:
      b = GlassButton(text=label, height=dp(44), size_hint_y=None)
      b.font_size = dp(13)
      b.bind(on_press=lambda _b, t=target, name=label: show_workspace(t, name))
      nav_list.add_widget(b)

    nav_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True,
                            bar_width=dp(5), scroll_type=["bars", "content"])
    nav_scroll.add_widget(nav_list)
    sidebar.add_widget(nav_scroll)
    root.add_widget(sidebar)

    # Top bar: actual avatar art, selected frame and rank emblem; no emoji glyphs.
    content = BoxLayout(orientation="vertical", spacing=dp(8), padding=(dp(2), 0))
    topbar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(88),
                       spacing=dp(14), padding=dp(10))
    _glass_card(topbar, color=(0.035, 0.065, 0.15, 0.97),
                edge=(0.12, 0.42, 0.95, 0.9), radius=dp(18))

    avatar_holder = FloatLayout(size_hint_x=None, width=dp(72))
    frame_art = FrameArt(str(data.get("frame", "none")), dp(68))
    frame_art.size_hint = (None, None)
    frame_art.size = (dp(68), dp(68))
    frame_art.pos_hint = {"center_x": .5, "center_y": .5}
    avatar_holder.add_widget(frame_art)
    avatar_art = avatar_to_art(str(data.get("avatar", "cat_orange")), dp(44))
    if avatar_art is not None:
      avatar_art.size_hint = (None, None)
      avatar_art.size = (dp(44), dp(44))
      avatar_art.pos_hint = {"center_x": .5, "center_y": .5}
      avatar_holder.add_widget(avatar_art)
    rank_icon = RankIcon(max(0, min(int(data.get("profile_rank", rank_idx)), len(RANKS)-1)), dp(27))
    rank_icon.size_hint = (None, None)
    rank_icon.size = (dp(27), dp(27))
    rank_icon.pos_hint = {"right": 1, "y": 0}
    avatar_holder.add_widget(rank_icon)
    topbar.add_widget(avatar_holder)

    player = BoxLayout(orientation="vertical", spacing=dp(2))
    player.add_widget(Label(text=nick, bold=True, font_size=dp(18),
                            color=(0.9, 0.95, 1, 1), halign="left", valign="middle"))
    player.add_widget(Label(text=f"{RANKS[rank_idx][1]}  |  MMR {mmr}",
                            font_size=dp(12), color=(0.55, 0.75, 1, 1),
                            halign="left", valign="middle"))
    topbar.add_widget(player)
    currency = Label(text=f"{coins:,} монет".replace(",", " "), bold=True,
                     font_size=dp(17), color=(1, 0.83, 0.35, 1),
                     size_hint_x=None, width=dp(150))
    topbar.add_widget(currency)
    content.add_widget(topbar)

    # The extra mini-tabs below the player panel are intentionally removed.
    # The main workspace now starts immediately under the top player bar.
    pane_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=dp(4))
    pane_scroll.add_widget(workspace)
    content.add_widget(pane_scroll)
    root.add_widget(content)
    show_workspace("home", "Главная")


# ============================================================
# ИКОНКИ ШАХТЫ (зависят от темы оформления)
# ============================================================
class ThemeIconArt(Widget):
  """Векторные иконки тем: тыква, ёлка, торт. Рисуются средствами Kivy без картинок."""
  def __init__(self, kind="pumpkin", size=dp(120), **kwargs):
    super().__init__(size_hint=(None, None), size=(size, size), **kwargs)
    self.kind = kind
    self.bind(pos=self.redraw, size=self.redraw)
    self.redraw()

  def redraw(self, *_):
    self.canvas.clear()
    x, y = self.pos
    s = min(self.width, self.height)
    def P(fx, fy):
      return (x + s * fx, y + s * fy)
    with self.canvas:
      if self.kind == "pumpkin":
        Color(1.0, 0.45, 0.05, 0.22); Ellipse(pos=P(.02, .10), size=(s * .96, s * .84))
        # дольки тыквы
        Color(0.78, 0.30, 0.02, 1); Ellipse(pos=P(.06, .16), size=(s * .50, s * .66)); Ellipse(pos=P(.44, .16), size=(s * .50, s * .66))
        Color(0.95, 0.42, 0.04, 1); Ellipse(pos=P(.14, .12), size=(s * .46, s * .70)); Ellipse(pos=P(.40, .12), size=(s * .46, s * .70))
        Color(1.0, 0.55, 0.10, 1); Ellipse(pos=P(.26, .10), size=(s * .48, s * .74))
        Color(0.62, 0.22, 0.0, 1)
        for fx in (.34, .66):
          Line(ellipse=(x + s * (fx - .10), y + s * .12, s * .20, s * .70), width=max(1, s * .012))
        # хвостик и лист
        Color(0.30, 0.20, 0.05, 1); Rectangle(pos=P(.45, .80), size=(s * .10, s * .13))
        Color(0.25, 0.65, 0.20, 1); Triangle(points=[*P(.55, .86), *P(.76, .96), *P(.62, .80)])
        # светящееся страшное лицо
        Color(1.0, 0.92, 0.25, 1)
        Triangle(points=[*P(.27, .52), *P(.43, .52), *P(.34, .66)])
        Triangle(points=[*P(.57, .52), *P(.73, .52), *P(.66, .66)])
        Triangle(points=[*P(.46, .40), *P(.54, .40), *P(.50, .48)])
        Ellipse(pos=P(.26, .20), size=(s * .48, s * .18))
        Color(0.30, 0.08, 0.0, 1)
        for i in range(4):
          Triangle(points=[*P(.30 + i * .11, .38), *P(.36 + i * .11, .38), *P(.33 + i * .11, .30)])
        for i in range(3):
          Triangle(points=[*P(.35 + i * .11, .20), *P(.41 + i * .11, .20), *P(.38 + i * .11, .27)])
      elif self.kind == "tree":
        Color(0.2, 0.7, 1.0, 0.16); Ellipse(pos=P(.02, .06), size=(s * .96, s * .90))
        Color(0.40, 0.24, 0.10, 1); Rectangle(pos=P(.44, .06), size=(s * .12, s * .14))
        for i, (col, w, yy) in enumerate([((0.05, 0.40, 0.18), .74, .16), ((0.07, 0.50, 0.22), .60, .34), ((0.10, 0.60, 0.27), .46, .52)]):
          Color(*col)
          Triangle(points=[*P(.5 - w / 2, yy), *P(.5 + w / 2, yy), *P(.5, yy + .30)])
        Color(1.0, 0.86, 0.25, 1)
        Triangle(points=[*P(.42, .80), *P(.58, .80), *P(.50, .95)]); Triangle(points=[*P(.42, .875), *P(.58, .875), *P(.50, .74)])
        for fx, fy, col in [(.40, .26, (0.95, 0.15, 0.20)), (.60, .24, (0.2, 0.55, 1.0)), (.46, .44, (1.0, 0.8, 0.2)), (.58, .46, (0.95, 0.15, 0.20)), (.50, .62, (0.2, 0.55, 1.0)), (.36, .30, (1.0, 0.8, 0.2))]:
          Color(*col); Ellipse(pos=P(fx - .03, fy - .03), size=(s * .06, s * .06))
        Color(1, 1, 1, .85); Ellipse(pos=P(.16, .02), size=(s * .68, s * .09))
      else:  # cake
        Color(1.0, 0.7, 0.9, 0.18); Ellipse(pos=P(.02, .06), size=(s * .96, s * .90))
        Color(0.85, 0.85, 0.95, 1); Ellipse(pos=P(.08, .08), size=(s * .84, s * .12))
        Color(0.95, 0.45, 0.65, 1); Rectangle(pos=P(.16, .17), size=(s * .68, s * .24))
        Color(1.0, 0.82, 0.45, 1); Rectangle(pos=P(.24, .41), size=(s * .52, s * .20))
        Color(1, 1, 1, 1)
        for i in range(6):
          Ellipse(pos=P(.14 + i * .115, .36), size=(s * .12, s * .10))
        for i in range(4):
          Ellipse(pos=P(.22 + i * .13, .56), size=(s * .12, s * .10))
        for i, col in enumerate([(0.2, 0.6, 1.0), (0.3, 0.9, 0.4), (1.0, 0.3, 0.3)]):
          Color(*col); Rectangle(pos=P(.34 + i * .14, .64), size=(s * .05, s * .17))
          Color(1.0, 0.8, 0.15, 1); Ellipse(pos=P(.325 + i * .14, .80), size=(s * .08, s * .11))
          Color(1.0, 0.45, 0.05, 1); Ellipse(pos=P(.345 + i * .14, .81), size=(s * .04, s * .07))
        Color(0.6, 0.9, 1.0, 1)
        for fx, fy in [(.22, .26), (.40, .30), (.58, .24), (.72, .30)]:
          Ellipse(pos=P(fx, fy), size=(s * .04, s * .04))


def make_mine_icon(kind, size):
  """Иконка шахты: минерал по умолчанию, у тем — своя картинка (тыква, ёлка, торт, гриб)."""
  try:
    if kind == "mineral":
      w = MineralArt("gold_mineral", size)
    elif kind == "mushroom":
      w = MushroomArt("glow", size)
    else:
      w = ThemeIconArt(kind, size)
  except Exception:
    w = ThemeIconArt("pumpkin", size)
  w.size_hint = (None, None)
  w.size = (size, size)
  return w


# Лёгкие статичные обои: рисуются средствами Kivy, без тяжёлых картинок и анимаций.
STATIC_WALLPAPERS = [
  ("cosmic", "Космическая вспышка", (0.015, 0.025, 0.12, 1)),
  ("sunset", "Закат в горах", (0.16, 0.045, 0.16, 1)),
  ("moon", "Лунная ночь", (0.015, 0.045, 0.08, 1)),
  ("aurora", "Северное сияние", (0.005, 0.09, 0.12, 1)),
  ("ocean", "Глубокий океан", (0.0, 0.10, 0.22, 1)),
  ("flame", "Вечное пламя", (0.12, 0.018, 0.01, 1)),
  ("gold", "Золотой минерал", (0.12, 0.075, 0.008, 1)),
  ("mushroom", "Грибной лес", (0.045, 0.02, 0.08, 1)),
  ("halloween", "Хэллоуин", (0.035, 0.008, 0.055, 1)),
  ("newyear", "Новый год", (0.01, 0.03, 0.12, 1)),
  ("birthday", "День рождения игры", (0.075, 0.03, 0.15, 1)),
]

# Темы оформления: выбираются ТОЛЬКО в админ-панели и действуют для всей игры.
# Анимированных обоев больше нет — у каждой темы своя статичная картинка и своя иконка шахты.
THEMES = {
  "default":   {"name": "Стандартная",        "wallpaper": "cosmic",    "icon": "mineral",
                "desc": "Космический фон, золотой минерал в шахте."},
  "halloween": {"name": "Хэллоуин",           "wallpaper": "halloween", "icon": "pumpkin",
                "desc": "Страшный фон с паутиной, в шахте тыква вместо минерала."},
  "newyear":   {"name": "Новый год",          "wallpaper": "newyear",   "icon": "tree",
                "desc": "Снег, ёлки и гирлянды, в шахте новогодняя ёлка."},
  "birthday":  {"name": "День рождения игры", "wallpaper": "birthday",  "icon": "cake",
                "desc": "Шарики, конфетти и флажки, в шахте праздничный торт."},
  "mushrooms": {"name": "Грибы",              "wallpaper": "mushroom",  "icon": "mushroom",
                "desc": "Светящийся грибной лес, в шахте светящийся гриб."},
}


def current_theme_key():
  try:
    key = _load_admin_settings().get("global_theme", "halloween")
  except Exception:
    key = "default"
  return key if key in THEMES else "default"


def current_theme():
  return THEMES[current_theme_key()]


_THEME_BGS = weakref.WeakSet()


def apply_theme_everywhere():
  """Мгновенно перерисовывает фон на всех уже созданных экранах после смены темы."""
  wall = current_theme()["wallpaper"]
  for bg in list(_THEME_BGS):
    try:
      bg.wallpaper = wall
      bg.redraw()
    except Exception:
      pass

class StaticWallpaperBg(Widget):
  def __init__(self, wallpaper="cosmic", rounded_preview=False, **kwargs):
    super().__init__(**kwargs)
    self.wallpaper = wallpaper
    self.rounded_preview = rounded_preview
    self.bind(pos=self.redraw, size=self.redraw)
    self.redraw()
  def redraw(self, *args):
    self.canvas.clear()
    w, h = max(1, self.width), max(1, self.height)
    x, y = self.pos
    colors = {item[0]: item[2] for item in STATIC_WALLPAPERS}
    base = colors.get(self.wallpaper, colors["cosmic"])
    with self.canvas:
      if self.rounded_preview:
        StencilPush()
        RoundedRectangle(pos=(x, y), size=(w, h), radius=[dp(12)])
        StencilUse()
      Color(*base)
      if self.rounded_preview:
        RoundedRectangle(pos=(x,y), size=(w,h), radius=[dp(12)])
      else:
        Rectangle(pos=(x,y), size=(w,h))
      # Графические акценты различаются по выбранному статичному фону.
      if self.wallpaper == "sunset":
        Color(1, .25, .25, .75); Ellipse(pos=(x+w*.58,y+h*.40), size=(w*.25,w*.25))
        Color(.025,.018,.07,1); Triangle(points=[x,y+h*.32,x+w*.36,y+h*.78,x+w*.68,y+h*.32]); Triangle(points=[x+w*.35,y+h*.28,x+w*.73,y+h*.70,x+w,y+h*.28])
      elif self.wallpaper == "moon":
        Color(.72,.84,1,.9); Ellipse(pos=(x+w*.62,y+h*.56), size=(min(w,h)*.22, min(w,h)*.22))
        Color(.015,.045,.08,1); Ellipse(pos=(x+w*.68,y+h*.60), size=(min(w,h)*.20,min(w,h)*.20))
        Color(.22,.34,.48,.8); Triangle(points=[x,y,x+w*.30,y+h*.38,x+w*.55,y]); Triangle(points=[x+w*.4,y,x+w*.78,y+h*.30,x+w,y])
      elif self.wallpaper == "aurora":
        for i in range(5):
          Color(.05,.95,.72,.12+i*.035); Line(points=[x-w*.1,y+h*(.52+i*.045),x+w*.25,y+h*(.78-i*.025),x+w*.58,y+h*(.48+i*.035),x+w*1.05,y+h*(.75-i*.02)], width=dp(2+i*.5))
      elif self.wallpaper == "ocean":
        for i in range(8):
          Color(.1,.65,1,.12+i*.025); Line(points=[x,y+h*(.18+i*.055),x+w*.3,y+h*(.22+i*.055),x+w*.65,y+h*(.15+i*.055),x+w,y+h*(.20+i*.055)], width=dp(2))
        Color(.1,.6,1,.16); Ellipse(pos=(x+w*.3,y+h*.35),size=(w*.42,h*.32))
      elif self.wallpaper == "flame":
        Color(1,.18,.015,.75); Triangle(points=[x+w*.18,y,x+w*.42,y+h*.78,x+w*.55,y])
        Color(1,.55,.02,.55); Triangle(points=[x+w*.4,y,x+w*.62,y+h*.64,x+w*.8,y])
      elif self.wallpaper == "gold":
        Color(1,.72,.05,.7); Line(points=[x+w*.15,y+h*.2,x+w*.4,y+h*.72,x+w*.55,y+h*.36,x+w*.83,y+h*.82],width=dp(3))
        Color(1,.85,.25,.25); Ellipse(pos=(x+w*.2,y+h*.25),size=(w*.55,h*.45))
      elif self.wallpaper == "mushroom":
        rnd = random.Random(11)
        Color(.3, .95, .6, .10); Ellipse(pos=(x + w * .1, y + h * .02), size=(w * .8, h * .4))
        for i in range(34):  # светящиеся споры
          Color(.5, 1, .75, rnd.uniform(.12, .5))
          r = rnd.uniform(1.2, 3.2) * dp(1)
          Ellipse(pos=(x + rnd.random() * w, y + rnd.random() * h), size=(r, r))
        caps = [(.14, .10, .20, (.85, .15, .35)), (.42, .06, .28, (.55, .25, .95)), (.74, .12, .22, (.15, .75, .85)),
                (.28, .30, .13, (.95, .65, .15)), (.62, .34, .15, (.85, .15, .35)), (.88, .40, .10, (.55, .25, .95))]
        for fx, fy, fw, col in caps:
          cw = w * fw; ch = cw * .62; stem_w = cw * .26; stem_h = ch * 1.25
          sx = x + w * fx + cw / 2 - stem_w / 2; sy = y + h * fy
          Color(.9, .85, .75, .95); Rectangle(pos=(sx, sy), size=(stem_w, stem_h))
          Color(col[0], col[1], col[2], .22); Ellipse(pos=(x + w * fx - cw * .2, sy + stem_h - ch * .5), size=(cw * 1.4, ch * 1.6))
          Color(*col, .95); Ellipse(pos=(x + w * fx, sy + stem_h - ch * .45), size=(cw, ch))
          Color(1, 1, 1, .8)
          for k in range(3):
            Ellipse(pos=(x + w * fx + cw * (.2 + .22 * k), sy + stem_h + ch * (.02 + .12 * (k % 2))), size=(cw * .12, cw * .12))
      elif self.wallpaper == "halloween":
        rnd = random.Random(31)
        mm = min(w, h)
        Color(1.0, .50, .08, .16); Ellipse(pos=(x + w * .50, y + h * .56), size=(mm * .52, mm * .52))
        Color(1.0, .55, .10, .95); Ellipse(pos=(x + w * .56, y + h * .62), size=(mm * .38, mm * .38))
        # силуэты летучих мышей
        def bat(cx, cy, sz):
          Color(.01, 0, .02, 1)
          Triangle(points=[cx, cy, cx - sz, cy + sz * .55, cx - sz * .35, cy - sz * .22])
          Triangle(points=[cx, cy, cx + sz, cy + sz * .55, cx + sz * .35, cy - sz * .22])
          Ellipse(pos=(cx - sz * .16, cy - sz * .2), size=(sz * .32, sz * .42))
          Triangle(points=[cx - sz * .14, cy + sz * .18, cx - sz * .06, cy + sz * .34, cx, cy + sz * .18])
          Triangle(points=[cx + sz * .14, cy + sz * .18, cx + sz * .06, cy + sz * .34, cx, cy + sz * .18])
        bat(x + w * .70, y + h * .78, mm * .10); bat(x + w * .38, y + h * .66, mm * .07); bat(x + w * .86, y + h * .60, mm * .06)
        # земля, кладбище и мёртвое дерево
        Color(.01, 0, .015, 1); Rectangle(pos=(x, y), size=(w, h * .10))
        Color(.45, 1, .55, .08); Ellipse(pos=(x - w * .1, y + h * .02), size=(w * 1.2, h * .14))
        for fx in (.12, .30, .78):
          Color(.10, .09, .13, 1)
          Rectangle(pos=(x + w * fx, y + h * .08), size=(w * .09, h * .07)); Ellipse(pos=(x + w * fx, y + h * .125), size=(w * .09, h * .05))
        Color(.01, 0, .015, 1)
        Line(points=[x + w * .60, y + h * .09, x + w * .61, y + h * .30, x + w * .56, y + h * .42], width=dp(3.5))
        Line(points=[x + w * .61, y + h * .26, x + w * .70, y + h * .36, x + w * .74, y + h * .44], width=dp(2.5))
        Line(points=[x + w * .60, y + h * .20, x + w * .52, y + h * .27], width=dp(2))
        # глаза в темноте
        for fx, fy in [(.08, .28), (.90, .24), (.45, .14)]:
          Color(1, .85, .1, .9)
          Ellipse(pos=(x + w * fx, y + h * fy), size=(dp(5), dp(3.5))); Ellipse(pos=(x + w * fx + dp(9), y + h * fy), size=(dp(5), dp(3.5)))
        # паутина по углам: лучи и провисающие дуги
        def web(ox, oy, a0, a1, R):
          rays = 6
          pts = []
          for i in range(rays + 1):
            ang = a0 + (a1 - a0) * i / rays
            pts.append((math.cos(ang), math.sin(ang)))
          Color(.86, .88, .95, .6)
          for dx, dy in pts:
            Line(points=[ox, oy, ox + dx * R, oy + dy * R], width=dp(.9))
          for k in range(1, 6):
            r = R * k / 5.5
            for i in range(rays):
              (ax, ay), (bx, by) = pts[i], pts[i + 1]
              p1 = (ox + ax * r, oy + ay * r); p2 = (ox + bx * r, oy + by * r)
              mid = ((p1[0] + p2[0]) / 2 + (ox - (p1[0] + p2[0]) / 2) * .16, (p1[1] + p2[1]) / 2 + (oy - (p1[1] + p2[1]) / 2) * .16)
              Line(points=[p1[0], p1[1], mid[0], mid[1], p2[0], p2[1]], width=dp(.8))
        web(x, y + h, -math.pi / 2, 0, mm * .62)
        web(x + w, y + h, math.pi, math.pi * 1.5, mm * .62)
        web(x, y, 0, math.pi / 2, mm * .30)
        # пауки на нитях
        for fx, fy in [(.22, .74), (.80, .84)]:
          sx, sy = x + w * fx, y + h * fy
          Color(.9, .9, .95, .7); Line(points=[sx, y + h, sx, sy + dp(7)], width=dp(.9))
          Color(.02, 0, .03, 1); Ellipse(pos=(sx - dp(7), sy - dp(7)), size=(dp(14), dp(15))); Ellipse(pos=(sx - dp(4), sy + dp(5)), size=(dp(8), dp(8)))
          for k in range(4):
            Line(points=[sx - dp(5), sy + dp(k * 2 - 3), sx - dp(14), sy + dp(k * 4 - 8)], width=dp(1))
            Line(points=[sx + dp(5), sy + dp(k * 2 - 3), sx + dp(14), sy + dp(k * 4 - 8)], width=dp(1))
          Color(1, .1, .1, 1); Ellipse(pos=(sx - dp(3), sy + dp(8)), size=(dp(2.2), dp(2.2))); Ellipse(pos=(sx + dp(1), sy + dp(8)), size=(dp(2.2), dp(2.2)))
      elif self.wallpaper == "newyear":
        rnd = random.Random(52)
        mm = min(w, h)
        Color(.9, .95, 1, .85); Ellipse(pos=(x + w * .64, y + h * .66), size=(mm * .20, mm * .20))
        Color(.01, .03, .12, 1); Ellipse(pos=(x + w * .69, y + h * .69), size=(mm * .18, mm * .18))
        for i in range(70):  # снег
          Color(1, 1, 1, rnd.uniform(.25, .9))
          r = rnd.uniform(1.2, 4) * dp(1)
          Ellipse(pos=(x + rnd.random() * w, y + rnd.random() * h), size=(r, r))
        # ёлки
        for fx, fh in [(.12, .38), (.34, .52), (.78, .44), (.60, .30)]:
          tx = x + w * fx; tw = w * .20
          Color(.25, .15, .07, 1); Rectangle(pos=(tx - tw * .06, y + h * .08), size=(tw * .12, h * .05))
          for lvl in range(3):
            by = y + h * (.10 + fh * (.12 + lvl * .26))
            ww = tw * (1 - lvl * .24)
            Color(.04, .30 + lvl * .06, .16, 1); Triangle(points=[tx - ww / 2, by, tx + ww / 2, by, tx, by + h * fh * .36])
            Color(1, 1, 1, .85); Triangle(points=[tx - ww * .17, by + h * fh * .25, tx + ww * .17, by + h * fh * .25, tx, by + h * fh * .36])
          for k in range(5):
            Color(*[(1, .2, .2), (1, .85, .2), (.3, .6, 1)][k % 3], 1)
            Ellipse(pos=(tx + (k - 2) * tw * .09, y + h * (.14 + fh * .12 * (k % 3 + 1))), size=(dp(5), dp(5)))
        # сугробы
        Color(.92, .96, 1, 1); Ellipse(pos=(x - w * .2, y - h * .08), size=(w * .8, h * .18)); Ellipse(pos=(x + w * .3, y - h * .10), size=(w * .9, h * .20))
        # гирлянда сверху
        pts = []
        for i in range(0, 21):
          px = x + w * i / 20
          pts += [px, y + h * (.97 - .035 * math.sin(math.pi * (i % 5) / 4))]
        Color(.1, .35, .15, 1); Line(points=pts, width=dp(1.2))
        for i in range(0, 21, 2):
          px = x + w * i / 20; py = y + h * (.97 - .035 * math.sin(math.pi * (i % 5) / 4))
          Color(*[(1, .25, .25), (1, .9, .25), (.35, .7, 1), (.45, 1, .5)][(i // 2) % 4], .95)
          Ellipse(pos=(px - dp(4), py - dp(9)), size=(dp(8), dp(10)))
      elif self.wallpaper == "birthday":
        rnd = random.Random(73)
        mm = min(w, h)
        Color(1, .9, .4, .07)
        Triangle(points=[x + w * .5, y, x + w * .05, y + h, x + w * .35, y + h]); Triangle(points=[x + w * .5, y, x + w * .65, y + h, x + w * .95, y + h])
        palette = [(1, .3, .4), (1, .85, .2), (.3, .8, 1), (.5, 1, .5), (.9, .4, 1), (1, .6, .2)]
        for i in range(90):  # конфетти
          Color(*palette[rnd.randrange(6)], rnd.uniform(.45, .95))
          rw = rnd.uniform(2, 6) * dp(1)
          if i % 3:
            Rectangle(pos=(x + rnd.random() * w, y + rnd.random() * h), size=(rw, rw * .5))
          else:
            Ellipse(pos=(x + rnd.random() * w, y + rnd.random() * h), size=(rw, rw))
        # шарики
        for fx, fy, col in [(.12, .30, (1, .3, .4)), (.28, .45, (.3, .8, 1)), (.50, .28, (1, .85, .2)), (.70, .48, (.5, 1, .5)), (.88, .32, (.9, .4, 1))]:
          bw = mm * .15; bh = bw * 1.25; bx = x + w * fx; by = y + h * fy
          Color(.9, .9, 1, .6); Line(points=[bx + bw / 2, by, bx + bw * .42, by - h * .16, bx + bw * .58, by - h * .30], width=dp(1))
          Color(*col, .95); Ellipse(pos=(bx, by), size=(bw, bh))
          Color(1, 1, 1, .45); Ellipse(pos=(bx + bw * .18, by + bh * .55), size=(bw * .2, bh * .22))
          Color(*col, .95); Triangle(points=[bx + bw * .5, by + dp(1), bx + bw * .38, by - bw * .16, bx + bw * .62, by - bw * .16])
        # флажки
        Color(.95, .95, 1, .9); Line(points=[x, y + h * .95, x + w * .5, y + h * .90, x + w, y + h * .95], width=dp(1.1))
        for i in range(11):
          t = i / 10; fxp = x + w * t; fyp = y + h * (.95 - .05 * math.sin(math.pi * t))
          Color(*palette[i % 6], 1)
          Triangle(points=[fxp - dp(9), fyp, fxp + dp(9), fyp, fxp, fyp - dp(20)])
      else: # cosmic: glowing purple-blue diagonal burst
        for i in range(7):
          Color(.15,.35,1,.12+i*.045); Line(points=[x+w*(.08+i*.04),y+h*.12,x+w*.48,y+h*.48,x+w*(.75+i*.025),y+h*.88],width=dp(2+i*.5))
        Color(.7,.12,1,.45); Ellipse(pos=(x+w*.38,y+h*.35),size=(w*.24,h*.24))
        Color(.08,.25,1,.5); Ellipse(pos=(x+w*.42,y+h*.39),size=(w*.16,h*.16))
      if self.rounded_preview:
        StencilUnUse()
        StencilPop()
        Color(.48, .42, .72, .95)
        Line(rounded_rectangle=(x, y, w, h, dp(12)), width=dp(0.8))


def make_game_background(theme="fire", style="particles_up", **kwargs):
  """Фон экрана: статичная картинка текущей темы оформления (меняется только в админ-панели)."""
  bg = StaticWallpaperBg(current_theme()["wallpaper"], **kwargs)
  try:
    _THEME_BGS.add(bg)
  except Exception:
    pass
  return bg


# ============================================================
# ШАХТА (вместо тапалки): монеты копятся сами, даже пока тебя нет в игре
# ============================================================
MINE_MAX_LEVEL = 50


PRESTIGE_LEVEL = 25      # с этого уровня доступен престиж
PRESTIGE_BONUS = 0.25    # +25% к добыче за каждый престиж, навсегда


def mine_prestige(data):
  try:
    return max(0, int(data.get("mine_prestige", 0) or 0))
  except Exception:
    return 0


def mine_income_per_hour(level, prestige=0):
  return int(round(100 * (max(1, int(level)) ** 1.3) * (1 + PRESTIGE_BONUS * max(0, int(prestige)))))


def mine_capacity_hours(level, vip=False):
  """Сколько часов шахта копит добычу, пока ты не заберёшь её (от 4 до 12 часов, у VIP вдвое больше)."""
  base = min(12, 4 + (max(1, int(level)) - 1) // 3)
  return base * 2 if vip else base


def mine_upgrade_cost(level):
  return int(round(1500 * (max(1, int(level)) ** 1.8) / 50.0)) * 50


def mine_level(data):
  try:
    lvl = int(data.get("mine_level", 1) or 1)
  except Exception:
    lvl = 1
  return max(1, min(MINE_MAX_LEVEL, lvl))


def mine_boost(data):
  """Множитель добычи: бывший «буст тапалки» из магазина (и VIP x5)."""
  try:
    return max(1, int(data.get("tap_boost", 1) or 1))
  except Exception:
    return 1


def mine_pending(data, now=None):
  """Возвращает (базовая добыча, часов накоплено, лимит часов, добыча в час) без учёта бустов."""
  now = time.time() if now is None else now
  level = mine_level(data)
  try:
    last = float(data.get("mine_last", 0) or 0)
  except Exception:
    last = 0.0
  if last <= 0 or last > now:
    last = now
  cap = mine_capacity_hours(level, bool(data.get("vip", False)))
  hours = min(float(cap), max(0.0, (now - last) / 3600.0))
  per_hour = mine_income_per_hour(level, mine_prestige(data))
  return int(hours * per_hour), hours, cap, per_hour


def mine_collect(data, allow_crit=True, force=False):
  """Начисляет накопленную добычу в словарь data. Возвращает (получено, был_крит)."""
  now = time.time()
  base = mine_pending(data, now)[0]
  earned = base * mine_boost(data)
  crit = False
  if earned > 0 and allow_crit:
    chance = max(0, min(15, int(data.get("crit_chance", 0) or 0)))
    crit = random.randint(1, 100) <= chance
    if crit:
      earned *= 2
  data["coins"] = int(data.get("coins", 0) or 0) + earned
  if earned > 0 or force:
    data["mine_last"] = now
  if earned > 0:
    data["mine_total"] = int(data.get("mine_total", 0) or 0) + earned
  return earned, crit


def mine_roll_event(earned):
  """Случайная находка при сборе добычи. Возвращает (бонус_монет, кейс_или_None, текст)."""
  if earned <= 0:
    return 0, None, ""
  r = random.random()
  if r < 0.01:
    case = random.choice(list(CASE_INFO.keys()))
    return 0, case, "Находка! Бесплатный кейс: " + CASE_INFO[case]["label"]
  if r < 0.04:
    return earned * 2, None, "Сокровище! Бонус +200%"
  if r < 0.16:
    return earned // 2, None, "Золотая жила! Бонус +50%"
  return 0, None, ""


def _fmt_num(n):
  return f"{int(n):,}".replace(",", " ")


class MineScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.theme = None
    self.art_widget = None
    self._bg_widget = None
    self._bg_key = None
    self._refresh_event = None
    self._prestige_armed = 0.0
    self._apply_background(load_data())

    root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8), size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))
    self.coins_label = Label(text="Монеты: 0", font_size=dp(26), bold=True,
                             size_hint_y=None, height=dp(42), color=(1, .86, .38, 1))
    root.add_widget(self.coins_label)
    self.level_label = Label(text="", font_size=dp(17), bold=True, size_hint_y=None, height=dp(28),
                             color=(.6, .9, 1, 1))
    root.add_widget(self.level_label)
    self.art_holder = FloatLayout(size_hint_y=None, height=dp(150))
    root.add_widget(self.art_holder)
    self.rate_label = Label(text="", font_size=dp(13), size_hint_y=None, height=dp(22),
                            color=(.9, .94, 1, 1))
    root.add_widget(self.rate_label)
    self.store_label = Label(text="", font_size=dp(16), bold=True, size_hint_y=None, height=dp(26))
    root.add_widget(self.store_label)
    self.store_bar = ProgressBar(max=1, value=0, size_hint_y=None, height=dp(10))
    root.add_widget(self.store_bar)
    self.eta_label = Label(text="", font_size=dp(12), size_hint_y=None, height=dp(20),
                           color=(.78, .84, .95, 1))
    root.add_widget(self.eta_label)
    self.gain_label = Label(text="", font_size=dp(18), bold=True, size_hint_y=None, height=dp(28),
                            color=(.5, 1, .6, 1), opacity=0)
    root.add_widget(self.gain_label)
    self.claim_btn = GlassButton(text="СОБРАТЬ", height=dp(58))
    self.claim_btn.font_size = dp(20); self.claim_btn.bold = True
    self.claim_btn.bind(on_press=self._claim)
    root.add_widget(self.claim_btn)
    self.upgrade_btn = GlassButton(text="Улучшить шахту", height=dp(50))
    self.upgrade_btn.font_size = dp(14)
    self.upgrade_btn.bind(on_press=self._upgrade)
    root.add_widget(self.upgrade_btn)
    self.prestige_btn = GlassButton(text="Престиж", height=dp(0))
    self.prestige_btn.font_size = dp(13)
    self.prestige_btn.opacity = 0
    self.prestige_btn.disabled = True
    self.prestige_btn.bind(on_press=self._prestige)
    root.add_widget(self.prestige_btn)
    self.msg_label = Label(text="", font_size=dp(12), size_hint_y=None, height=dp(22),
                           color=(1, .8, .5, 1))
    root.add_widget(self.msg_label)
    btn_back = GlassButton(text="Назад в меню", height=dp(46))
    btn_back.bind(on_press=lambda *_: self.manager.go_to("main"))
    root.add_widget(btn_back)
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True, bar_width=dp(4))
    scroll.add_widget(root)
    self.add_widget(scroll)

  # ---------- фон и оформление (тема задаётся только в админ-панели) ----------
  def _apply_background(self, data=None):
    key = current_theme_key()
    if key == self._bg_key and self._bg_widget is not None:
      return
    if self._bg_widget is not None:
      try:
        self.remove_widget(self._bg_widget)
      except Exception:
        pass
    self._bg_widget = make_game_background()
    self.add_widget(self._bg_widget, index=len(self.children))
    self._bg_key = key

  def _set_art(self, icon_kind):
    if icon_kind == self.theme and self.art_widget is not None:
      return
    self.theme = icon_kind
    try:
      if self.art_widget is not None:
        self.art_holder.remove_widget(self.art_widget)
    except Exception:
      pass
    self.art_widget = make_mine_icon(icon_kind, dp(130))
    self.art_widget.pos_hint = {"center_x": 0.5, "center_y": 0.5}
    self.art_holder.add_widget(self.art_widget)

  # ---------- обновление цифр ----------
  def _refresh(self, *_):
    data = load_data()
    if not data:
      return
    level = mine_level(data)
    boost = mine_boost(data)
    base, hours, cap, per_hour = mine_pending(data)
    pending = base * boost
    capacity = int(per_hour * cap * boost)
    crit = max(0, min(15, int(data.get("crit_chance", 0) or 0)))
    self.coins_label.text = f"Монеты: {_fmt_num(data.get('coins', 0))}"
    self.level_label.text = f"Шахта • уровень {level}"
    prestige = mine_prestige(data)
    rate = f"Добыча: {_fmt_num(per_hour * boost)} монет/час"
    if boost > 1:
      rate += f"  (буст x{boost})"
    if prestige:
      rate += f"  • престиж {prestige}"
    if crit:
      rate += f"  • шанс x2: {crit}%"
    if data.get("vip", False):
      rate += "  • VIP: хранилище x2"
    self.rate_label.text = rate
    self.store_label.text = f"Накоплено: {_fmt_num(pending)} / {_fmt_num(capacity)}"
    self.store_bar.max = float(cap)
    self.store_bar.value = hours
    if hours >= cap:
      self.eta_label.text = "Хранилище заполнено — собери добычу!"
    else:
      left = int((cap - hours) * 3600)
      self.eta_label.text = f"Хранилище заполнится через {left // 3600} ч {(left % 3600) // 60:02d} мин"
    if pending >= 1:
      self.claim_btn.text = f"СОБРАТЬ  +{_fmt_num(pending)}"
      self.claim_btn.disabled = False
    else:
      self.claim_btn.text = "Пока нечего собирать"
      self.claim_btn.disabled = True
    if level >= MINE_MAX_LEVEL:
      self.upgrade_btn.text = "Максимальный уровень шахты"
      self.upgrade_btn.disabled = True
    else:
      self.upgrade_btn.text = f"Улучшить до ур. {level + 1} — {_fmt_num(mine_upgrade_cost(level))} монет"
      self.upgrade_btn.disabled = False
    if level >= PRESTIGE_LEVEL:
      self.prestige_btn.height = dp(46); self.prestige_btn.opacity = 1; self.prestige_btn.disabled = False
      if time.time() - self._prestige_armed <= 5:
        self.prestige_btn.text = "Подтвердить престиж? Нажми ещё раз"
      else:
        self.prestige_btn.text = f"Престиж: сброс до ур. 1, +{int(PRESTIGE_BONUS * 100)}% добычи навсегда"
    else:
      self.prestige_btn.height = dp(0); self.prestige_btn.opacity = 0; self.prestige_btn.disabled = True

  def _show_gain(self, text, color=(.5, 1, .6, 1)):
    Animation.cancel_all(self.gain_label)
    self.gain_label.text = text
    self.gain_label.color = color
    self.gain_label.opacity = 1
    Animation(opacity=0, duration=2.0, t="in_quad").start(self.gain_label)

  # ---------- действия ----------
  def _claim(self, *_):
    data = load_data()
    if not data:
      return
    earned, crit = mine_collect(data, allow_crit=True)
    if earned <= 0:
      self._refresh()
      return
    data["mine_claims"] = int(data.get("mine_claims", 0) or 0) + 1
    bonus, case, event_text = mine_roll_event(earned)
    if bonus:
      data["coins"] = int(data.get("coins", 0) or 0) + bonus
      data["mine_total"] = int(data.get("mine_total", 0) or 0) + bonus
    if case:
      inv = list(data.get("inventory", []))
      inv.append({"type": "case", "kind": case, "case": case})
      data["inventory"] = inv
    save_data(data)
    GameAudio.play("coin")
    total = earned + bonus
    self.msg_label.text = event_text
    self._show_gain(f"КРИТ! +{_fmt_num(total)} (x2)" if crit else f"+{_fmt_num(total)} монет",
                    (1, .85, .3, 1) if crit else (.5, 1, .6, 1))
    self._refresh()

  def _upgrade(self, *_):
    data = load_data()
    if not data:
      return
    level = mine_level(data)
    if level >= MINE_MAX_LEVEL:
      return
    cost = mine_upgrade_cost(level)
    pending = mine_pending(data)[0] * mine_boost(data)
    if int(data.get("coins", 0) or 0) + pending < cost:
      self.msg_label.text = "Не хватает монет для улучшения"
      return
    # Накопленное забираем до улучшения, чтобы новый уровень не пересчитывал старое время.
    mine_collect(data, allow_crit=False, force=True)
    data["coins"] = int(data.get("coins", 0) or 0) - cost
    data["mine_level"] = level + 1
    data["mine_best_level"] = max(int(data.get("mine_best_level", 0) or 0), level + 1)
    save_data(data)
    self.msg_label.text = f"Шахта улучшена до уровня {level + 1}!"
    self._refresh()

  def _prestige(self, *_):
    data = load_data()
    if not data or mine_level(data) < PRESTIGE_LEVEL:
      return
    now = time.time()
    if now - self._prestige_armed > 5:  # первое нажатие только «взводит» кнопку
      self._prestige_armed = now
      self._refresh()
      return
    self._prestige_armed = 0.0
    mine_collect(data, allow_crit=False, force=True)
    data["mine_best_level"] = max(int(data.get("mine_best_level", 0) or 0), mine_level(data))
    data["mine_level"] = 1
    data["mine_prestige"] = mine_prestige(data) + 1
    save_data(data)
    self.msg_label.text = f"Престиж {data['mine_prestige']}! Добыча навсегда +{int(PRESTIGE_BONUS * 100 * data['mine_prestige'])}%"
    self._refresh()

  def on_pre_enter(self, *args):
    data = load_data()
    if data and not data.get("mine_last"):
      data["mine_last"] = time.time()
      save_data(data)
    self._apply_background(data)
    self._set_art(current_theme()["icon"])
    self.msg_label.text = ""
    self._refresh()
    if self._refresh_event is None:
      self._refresh_event = Clock.schedule_interval(self._refresh, 1)

  def on_leave(self, *args):
    if self._refresh_event is not None:
      try:
        self._refresh_event.cancel()
      except Exception:
        pass
      self._refresh_event = None


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
    self.bg_widget = make_game_background(None, "corners")
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
    # Пока оставляем в магазине ровно четыре кейса; систему кейсов в инвентаре не добавляем.
    for case_id in ["cats", "planets", "ice", "fire"]:
      grid.add_widget(CaseMiniCard(case_id, on_open=self._open_case))
    content.add_widget(grid)
    content.add_widget(Label(text="", size_hint_y=None, height=dp(5)))
    btn_back = GlassButton(text="Назад", height=dp(55))
    btn_back.bind(on_press=lambda x: self.manager.go_to('main'))
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
    self.opening_owned_case = False
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
    self._bg_widget = make_game_background(theme, style)
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
    btn_back.bind(on_press=lambda x: self.manager.go_to('cases'))
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
    if getattr(self, "opening_owned_case", False):
      self.opening_owned_case = False
      data = load_data()
      inventory = list(data.get("inventory", []))
      for i, item in enumerate(inventory):
        if item.get("type") == "case" and item.get("kind") == self.case_id:
          inventory.pop(i)
          data["inventory"] = inventory
          save_data(data)
          self._do_spin(1, 0)
          return
      self.result_label.text = "Такого кейса больше нет в инвентаре"
      return
    GameAudio.play('case_open')
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
    GameAudio.play('case_spin')
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
        GameAudio.play('case_reveal')
        self.result_label.text = f"Выпало: {get_name(item_type, self._final)}"
        self.spinning = False
        popup = PopupResult([self._final], item_type, on_close=self._close_popup,
                            on_sell=self._sell_results, on_spin_again=self._spin_again)
        self.add_widget(popup)
        self.popup = popup
      self.roulette.start_spin(seq, on_finish)
    else:
      GameAudio.play('case_reveal')
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
    self.bg_widget = make_game_background(None, "particles_up")
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
    btn_back.bind(on_press=lambda x: self.manager.go_to('main'))
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
    category_targets = {"category_cases": "cases_inventory",
                        "category_avatars": "avatars_inventory",
                        "category_frames": "frames_inventory"}
    if f in category_targets:
      self._close_filter()
      self.manager.go_to(category_targets[f])
      return
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
    title = Label(text="Фильтр инвентаря", font_size=dp(18), bold=True,
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
    options = [("all", "Все предметы"),
               ("category_cases", "Кейсы"),
               ("category_avatars", "Аватарки"),
               ("category_frames", "Рамки")]
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
    self.bg_widget = make_game_background(None, "rank_sticks")
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
    btn_back.bind(on_press=lambda x: self.manager.go_to('main'))
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
class ProfileDecorBanner(BoxLayout):
  """Небольшая декоративная плашка профиля, нарисованная примитивами Kivy."""
  def __init__(self, title="PLAYER CARD", subtitle="ЛИЧНОЕ ДЕЛО ИГРОКА", **kwargs):
    super().__init__(orientation="vertical", padding=(dp(16), dp(8)), spacing=dp(2), **kwargs)
    self.size_hint_y = None
    self.height = dp(64)
    with self.canvas.before:
      _fill, _edge, _glow, _shadow = _theme_button_palette()
      Color(*_shadow)
      self._panel = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
      Color(*_edge)
      self._outline = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(15)), width=1.15)
      Color(0.95, 0.72, 0.28, 0.95)
      self._diamond1 = Line(points=[0,0, 0,0, 0,0, 0,0], close=True, width=1.4)
      Color(0.38, 0.85, 1.0, 0.95)
      self._diamond2 = Line(points=[0,0, 0,0, 0,0, 0,0], close=True, width=1.2)
      Color(0.72, 0.52, 1.0, 0.95)
      self._diamond3 = Line(points=[0,0, 0,0, 0,0, 0,0], close=True, width=1.2)
    self.bind(pos=self._update_art, size=self._update_art)
    self.add_widget(Label(text=title, bold=True, font_size=dp(14), color=(0.96,0.97,1,1), halign="left", valign="middle"))
    self.add_widget(Label(text=subtitle, font_size=dp(9), color=(0.48,0.82,1,1), halign="left", valign="middle"))
  def _update_art(self, *_):
    self._panel.pos = self.pos
    self._panel.size = self.size
    self._outline.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(15))
    cy = self.center_y
    x1 = self.right - dp(48); x2 = self.right - dp(31); x3 = self.right - dp(14)
    r = dp(5)
    self._diamond1.points = [x1,cy+r, x1+r,cy, x1,cy-r, x1-r,cy]
    self._diamond2.points = [x2,cy+r, x2+r,cy, x2,cy-r, x2-r,cy]
    self._diamond3.points = [x3,cy+r, x3+r,cy, x3,cy-r, x3-r,cy]


class ProfileScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.bg_widget = make_game_background(None, "particles_up")
    self.add_widget(self.bg_widget)

    data = load_data()
    mmr = data.get("mmr", 0)
    rank_idx = rank_index_by_mmr(mmr)
    avatar_key = data.get("avatar", "cat_orange")
    frame_key = data.get("frame", "none")
    nickname = str(data.get("nickname", "Игрок"))

    desktop_mode = data.get("interface_mode", "mobile") == "desktop"
    root = BoxLayout(orientation='vertical', padding=dp(15 if not desktop_mode else 24), spacing=dp(8),
             size_hint_x=1 if not desktop_mode else None,
             width=Window.width if not desktop_mode else min(Window.width * 0.72, dp(900)))
    if desktop_mode:
      root.pos_hint = {"center_x": 0.5}
    root.add_widget(Label(text="Профиль", font_size=dp(24), bold=True,
                size_hint_y=None, height=dp(36)))
    mode = data.get("interface_mode", "mobile")
    mode_btn = GlassButton(text="Версия интерфейса: " + ("Мобильная" if mode == "mobile" else "ПК"), height=dp(40))
    mode_btn.font_size = dp(12)
    def toggle_interface_mode(*_):
      fresh = load_data()
      fresh["interface_mode"] = "desktop" if fresh.get("interface_mode", "mobile") == "mobile" else "mobile"
      save_data(fresh)
      self._build_ui()
    mode_btn.bind(on_press=toggle_interface_mode)
    root.add_widget(mode_btn)
    root.add_widget(ProfileDecorBanner(
      title="VIP PROFILE" if data.get("vip", False) else "PLAYER CARD",
      subtitle="РАДУЖНЫЙ НИК АКТИВЕН" if data.get("vip", False) else "ТВОЙ ПРОФИЛЬ • ТВОИ ДОСТИЖЕНИЯ"))

    top = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(228),
             spacing=dp(10), padding=dp(4))
    av_holder = FloatLayout(size_hint_x=None, width=dp(150))
    frame_art = FrameArt(frame_key, dp(164))
    frame_art.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
    av_holder.add_widget(frame_art)
    avatar_art = avatar_to_art(avatar_key, dp(70))
    if avatar_art is not None:
      avatar_art.size_hint = (None, None)
      avatar_art.size = (dp(54), dp(54))
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
    profile_name_row = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint_y=None, height=dp(30))
    NickLabel = RainbowNickLabel if data.get('vip', False) else Label
    nick_label_kwargs = {"rainbow_style": data.get("rainbow_nick_style", "classic")} if data.get("vip", False) else {}
    profile_name_label = NickLabel(**nick_label_kwargs, text=nickname, font_size=dp(16), bold=True, shorten=True, shorten_from='right',
                color=(1, 1, 1, 1), halign='center', valign='middle', size_hint_x=1)
    profile_name_label.bind(size=lambda w, v: setattr(w, 'text_size', v))
    profile_name_row.add_widget(profile_name_label)
    info.add_widget(profile_name_row)
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
    nick_btn.bind(on_press=lambda x: self.manager.go_to('nickname'))
    info.add_widget(nick_btn)
    top.add_widget(info)
    root.add_widget(top)

    # Статистика профиля удалена по просьбе пользователя.

    change_av = GlassButton(text="Купить аватарку", height=dp(44))
    change_av.bind(on_press=lambda x: self.manager.go_to('avatar_select'))
    root.add_widget(change_av)
    change_fr = GlassButton(text="Купить рамку", height=dp(44))
    change_fr.bind(on_press=lambda x: self.manager.go_to('frames'))
    root.add_widget(change_fr)

    # Убрана лишняя панель «ТВОЙ ПУТЬ К ВЕРШИНЕ» по просьбе пользователя.
    rank_btn = GlassButton(text="Открыть ранги", height=dp(42))
    rank_btn.bind(on_press=lambda *_: self.manager.go_to('rank_select'))
    root.add_widget(rank_btn)
    match_btn = GlassButton(text="Рейтинговый матч: заработать MMR", height=dp(44))
    match_btn.bind(on_press=lambda *_: self.manager.go_to('ranked'))
    root.add_widget(match_btn)
    shop_btn = GlassButton(text="Магазин бустов и медалей", height=dp(42))
    shop_btn.bind(on_press=lambda *_: self.manager.go_to('shop'))
    root.add_widget(shop_btn)
    daily_btn = GlassButton(text="Ежедневный подарок", height=dp(42))
    daily_btn.bind(on_press=lambda *_: self.manager.go_to('daily_reward'))
    root.add_widget(daily_btn)
    promo_btn = GlassButton(text="Промокод", height=dp(42))
    promo_btn.bind(on_press=lambda *_: self.manager.go_to('promo'))
    root.add_widget(promo_btn)
    logout_btn = GlassButton(text="Выйти из аккаунта", height=dp(42))
    logout_btn.bind(on_press=lambda *_: self._logout())
    root.add_widget(logout_btn)
    btn_back = GlassButton(text="Назад", height=dp(46))
    btn_back.background_normal = ''
    btn_back.background_down = ''
    btn_back.background_disabled_normal = ''
    btn_back.background_color = (0, 0, 0, 0)
    btn_back.bind(on_press=lambda x: self.manager.go_to('main'))
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

  def _cycle_rainbow_nick_style(self):
    data = load_data()
    if not data.get("vip", False):
      return
    styles = list(RAINBOW_NICK_STYLES.keys())
    current = str(data.get("rainbow_nick_style", "classic"))
    if current not in styles:
      current = "classic"
    data["rainbow_nick_style"] = styles[(styles.index(current) + 1) % len(styles)]
    save_data(data)
    self._build_ui()

  def on_pre_enter(self, *args):
    self._build_ui()


  def _logout(self):
    logout_account()
    self.manager.current = "auth"

class DailyRewardScreen(Screen):
  """Ежедневный бесплатный подарок с сохранением даты и серии входов."""
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.build_ui()

  def build_ui(self):
    self.clear_widgets()
    self.add_widget(make_game_background(None, "particles_up"))
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
    back.bind(on_press=lambda *_: self.manager.go_to('profile'))
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
  """Unique hand-drawn vector textures for each store item."""
  def __init__(self, kind='boost', accent=(0.25, 0.72, 1.0), **kwargs):
    super().__init__(**kwargs)
    self.kind = kind
    self.accent = tuple(accent[:3])
    self.bind(pos=self.redraw, size=self.redraw)
    self.redraw()

  def redraw(self, *args):
    self.canvas.clear()
    x, y = self.pos; w, h = self.size
    cx, cy = x + w * .5, y + h * .5
    r = max(dp(3), min(w, h) * .36)
    ar, ag, ab = self.accent
    with self.canvas:
      # Glassy collectible plate with a subtle double border.
      Color(.035, .055, .10, .98)
      RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(13)])
      Color(ar, ag, ab, .24)
      RoundedRectangle(pos=(x+dp(3), y+dp(3)), size=(max(0,w-dp(6)), max(0,h-dp(6))), radius=[dp(10)])
      Color(ar, ag, ab, .95)
      Line(rounded_rectangle=(x, y, w, h, dp(13)), width=dp(1.25))
      Color(1, 1, 1, .13)
      Line(points=[x+dp(10), y+h-dp(8), x+w*.45, y+h-dp(8)], width=dp(1))

      if self.kind == 'vip':
        # Gold crown inside a faceted medallion.
        Color(1.0, .63, .08, .22); Ellipse(pos=(cx-r*1.12,cy-r*1.12),size=(r*2.24,r*2.24))
        Color(1.0,.78,.22,1)
        Line(points=[cx-r*.8,cy-r*.35,cx-r*.63,cy+r*.48,cx-r*.2,cy+r*.08,cx,cy+r*.58,cx+r*.25,cy+r*.08,cx+r*.64,cy+r*.48,cx+r*.8,cy-r*.35,cx-r*.8,cy-r*.35],close=True,width=dp(2))
        Line(points=[cx-r*.62,cy-r*.52,cx+r*.62,cy-r*.52],width=dp(2))
        for px in (cx-r*.63,cx,cx+r*.64):
          Ellipse(pos=(px-dp(2),cy+r*.48-dp(2)),size=(dp(4),dp(4)))
      elif self.kind == 'boost2':
        Color(.22,.78,1,1)
        # Lightning shard with two speed trails.
        Line(points=[cx+r*.1,cy+r*.95,cx-r*.42,cy+r*.05,cx-r*.02,cy+r*.05,cx-r*.18,cy-r*.82,cx+r*.5,cy+r*.08,cx+r*.12,cy+r*.08,cx+r*.1,cy+r*.95],close=True,width=dp(2))
        Line(points=[cx-r*.9,cy+r*.4,cx-r*.57,cy+r*.4],width=dp(1.5))
        Line(points=[cx-r*.85,cy-r*.05,cx-r*.55,cy-r*.05],width=dp(1.5))
      elif self.kind == 'boost4':
        Color(.62,.42,1,1)
        # Four-point power core and orbital ring.
        Ellipse(pos=(cx-r*.58,cy-r*.58),size=(r*1.16,r*1.16))
        Color(.08,.08,.2,1); Ellipse(pos=(cx-r*.36,cy-r*.36),size=(r*.72,r*.72))
        Color(.82,.72,1,1)
        Line(points=[cx,cy+r*.76,cx+r*.2,cy+r*.2,cx+r*.76,cy,cx+r*.2,cy-r*.2,cx,cy-r*.76,cx-r*.2,cy-r*.2,cx-r*.76,cy,cx-r*.2,cy+r*.2,cx,cy+r*.76],width=dp(2))
      elif self.kind == 'boost6':
        Color(1,.35,.22,1)
        # Triple flame streaks and an orange core.
        for i, scale in enumerate((.72,.48,.25)):
          Line(points=[cx-r*scale,cy-r*.58,cx-r*scale*.45,cy+r*.05,cx-r*scale*.15,cy+r*.68,cx+r*scale*.4,cy+r*.12],width=dp(2+i*.2))
        Color(1,.76,.18,.9); Ellipse(pos=(cx-dp(4),cy-dp(4)),size=(dp(8),dp(8)))
      elif self.kind == 'crit':
        Color(.3,1,.73,1)
        # Precision reticle around a diamond.
        Line(circle=(cx,cy,r*.72),width=dp(1.5))
        Line(points=[cx,cy+r*.5,cx+r*.38,cy,cx,cy-r*.5,cx-r*.38,cy,cx,cy+r*.5],close=True,width=dp(2))
        for a in (0,90,180,270):
          rad=math.radians(a); ex=cx+math.cos(rad)*r*.92; ey=cy+math.sin(rad)*r*.92
          Line(points=[cx+math.cos(rad)*r*.72,cy+math.sin(rad)*r*.72,ex,ey],width=dp(1.5))
      else:
        # Medal: layered enamel coin with a unique star-cut center.
        Color(ar,ag,ab,1); Ellipse(pos=(cx-r*.78,cy-r*.78),size=(r*1.56,r*1.56))
        Color(.04,.07,.12,1); Ellipse(pos=(cx-r*.56,cy-r*.56),size=(r*1.12,r*1.12))
        Color(1,.86,.36,1)
        pts=[]
        for i in range(10):
          a=math.pi/2+i*math.pi/5
          rr=r*(.46 if i%2==0 else .22)
          pts.extend([cx+math.cos(a)*rr,cy+math.sin(a)*rr])
        Line(points=pts+[pts[0],pts[1]],width=dp(1.7))


class ShopScreen(Screen):
  BOOSTS = [(2, 5000), (4, 25000), (6, 100000)]
  # Единственная новая медаль в магазине — бесплатная.
  FREE_MEDAL = "Знак точности"
  LEGACY_MEDALS = ["Золотая звезда", "Лунная медаль", "Королевский знак"]

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.build_ui()

  def _item_card(self, title, description, price, action, accent=(0.25, 0.72, 1.0, 1), owned=False, button_text=None):
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
    if title.startswith("VIP"):
      art_kind = 'vip'
    elif "x2" in title or "x3" in title:
      art_kind = 'boost2'
    elif "x4" in title:
      art_kind = 'boost4'
    elif "x6" in title:
      art_kind = 'boost6'
    elif "Критический" in title:
      art_kind = 'crit'
    else:
      art_kind = 'medal'
    art = ShopItemArt(art_kind, accent=accent, size_hint=(1, 1))
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

    buy = GlassButton(text=(button_text if button_text is not None else ("Установлено" if owned else f"{price:,} монет".replace(',', ' '))), height=dp(42))
    buy.size_hint_x = None
    buy.width = dp(104)
    buy.font_size = dp(11)
    buy.disabled = owned
    buy.bind(on_press=action)
    card.add_widget(buy)
    return card

  def build_ui(self):
    self.clear_widgets()
    self.add_widget(make_game_background(None, "particles_up"))
    root = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(7))
    root.add_widget(Label(text="МАГАЗИН", font_size=dp(25), bold=True, size_hint_y=None, height=dp(42)))
    data = load_data()
    root.add_widget(Label(text=f"Баланс: {data.get('coins', 0)} монет", size_hint_y=None, height=dp(26),
               color=(1, .85, .35, 1)))
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True, bar_width=dp(4))
    items = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(9), padding=dp(4))
    items.bind(minimum_height=items.setter('height'))
    current = int(data.get('tap_boost', 1))
    heading = Label(text=f"УЛУЧШЕНИЯ ШАХТЫ\nТекущий множитель добычи: x{current}",
                size_hint_y=None, height=dp(52), bold=True, halign='center', valign='middle',
                font_size=dp(15), text_size=(Window.width - dp(52), None))
    heading.bind(size=lambda w, _v: setattr(w, 'text_size', (max(dp(100), w.width - dp(8)), None)))
    items.add_widget(heading)
    active_offers = _load_admin_settings().get("offers", [])
    if active_offers:
      items.add_widget(Label(text="АКЦИИ ОТ АДМИНИСТРАЦИИ", size_hint_y=None, height=dp(34), bold=True, font_size=dp(15), color=(0.78,0.90,1,1)))
      for offer in active_offers:
        promo = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(76), spacing=dp(8), padding=dp(8))
        with promo.canvas.before:
          Color(0.12,0.20,0.32,0.92); promo_bg=RoundedRectangle(pos=promo.pos,size=promo.size,radius=[dp(15)])
          Color(0.40,0.78,1.0,0.68); promo_edge=Line(rounded_rectangle=(promo.x,promo.y,promo.width,promo.height,dp(15)),width=dp(1))
        def sync_promo(widget,*_):
          promo_bg.pos=widget.pos; promo_bg.size=widget.size; promo_edge.rounded_rectangle=(widget.x,widget.y,widget.width,widget.height,dp(15))
        promo.bind(pos=sync_promo,size=sync_promo)
        desc=Label(text=f"{offer.get('title','Акция')}\n{offer.get('description','')}",font_size=dp(11),halign="left",valign="middle")
        desc.bind(size=lambda w,v:setattr(w,"text_size",(max(dp(40),v[0]-dp(6)),max(dp(30),v[1]-dp(4)))))
        promo.add_widget(desc)
        claimed_ids = set(data.get("claimed_offers", []))
        already_claimed = offer.get("id") in claimed_ids
        claim_btn=GlassButton(text="Забрано" if already_claimed else "Забрать",height=dp(40),size_hint_x=None,width=dp(88)); claim_btn.font_size=dp(10)
        claim_btn.disabled = already_claimed
        claim_btn.bind(on_press=lambda _b,o=dict(offer): self.claim_offer(o))
        promo.add_widget(claim_btn); items.add_widget(promo)
    vip_owned = bool(data.get("vip", False))
    vip_desc = ("VIP активен: радужный анимированный ник и добыча шахты x5" if vip_owned
                else "Радужный анимированный ник и постоянный множитель добычи x5")
    items.add_widget(self._item_card(
        "VIP — радужный ник", vip_desc, 100000,
        lambda _b: self.buy_vip(), accent=(1.0, 0.72, 0.18, 1),
        owned=vip_owned, button_text=("Куплено" if vip_owned else "100 000 монет")
    ))
    for mult, price in self.BOOSTS:
      card = self._item_card(f"Буст добычи x{mult}", "Умножает монеты, которые приносит шахта", price,
                  lambda _b, m=mult, p=price: self.buy_boost(m, p),
                  accent=(0.2, 0.72, 1.0, 1), owned=(current == mult))
      items.add_widget(card)

    # Покупаемая механика: критический сбор, до 15% шанса удвоить добычу шахты.
    crit = max(0, min(15, int(data.get('crit_chance', 0))))
    if crit < 15:
      crit_price = 12000 + (crit // 5) * 8000
      crit_desc = f"Шанс x2 при сборе добычи: {crit}% → {crit + 5}%"
      crit_button = f"{crit_price:,} монет".replace(',', ' ')
      crit_action = lambda _b, p=crit_price, c=crit: self.buy_crit(p, c)
      crit_owned = False
    else:
      crit_desc = "Максимальный шанс двойной награды"
      crit_button = "Максимум"
      crit_action = lambda *_: None
      crit_owned = True
    items.add_widget(self._item_card("Критический сбор +5%", crit_desc, 0,
                 crit_action, owned=crit_owned, button_text=crit_button))
    scroll.add_widget(items)
    root.add_widget(scroll)
    self.status = Label(text="Покупки сохраняются в профиле", size_hint_y=None, height=dp(42),
               color=(.7, 1, .8, 1), halign='center', valign='middle',
               text_size=(Window.width - dp(36), None))
    self.status.bind(width=lambda w, _v: setattr(w, 'text_size', (max(dp(80), w.width - dp(8)), None)))
    root.add_widget(self.status)
    back = GlassButton(text="Назад", height=dp(44))
    back.bind(on_press=lambda *_: self.manager.go_to('main'))
    root.add_widget(back)
    self.add_widget(root)

  def claim_offer(self, offer):
    """Claim a limited local offer once and persist its reward in the player save."""
    data = load_data()
    offer_id = str(offer.get("id", ""))
    claimed = list(data.get("claimed_offers", []))
    if not offer_id or offer_id in claimed:
      self.status.text = "Эта акция уже забрана"
      return
    reward_type = offer.get("reward_type", "coins")
    reward_kind = offer.get("reward_kind", "")
    reward_label = offer.get("title", "Награда")
    if reward_type == "case":
      inv = list(data.get("inventory", []))
      inv.append({"type": "case", "kind": reward_kind or "ice", "case": reward_kind or "ice", "source_offer": offer_id})
      data["inventory"] = inv
      reward_label = "Кейс добавлен в инвентарь"
    elif reward_type == "avatar":
      # Avatar inventory reads owned_avatars, so add the reward there as well.
      avatar_key = reward_kind or "winter_cat"
      owned = list(data.get("owned_avatars", [av[0] for av in AVATARS[:6]]))
      if avatar_key not in owned:
        owned.append(avatar_key)
      data["owned_avatars"] = owned
      inv = list(data.get("inventory", []))
      inv.append({"type": "avatar", "kind": avatar_key, "source_offer": offer_id})
      data["inventory"] = inv
      reward_label = "Зимняя аватарка добавлена в инвентарь аватарок"
    else:
      amount = max(0, int(offer.get("reward_amount", 1000) or 0))
      data["coins"] = int(data.get("coins", 0) or 0) + amount
      reward_label = f"Получено {amount} монет"
    claimed.append(offer_id); data["claimed_offers"] = claimed
    save_data(data)
    _admin_log(f"Акция забрана: {offer_id} игроком {ACTIVE_USER or 'unknown'}")
    self.status.text = reward_label
    self.build_ui()
    # Lightweight reward reveal animation; no heavy assets or repeated animation loops.
    try:
      from kivy.uix.popup import Popup
      panel = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
      icon = Label(text=("КЕЙС" if reward_type == "case" else "АВАТАР" if reward_type == "avatar" else "+"), font_size=dp(24), size_hint_y=None, height=dp(62))
      msg = Label(text=reward_label, font_size=dp(15), halign="center", valign="middle")
      msg.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(10)),max(0,v[1]-dp(6)))))
      ok = GlassButton(text="Отлично", height=dp(42), size_hint_y=None)
      panel.add_widget(icon); panel.add_widget(msg); panel.add_widget(ok)
      pop = Popup(title="Награда получена", content=panel, size_hint=(.78,.34), auto_dismiss=True)
      ok.bind(on_press=pop.dismiss); pop.open(); icon.opacity=0.2
      Animation(opacity=1, duration=.28, t="out_back").start(icon)
    except Exception:
      pass

  def buy_vip(self):
    data = load_data()
    if data.get("vip", False):
      self.status.text = "VIP уже куплен"
      return
    coins = int(data.get("coins", 0) or 0)
    price = 100000
    if coins < price:
      self.status.text = "Не хватает монет: для VIP нужно 100 000"
      return
    data["coins"] = coins - price
    data["vip"] = True
    data["tap_boost"] = max(5, int(data.get("tap_boost", 1) or 1))
    # Сохраняем VIP и баланс; покупка не начисляет второй раз бонус за выдачу из админки.
    save_data(data)
    self.build_ui()
    self.status.text = "VIP куплен! Твой ник теперь радужный"

  def buy_boost(self, mult, price):
    data = load_data(); coins = int(data.get('coins', 0))
    if coins < price:
      self.status.text = "Не хватает монет"
      return
    data['coins'] = coins - price; data['tap_boost'] = mult; save_data(data)
    self.build_ui()
    self.status.text = f"Куплен буст x{mult}"

  def buy_crit(self, price, old_chance):
    data = load_data()
    coins = int(data.get('coins', 0))
    current = max(0, min(15, int(data.get('crit_chance', old_chance))))
    if current >= 15:
      self.status.text = "Критический сбор уже улучшен до максимума"
      return
    if coins < price:
      self.status.text = "Не хватает монет"
      return
    data['coins'] = coins - price
    data['crit_chance'] = min(15, current + 5)
    save_data(data)
    self.build_ui()
    self.status.text = f"Критический сбор улучшен: шанс {data['crit_chance']}%"





class BattleCardsScreen(Screen):
  CARDS = ["Космический импульс", "Изумрудный шторм", "Золотой чемпион", "Ледяной разлом"]
  def __init__(self, **kwargs): super().__init__(**kwargs); self.build_ui()
  def build_ui(self):
    self.clear_widgets(); self.add_widget(make_game_background(None, "waves"))
    root=BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
    root.add_widget(Label(text="БОЕВЫЕ КАРТЫ", font_size=dp(23), bold=True, size_hint_y=None, height=dp(40)))
    data=load_data(); current=data.get('battle_card', self.CARDS[0])
    scroll=ScrollView(); grid=GridLayout(cols=2, spacing=dp(10), size_hint_y=None, padding=dp(4)); grid.bind(minimum_height=grid.setter('height'))
    for name in self.CARDS:
      cell=BoxLayout(orientation='vertical', size_hint_y=None, height=dp(175), spacing=dp(4))
      cell.add_widget(BattleCardArt(name, '', size_hint=(None,None), size=(dp(112),dp(112)), pos_hint={'center_x':.5}))
      cell.add_widget(Label(text=name + (" " if name==current else ""), size_hint_y=None, height=dp(24), font_size=dp(11)))
      b=GlassButton(text="Применить", height=dp(32)); b.bind(on_press=lambda _b,n=name:self.apply_card(n)); cell.add_widget(b); grid.add_widget(cell)
    scroll.add_widget(grid); root.add_widget(scroll)
    back=GlassButton(text="Назад в профиль", height=dp(44)); back.bind(on_press=lambda *_: self.manager.go_to('profile')); root.add_widget(back); self.add_widget(root)
  def apply_card(self,name):
    d=load_data(); d['battle_card']=name; save_data(d); self.build_ui()

class RankSelectScreen(Screen):
  def __init__(self, **kwargs): super().__init__(**kwargs); self.build_ui()
  def build_ui(self):
    self.clear_widgets(); self.add_widget(make_game_background(None, "rank_sticks"))
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
    back=GlassButton(text="Назад в профиль", height=dp(44)); back.bind(on_press=lambda *_:self.manager.go_to('profile')); root.add_widget(back); self.add_widget(root)
  def apply_rank(self,idx):
    d=load_data(); d['profile_rank']=idx; save_data(d); self.build_ui()


class NicknameScreen(Screen):
  NICK_CHANGE_COST = 500

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    data = load_data()
    self.bg_widget = make_game_background(None, "waves")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
    layout.add_widget(Label(text="Смена ника", font_size=dp(24), bold=True,
                size_hint_y=None, height=dp(40)))
    free_change = bool(data.get("nickname_auto"))
    layout.add_widget(Label(text="Введи новый ник (2–16 символов) • " + ("первая смена бесплатно" if free_change else "Цена: 500 монет"),
                font_size=dp(13), size_hint_y=None, height=dp(34), halign='center', valign='middle'))

    # Text field styled to match the game's liquid-glass buttons.
    input_holder = FloatLayout(size_hint_y=None, height=dp(60))
    with input_holder.canvas.before:
      self.input_fill = Color(0.12, 0.15, 0.30, 0.82)
      self.input_rect = RoundedRectangle(pos=input_holder.pos, size=input_holder.size, radius=[dp(24)])
      self.input_edge_color = Color(0.67, 0.65, 1.0, 0.78)
      self.input_edge = Line(rounded_rectangle=(input_holder.x, input_holder.y, input_holder.width, input_holder.height, dp(24)), width=dp(1.2))
    input_holder.bind(pos=self._update_input_shape, size=self._update_input_shape)
    self.text_input = TextInput(
      text=str(data.get("nickname", "Игрок")), multiline=False, font_size=dp(18),
      size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
      background_normal='', background_active='', background_color=(0, 0, 0, 0),
      foreground_color=(1, 1, 1, 1), cursor_color=(0.55, 0.9, 1, 1),
      hint_text='Новый ник', padding=[dp(18), dp(17), dp(18), dp(10)])
    input_holder.add_widget(self.text_input)
    layout.add_widget(input_holder)

    self.result_lbl = Label(text="", font_size=dp(13), size_hint_y=None, height=dp(28),
                 color=(1, 0.6, 0.6, 1))
    layout.add_widget(self.result_lbl)

    save_btn = GlassButton(text="Сменить ник • " + ("бесплатно" if free_change else "500 монет"), height=dp(54))
    save_btn.bind(on_press=self._save)
    layout.add_widget(save_btn)

    if data.get("vip", False):
      current_style = str(data.get("rainbow_nick_style", "classic"))
      if current_style not in RAINBOW_NICK_STYLES:
        current_style = "classic"
      self.rainbow_btn = GlassButton(text="Радуга ника: " + RAINBOW_NICK_STYLES[current_style][0], height=dp(48))
      self.rainbow_btn.font_size = dp(13)
      self.rainbow_btn.bind(on_press=self._cycle_rainbow_nick_style)
      layout.add_widget(self.rainbow_btn)

    back = GlassButton(text="Назад в профиль", height=dp(48))
    back.bind(on_press=lambda *_: self.manager.go_to('profile'))
    layout.add_widget(back)
    self.add_widget(layout)

  def _update_input_shape(self, holder, *args):
    self.input_rect.pos = holder.pos
    self.input_rect.size = holder.size
    self.input_edge.rounded_rectangle = (holder.x, holder.y, holder.width, holder.height, dp(24))

  def _cycle_rainbow_nick_style(self, *args):
    data = load_data()
    styles = list(RAINBOW_NICK_STYLES.keys())
    current = str(data.get("rainbow_nick_style", "classic"))
    if current not in styles:
      current = styles[0]
    data["rainbow_nick_style"] = styles[(styles.index(current) + 1) % len(styles)]
    save_data(data)
    self.rainbow_btn.text = "Радуга ника: " + RAINBOW_NICK_STYLES[data["rainbow_nick_style"]][0]

  def _save(self, *args):
    nick = self.text_input.text.strip()
    if len(nick) < 2:
      self.result_lbl.text = "Слишком короткий ник (мин. 2)"
      return
    if len(nick) > 16:
      self.result_lbl.text = "Слишком длинный ник (макс. 16)"
      return
    data = load_data()
    old_nick = str(data.get("nickname", "Игрок"))
    if nick == old_nick:
      self.result_lbl.text = "Это уже твой текущий ник"
      return
    if "@" in nick:
      self.result_lbl.text = "Ник не должен быть почтой"
      return
    cost = 0 if data.get("nickname_auto") else self.NICK_CHANGE_COST
    coins = int(data.get("coins", 0))
    if coins < cost:
      self.result_lbl.text = "Не хватает монет: нужно 500"
      return
    data["coins"] = coins - cost
    data.pop("nickname_auto", None)
    data["nickname"] = nick
    save_data(data)
    # Refresh profile so the saved nickname and coin balance update immediately.
    if self.manager and self.manager.has_screen('profile'):
      profile = self.manager.get_screen('profile')
      if hasattr(profile, '_build_ui'):
        profile._build_ui()
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
    self.bg_widget = make_game_background(None, "corners")
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
    photo_btn = GlassButton(text="Выбрать фото из галереи", height=dp(48))
    photo_btn.bind(on_press=lambda *_: self._choose_photo())
    layout.add_widget(photo_btn)
    btn_back = GlassButton(text="Назад", height=dp(50))
    btn_back.bind(on_press=lambda x: self.manager.go_to('profile'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def on_pre_enter(self, *args):
    self._build_ui()

  def _choose_photo(self):
    def _finish(path):
      if not path:
        return
      data = load_data()
      data["custom_avatar_photo"] = path
      data["avatar"] = PHOTO_AVATAR_KEY
      save_data(data)
      self._build_ui()
      try:
        self.manager.go_to("profile")
      except Exception:
        pass
    if not _open_android_photo_picker(_finish):
      from kivy.utils import platform as _platform
      if _platform != "android":
        from kivy.uix.filechooser import FileChooserIconView
        from kivy.uix.popup import Popup
        chooser = FileChooserIconView(filters=["*.png", "*.jpg", "*.jpeg", "*.webp"])
        shell = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        shell.add_widget(chooser)
        actions = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        ok = GlassButton(text="Выбрать", height=dp(42))
        cancel = GlassButton(text="Отмена", height=dp(42))
        actions.add_widget(ok); actions.add_widget(cancel); shell.add_widget(actions)
        pop = Popup(title="Выбрать фото для аватара", content=shell, size_hint=(.95,.9))
        def _pick(*_):
          selected = chooser.selection
          if selected:
            try:
              import shutil
              target = os.path.join(DATA_DIR, "profile_avatar_photo.jpg")
              shutil.copyfile(selected[0], target)
              data = load_data(); data["custom_avatar_photo"] = target
              data["avatar"] = PHOTO_AVATAR_KEY; save_data(data)
              pop.dismiss(); self.manager.go_to("profile")
            except Exception as exc:
              print("AVATAR PHOTO ERROR:", exc)
        ok.bind(on_press=_pick); cancel.bind(on_press=lambda *_: pop.dismiss())
        pop.open()
      else:
        _open_glass_popup("Галерея", Label(text="Не удалось открыть системный выбор фото. Проверь crash_log.txt.", color=(1,1,1,1)))

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
    self.bg_widget = make_game_background(None, "waves")
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
    btn_back.bind(on_press=lambda x: self.manager.go_to('profile'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def on_pre_enter(self, *args):
    self._build_ui()

  def _buy(self, fk, price):
    data = load_data()
    try:
      price = int(price)
      coins = int(data.get("coins", 0) or 0)
    except (TypeError, ValueError):
      _open_glass_popup("Ошибка покупки", Label(
        text="Не удалось прочитать баланс монет. Перезапусти игру и попробуй снова.",
        color=(1, 1, 1, 1)))
      return

    owned = data.get("owned_frames", ["none"])
    if not isinstance(owned, list):
      owned = list(owned) if isinstance(owned, (tuple, set)) else ["none"]

    if fk in owned:
      _open_glass_popup("Рамка уже куплена", Label(
        text="Эта рамка уже есть в твоём инвентаре.", color=(1, 1, 1, 1)))
      self._build_ui()
      return

    if coins < price:
      _open_glass_popup("Не хватает монет", Label(
        text=f"Рамка стоит {price} монет.\nУ тебя: {coins} монет.",
        color=(1, 1, 1, 1)))
      return

    data["coins"] = coins - price
    owned.append(fk)
    data["owned_frames"] = owned
    save_data(data)
    self._build_ui()
    _open_glass_popup("Покупка успешна", Label(
      text="Рамка куплена и добавлена в инвентарь рамок.",
      color=(1, 1, 1, 1)))

  def _equip(self, fk):
    data = load_data()
    data["frame"] = fk
    save_data(data)
    self._build_ui()


# ============================================================
# ИНВЕНТАРЬ КЕЙСОВ — пока заглушка, полную систему добавим позже
# ============================================================
class CasesInventoryScreen(Screen):
  """Purchased cases are stored per account and can be opened once each."""
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.add_widget(make_game_background(None, "corners"))
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Инвентарь кейсов", font_size=dp(24), bold=True,
                            size_hint_y=None, height=dp(46)))
    data = load_data()
    cases = [x for x in data.get("inventory", []) if x.get("type") == "case"]
    layout.add_widget(Label(text=f"Кейсов в инвентаре: {len(cases)}",
                            font_size=dp(14), size_hint_y=None, height=dp(28)))
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
    grid = GridLayout(cols=2 if Window.width >= dp(560) else 1, spacing=dp(10),
                      padding=dp(6), size_hint_y=None)
    grid.bind(minimum_height=grid.setter('height'))
    for case in cases:
      case_id = str(case.get("kind", "cats"))
      if case_id not in CASE_INFO: continue
      card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150),
                       padding=dp(10), spacing=dp(6))
      _glass_card(card, color=(0.08,0.11,0.22,0.96), edge=CASE_BTN_COLORS.get(case_id,(0.4,0.6,1,1)))
      card.add_widget(Label(text=CASE_INFO[case_id]["label"], bold=True, font_size=dp(15)))
      card.add_widget(Label(text="Кейс куплен • открытие бесплатно", font_size=dp(11),
                            color=(0.7,0.9,0.75,1)))
      btn = GlassButton(text="Открыть кейс", height=dp(42))
      btn.bind(on_press=lambda _b, cid=case_id: self._open_case(cid))
      card.add_widget(btn)
      grid.add_widget(card)
    if not cases:
      grid.add_widget(Label(text="Пока пусто. Купи кейсы на рынке — они появятся здесь.",
                            size_hint_y=None, height=dp(90), halign='center', valign='middle'))
    scroll.add_widget(grid); layout.add_widget(scroll)
    nav = GridLayout(cols=2, size_hint_y=None, height=dp(48), spacing=dp(8))
    market = GlassButton(text="На рынок", height=dp(48)); market.bind(on_press=lambda *_: self.manager.go_to('market'))
    back = GlassButton(text="Назад", height=dp(48)); back.bind(on_press=lambda *_: self.manager.go_to('main'))
    nav.add_widget(market); nav.add_widget(back); layout.add_widget(nav)
    self.add_widget(layout)

  def _open_case(self, case_id):
    box = self.manager.get_screen('box')
    box.setup_case(case_id)
    box.opening_owned_case = True
    self.manager.current = 'box'

  def on_pre_enter(self, *args):
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
    self.add_widget(make_game_background(None, "corners"))
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Инвентарь аватарок", font_size=dp(22), bold=True,
                            size_hint_y=None, height=dp(42)))
    scroll = ScrollView(size_hint=(1, 1))
    grid = GridLayout(cols=3, spacing=dp(10), padding=dp(8), size_hint_y=None)
    grid.bind(minimum_height=grid.setter('height'))
    data = load_data()
    owned = data.get("owned_avatars", [av[0] for av in AVATARS[:6]])
    current = data.get("avatar", AVATARS[0][0])
    for key, name in list(AVATARS) + list(SECRET_AVATARS):
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
    back.bind(on_press=lambda x: self.manager.go_to('main'))
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
    self.add_widget(make_game_background(None, "waves"))
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
    back.bind(on_press=lambda x: self.manager.go_to('main'))
    layout.add_widget(back); self.add_widget(layout)

  def on_pre_enter(self, *args):
    self._build_ui()

  def _apply(self, key):
    data = load_data(); data["frame"] = key; save_data(data)
    self._build_ui()


# ============================================================
# ТИР
# ============================================================
class DuelPad(Button):
  """Цветная кнопка дуэли памяти: подсвечивается, когда показывает шаг последовательности."""
  def __init__(self, color, **kwargs):
    super().__init__(**kwargs)
    self.base = color
    self.background_normal = ""; self.background_down = ""
    self.background_color = (0, 0, 0, 0)
    with self.canvas.before:
      self._fill = Color(color[0] * .32, color[1] * .32, color[2] * .32, 1)
      self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(22)])
      self._edge_color = Color(color[0], color[1], color[2], .55)
      self._edge = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(22)), width=dp(1.4))
    self.bind(pos=self._sync, size=self._sync)

  def _sync(self, *_):
    self._rect.pos = self.pos; self._rect.size = self.size
    self._edge.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(22))

  def set_lit(self, lit, bad=False):
    c = self.base
    if bad:
      self._fill.rgba = (.92, .12, .12, 1)
    elif lit:
      self._fill.rgba = (min(1, c[0] * 1.1 + .1), min(1, c[1] * 1.1 + .1), min(1, c[2] * 1.1 + .1), 1)
    else:
      self._fill.rgba = (c[0] * .32, c[1] * .32, c[2] * .32, 1)


class SimonBoard(FloatLayout):
  """Поле с четырьмя цветными кнопками: показывает растущую последовательность и принимает ввод.

  Им пользуются и рейтинговая дуэль, и дуэль с другом. Поле само ничего не знает про MMR:
  оно только вызывает функции on_round_start / on_ready / on_round_done / on_fail.
  """
  PAD_COLORS = [(0.95, 0.25, 0.32), (0.25, 0.82, 0.42), (0.30, 0.56, 1.0), (1.0, 0.82, 0.22)]

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.phase = "idle"
    self.sequence = []
    self.input_pos = 0
    self.flash_t = .5
    self.gap_t = .22
    self.rng = random.Random()
    self.on_round_start = None
    self.on_ready = None
    self.on_round_done = None
    self.on_fail = None
    self._events = []
    with self.canvas.before:
      Color(.025, .045, .085, .98)
      self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(18)])
      Color(.18, .72, 1, .95)
      self._border = Line(rounded_rectangle=(0, 0, 100, 100, dp(18)), width=dp(1.5))
    self.bind(pos=self._redraw, size=self._redraw)
    grid = GridLayout(cols=2, spacing=dp(10), padding=dp(12), size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
    self.pads = []
    for i, color in enumerate(self.PAD_COLORS):
      pad = DuelPad(color)
      pad.bind(on_press=lambda _w, k=i: self._on_pad(k))
      self.pads.append(pad)
      grid.add_widget(pad)
    self.add_widget(grid)

  def _redraw(self, *_):
    self._bg.pos = self.pos; self._bg.size = self.size
    self._border.rounded_rectangle = (self.x + dp(1), self.y + dp(1), max(1, self.width - dp(2)), max(1, self.height - dp(2)), dp(18))

  def configure(self, rng=None, flash_t=.5, gap_t=.22):
    self.rng = rng or random.Random()
    self.flash_t = flash_t
    self.gap_t = gap_t

  def _schedule(self, fn, delay):
    self._events.append(Clock.schedule_once(lambda dt: fn(), delay))

  def stop(self, lights_off=False):
    for ev in self._events:
      try: ev.cancel()
      except Exception: pass
    self._events = []
    self.phase = "idle"
    if lights_off:
      for pad in self.pads:
        pad.set_lit(False)

  def reset(self):
    self.stop()
    self.sequence = []
    self.input_pos = 0
    for pad in self.pads:
      pad.set_lit(False)

  def next_round(self, delay=.45):
    self.sequence.append(self.rng.randint(0, 3))
    self.phase = "showing"
    self.input_pos = 0
    if self.on_round_start:
      self.on_round_start(len(self.sequence))
    self._schedule(lambda: self._play_step(0), delay)

  def _play_step(self, i):
    if self.phase != "showing":
      return
    if i >= len(self.sequence):
      self.phase = "input"
      self.input_pos = 0
      if self.on_ready:
        self.on_ready(len(self.sequence))
      return
    k = self.sequence[i]
    self.pads[k].set_lit(True)
    GameAudio.play("pad%d" % k)
    self._schedule(lambda: self._unlight(k, i), self.flash_t)

  def _unlight(self, k, i):
    self.pads[k].set_lit(False)
    self._schedule(lambda: self._play_step(i + 1), self.gap_t)

  def _on_pad(self, k):
    if self.phase != "input":
      return
    expected = self.sequence[self.input_pos]
    pad = self.pads[k]
    if k == expected:
      pad.set_lit(True)
      GameAudio.play("pad%d" % k)
      self._schedule(lambda p=pad: p.set_lit(False), 0.12)
      self.input_pos += 1
      if self.input_pos >= len(self.sequence):
        self.phase = "idle"
        if self.on_round_done:
          self.on_round_done(len(self.sequence))
    else:
      pad.set_lit(True, bad=True)
      self.pads[expected].set_lit(True)
      GameAudio.play("wrong")
      score = len(self.sequence) - 1
      self.phase = "idle"
      if self.on_fail:
        self.on_fail(score)


class MemoryDuelScreen(Screen):
  """Рейтинговая дуэль памяти.

  Соперник (бот твоего ранга) и ты повторяете одну и ту же растущую последовательность
  цветов. Бот сходит с дистанции в раунде, зависящем от его ранга. Чем выше ранг, тем
  быстрее мигают кнопки и тем дольше держится соперник.
    * пройти раунд, в котором ошибся соперник  -> победа (+MMR, бонус за серию побед);
    * ошибиться в том же раунде, что и он       -> ничья (+5 MMR);
    * ошибиться раньше соперника                -> поражение (-MMR, но не ниже порога текущего ранга).
  """
  BOT_NAMES = ["Nova", "Bolt", "Cipher", "Echo", "Pixel", "Rogue", "Vega", "Zero", "Mirage", "Ghost", "Blitz", "Orbit"]
  WIN_BASE = 25
  DRAW_REWARD = 5
  LOSS_BASE = 18

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = make_game_background()
    self.add_widget(self.bg_widget)
    self.phase = "idle"
    self.bot_limit = 0
    self.bot_rank = 0
    self.bot_name = ""

    layout = BoxLayout(orientation="vertical", padding=dp(13), spacing=dp(6))
    layout.add_widget(Label(text="РЕЙТИНГОВАЯ ДУЭЛЬ", font_size=dp(23), bold=True,
                size_hint_y=None, height=dp(34), color=(.55, .88, 1, 1)))
    self.season_lbl = Label(text="", font_size=dp(11), size_hint_y=None, height=dp(18), color=(.75, .85, 1, 1))
    layout.add_widget(self.season_lbl)
    self.rank_lbl = Label(text="", font_size=dp(16), bold=True, size_hint_y=None, height=dp(24),
                color=(1, .86, .35, 1))
    layout.add_widget(self.rank_lbl)
    self.progress_lbl = Label(text="", font_size=dp(12), size_hint_y=None, height=dp(20),
                color=(.85, .9, 1, 1))
    layout.add_widget(self.progress_lbl)
    self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(8))
    layout.add_widget(self.progress_bar)
    self.stats_lbl = Label(text="", font_size=dp(11), size_hint_y=None, height=dp(18),
                color=(.7, .78, .92, 1))
    layout.add_widget(self.stats_lbl)
    self.opp_lbl = Label(text="Соперник: —", font_size=dp(14), bold=True, size_hint_y=None, height=dp(24),
                color=(1, .6, .6, 1))
    layout.add_widget(self.opp_lbl)
    self.info_lbl = Label(text="", font_size=dp(13), size_hint_y=None, height=dp(44),
                color=(1, 1, 1, 1), halign="center", valign="middle")
    self.info_lbl.bind(size=lambda w, v: setattr(w, "text_size", (v[0], None)))
    layout.add_widget(self.info_lbl)

    self.board = SimonBoard(size_hint=(1, 1))
    self.board.on_round_start = self._on_round_start
    self.board.on_ready = self._on_ready
    self.board.on_round_done = self._on_round_done
    self.board.on_fail = self._on_fail
    layout.add_widget(self.board)

    self.result_lbl = Label(text="", font_size=dp(16), bold=True, size_hint_y=None, height=dp(34),
                 color=(.95, .9, .5, 1))
    layout.add_widget(self.result_lbl)
    self.start_btn = GlassButton(text="НАЧАТЬ ДУЭЛЬ", height=dp(48))
    self.start_btn.bind(on_press=self._start_match)
    layout.add_widget(self.start_btn)
    btn_back = GlassButton(text="Назад", height=dp(43))
    btn_back.bind(on_press=lambda x: self.manager.go_to("main"))
    layout.add_widget(btn_back)
    self.add_widget(layout)
    self._update_rank_ui()

  # ---------- интерфейс ----------
  def _update_rank_ui(self):
    data = load_data()
    mmr = max(0, int(data.get("mmr", 0)))
    idx = rank_index_by_mmr(mmr)
    self.season_lbl.text = season_label()
    self.rank_lbl.text = f"{RANKS[idx][1]}  •  {mmr} MMR"
    if idx + 1 < len(RANKS):
      next_threshold = rank_threshold(idx + 1)
      floor = rank_threshold(idx)
      needed = max(1, next_threshold - floor)
      gained = max(0, min(needed, mmr - floor))
      self.progress_bar.max = needed
      self.progress_bar.value = gained
      self.progress_lbl.text = f"До {RANKS[idx + 1][1]}: ещё {max(0, next_threshold - mmr)} MMR  ({gained}/{needed})"
    else:
      self.progress_bar.max = 1; self.progress_bar.value = 1
      self.progress_lbl.text = "Максимальный ранг достигнут!"
    self.stats_lbl.text = (f"Победы: {int(data.get('duel_wins', 0))}  •  Поражения: {int(data.get('ranked_losses', 0))}"
                           f"  •  Ничьи: {int(data.get('ranked_draws', 0))}  •  Серия: {int(data.get('duel_streak', 0))}")

  # ---------- ход матча ----------
  def _start_match(self, *args):
    if self.phase == "playing":
      return
    data = load_data()
    mmr = max(0, int(data.get("mmr", 0)))
    idx = rank_index_by_mmr(mmr)
    # Соперник: ранг игрока ±1; чем выше ранг, тем дольше он держится.
    self.bot_rank = max(0, min(len(RANKS) - 1, idx + random.choice([-1, 0, 0, 1])))
    skill = 3.5 + self.bot_rank * 0.4 + random.uniform(-1.0, 1.0)
    self.bot_limit = int(max(2, min(15, round(skill))))
    self.bot_name = f"{random.choice(self.BOT_NAMES)}#{random.randint(10, 99)}"
    self.board.reset()
    # Скорость показа растёт вместе с рангом игрока.
    self.board.configure(rng=random.Random(),
                         flash_t=max(0.16, 0.50 - idx * 0.012), gap_t=max(0.08, 0.22 - idx * 0.005))
    self.phase = "playing"
    self.start_btn.disabled = True
    self.result_lbl.text = ""
    self.opp_lbl.text = f"Соперник: {self.bot_name} • {RANKS[self.bot_rank][1]}"
    self.info_lbl.text = "Дуэль началась! Запоминай цвета и повторяй.\nВыход из экрана = поражение."
    self.board.next_round(0.9)

  def _on_round_start(self, r):
    if r <= self.bot_limit:
      self.opp_lbl.text = f"Соперник: {self.bot_name} • держится (раунд {r})"
    else:
      self.opp_lbl.text = f"Соперник: {self.bot_name} • ОШИБСЯ в раунде {r}!"
    self.info_lbl.text = f"Раунд {r}: запоминай!" + ("\nПройди его — и победа за тобой!" if r > self.bot_limit else "")

  def _on_ready(self, r):
    self.info_lbl.text = f"Раунд {r}: повтори последовательность!"

  def _on_round_done(self, r):
    if self.phase != "playing":
      return
    if r > self.bot_limit:
      self._finish("win", r)
    else:
      self.info_lbl.text = f"Верно! Раунд {r} пройден."
      self.board.next_round(0.8)

  def _on_fail(self, score):
    if self.phase != "playing":
      return
    self._finish("draw" if score == self.bot_limit else "loss", score)

  def _finish(self, result, score, forfeit=False):
    if self.phase == "result":
      return
    self.phase = "result"
    self.board.stop(lights_off=(result == "win"))
    data = load_data()
    old_mmr = max(0, int(data.get("mmr", 0)))
    old_rank = rank_index_by_mmr(old_mmr)
    diff = self.bot_rank - old_rank
    streak = int(data.get("duel_streak", 0))
    data["ranked_matches"] = int(data.get("ranked_matches", 0)) + 1
    data["season_matches"] = int(data.get("season_matches", 0)) + 1
    if result == "win":
      reward = self.WIN_BASE + min(streak, 4) * 5 + max(0, diff) * 5
      streak += 1
      data["mmr"] = old_mmr + reward
      data["duel_wins"] = int(data.get("duel_wins", 0)) + 1
      data["ranked_wins"] = int(data.get("ranked_wins", 0)) + 1
      text = f"ПОБЕДА!  +{reward} MMR" + (f"  •  серия {streak}" if streak > 1 else "")
      color = (.45, 1, .65, 1)
      GameAudio.play("win")
    elif result == "draw":
      data["mmr"] = old_mmr + self.DRAW_REWARD
      data["ranked_draws"] = int(data.get("ranked_draws", 0)) + 1
      text = f"НИЧЬЯ  +{self.DRAW_REWARD} MMR"
      color = (1, .9, .45, 1)
    else:
      penalty = self.LOSS_BASE + max(0, -diff) * 3
      floor = rank_threshold(old_rank)  # ранг не падает ниже порога текущего ранга
      new_mmr = max(floor, old_mmr - penalty)
      lost = old_mmr - new_mmr
      data["mmr"] = new_mmr
      streak = 0
      data["ranked_losses"] = int(data.get("ranked_losses", 0)) + 1
      text = f"ПОРАЖЕНИЕ  -{lost} MMR" if lost else "ПОРАЖЕНИЕ  0 MMR (ранг защищён)"
      color = (1, .45, .45, 1)
    data["duel_streak"] = streak
    data["duel_best_streak"] = max(int(data.get("duel_best_streak", 0)), streak)
    data["duel_best_round"] = max(int(data.get("duel_best_round", 0)), max(0, score))
    data["best_rank"] = max(int(data.get("best_rank", 0)), rank_index_by_mmr(int(data.get("mmr", 0))))
    save_data(data)
    self.result_lbl.text = text
    self.result_lbl.color = color
    suffix = "\nМатч покинут — засчитано поражение." if forfeit else ""
    self.info_lbl.text = f"Твой результат: {max(0, score)} раунд(ов)  •  соперник: {self.bot_limit}" + suffix
    self._update_rank_ui()
    self.start_btn.text = "ЕЩЁ ОДНА ДУЭЛЬ"
    self.start_btn.disabled = False
    new_rank = rank_index_by_mmr(int(data.get("mmr", 0)))
    if result != "loss" and new_rank > old_rank:
      self._show_rank_up(new_rank)

  def _show_rank_up(self, new_rank):
    overlay = FloatLayout(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
    with overlay.canvas.before:
      Color(.04, .12, .22, .94)
      overlay.bg = RoundedRectangle(pos=overlay.pos, size=overlay.size, radius=[dp(22)])
      Color(.2, .8, 1, .95)
      overlay.glow = Line(rounded_rectangle=(0, 0, 100, 100, dp(22)), width=dp(2))
    def redraw(*_):
      overlay.bg.pos = overlay.pos; overlay.bg.size = overlay.size
      overlay.glow.rounded_rectangle = (overlay.x + dp(4), overlay.y + dp(4),
                                         max(1, overlay.width - dp(8)), max(1, overlay.height - dp(8)), dp(22))
    overlay.bind(pos=redraw, size=redraw)
    box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(16),
                    size_hint=(.94, .72), pos_hint={"center_x": .5, "center_y": .5})
    box.add_widget(Label(text="НОВЫЙ РАНГ", font_size=dp(24), bold=True, color=(1, .82, .25, 1)))
    rank_label = Label(text=RANKS[new_rank][1], font_size=dp(30), bold=True, color=RANKS[new_rank][2])
    box.add_widget(rank_label)
    box.add_widget(Label(text="РЕЙТИНГ ПОВЫШЕН", font_size=dp(15), bold=True, color=(.6, .9, 1, 1)))
    overlay.add_widget(box)
    self.board.add_widget(overlay)
    try:
      rank_label.opacity = 0.15
      Animation(opacity=1, duration=.35, t="out_quad").start(rank_label)
    except Exception:
      pass
    Clock.schedule_once(lambda dt: self._remove_overlay(overlay), 2.5)

  def _remove_overlay(self, overlay):
    try:
      self.board.remove_widget(overlay)
    except Exception:
      pass

  def _reset(self):
    self.board.reset()
    self.phase = "idle"
    self.opp_lbl.text = "Соперник: —"
    self.info_lbl.text = ("Пройди последовательность дальше соперника.\n"
                          "Победа: +MMR • ничья: +5 • поражение: -MMR (ранг не падает).")
    self.result_lbl.text = ""
    self.start_btn.text = "НАЧАТЬ ДУЭЛЬ"
    self.start_btn.disabled = False
    self._update_rank_ui()

  def on_pre_enter(self, *args):
    data = load_data()
    if data and apply_season_rollover(data):
      save_data(data)
    self._reset()

  def on_leave(self, *args):
    # Выход посреди матча засчитывается как поражение, чтобы нельзя было «сливать» рейтинг уходом.
    if self.phase == "playing":
      self._finish("loss", max(0, len(self.board.sequence) - 1), forfeit=True)
    self.board.stop()


# ============================================================
# ДУЭЛЬ С ДРУГОМ (асинхронная: у обоих одна и та же последовательность)
# ============================================================
FRIEND_DUEL_WIN_COINS = 250
FRIEND_DUEL_DRAW_COINS = 100


def _ensure_duel_tables():
  c = _db()
  c.execute("CREATE TABLE IF NOT EXISTS friend_duels (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "challenger TEXT NOT NULL COLLATE NOCASE, opponent TEXT NOT NULL COLLATE NOCASE, "
            "seed INTEGER NOT NULL, challenger_score INTEGER NOT NULL, opponent_score INTEGER, "
            "status TEXT NOT NULL DEFAULT 'open', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
  c.commit(); c.close()


def _open_duel_exists(challenger, opponent):
  _ensure_duel_tables(); c = _db()
  row = c.execute("SELECT id FROM friend_duels WHERE challenger=? AND opponent=? AND status='open'", (challenger, opponent)).fetchone()
  c.close()
  return row is not None


def _create_friend_duel(challenger, opponent, seed, score):
  _ensure_duel_tables()
  if _open_duel_exists(challenger, opponent):
    return None
  c = _db()
  cur = c.execute("INSERT INTO friend_duels(challenger,opponent,seed,challenger_score) VALUES(?,?,?,?)",
                  (challenger, opponent, int(seed), int(score)))
  c.commit(); duel_id = cur.lastrowid; c.close()
  return duel_id


def _open_duels_for(me):
  _ensure_duel_tables(); c = _db()
  rows = c.execute("SELECT id,challenger,seed,challenger_score FROM friend_duels WHERE opponent=? AND status='open' ORDER BY id DESC", (me,)).fetchall()
  c.close()
  return rows


def _finish_friend_duel(duel_id, opponent_score):
  _ensure_duel_tables(); c = _db()
  c.execute("UPDATE friend_duels SET opponent_score=?, status='done' WHERE id=? AND status='open'", (int(opponent_score), int(duel_id)))
  c.commit(); c.close()


def _recent_duels_for(me, limit=5):
  _ensure_duel_tables(); c = _db()
  rows = c.execute("SELECT challenger,opponent,challenger_score,opponent_score FROM friend_duels "
                   "WHERE status='done' AND (challenger=? OR opponent=?) ORDER BY id DESC LIMIT ?", (me, me, limit)).fetchall()
  c.close()
  return rows


def _grant_duel_reward(username, coins, win):
  """Начисляет награду за дуэль аккаунту username (и текущему, и другому локальному игроку)."""
  me = _session_user()
  if me and str(username).lower() == str(me).lower():
    d = load_data()
    d["coins"] = int(d.get("coins", 0) or 0) + coins
    if win:
      d["friend_duel_wins"] = int(d.get("friend_duel_wins", 0) or 0) + 1
    save_data(d)
    return
  c = _db()
  row = c.execute("SELECT data_json FROM players WHERE username=?", (username,)).fetchone()
  if row:
    try: d = json.loads(row[0] or "{}")
    except Exception: d = {}
    d["coins"] = int(d.get("coins", 0) or 0) + coins
    if win:
      d["friend_duel_wins"] = int(d.get("friend_duel_wins", 0) or 0) + 1
    c.execute("UPDATE players SET data_json=? WHERE username=?", (json.dumps(d, ensure_ascii=False), username))
    c.commit()
  c.close()


class FriendDuelScreen(Screen):
  """Дуэль с другом: друг проходит ту же последовательность, побеждает тот, кто продержался дольше."""
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.mode = None
    self.opponent = ""
    self.duel_id = None
    self.seed = 1
    self.target = None
    self.state = "idle"
    self.add_widget(make_game_background())
    layout = BoxLayout(orientation="vertical", padding=dp(13), spacing=dp(6))
    layout.add_widget(Label(text="ДУЭЛЬ С ДРУГОМ", font_size=dp(23), bold=True, size_hint_y=None, height=dp(36), color=(.55, .88, 1, 1)))
    self.who_lbl = Label(text="", font_size=dp(15), bold=True, size_hint_y=None, height=dp(26), color=(1, .86, .35, 1))
    layout.add_widget(self.who_lbl)
    self.info_lbl = Label(text="", font_size=dp(13), size_hint_y=None, height=dp(52), halign="center", valign="middle")
    self.info_lbl.bind(size=lambda w, v: setattr(w, "text_size", (v[0], None)))
    layout.add_widget(self.info_lbl)
    self.board = SimonBoard(size_hint=(1, 1))
    self.board.on_round_start = lambda r: setattr(self.info_lbl, "text", f"Раунд {r}: запоминай!")
    self.board.on_ready = lambda r: setattr(self.info_lbl, "text", f"Раунд {r}: повтори последовательность!")
    self.board.on_round_done = self._on_round_done
    self.board.on_fail = self._on_fail
    layout.add_widget(self.board)
    self.result_lbl = Label(text="", font_size=dp(15), bold=True, size_hint_y=None, height=dp(48), halign="center", valign="middle", color=(.95, .9, .5, 1))
    self.result_lbl.bind(size=lambda w, v: setattr(w, "text_size", (v[0], None)))
    layout.add_widget(self.result_lbl)
    self.start_btn = GlassButton(text="НАЧАТЬ", height=dp(48))
    self.start_btn.bind(on_press=lambda *_: self._start())
    layout.add_widget(self.start_btn)
    back = GlassButton(text="К друзьям", height=dp(43))
    back.bind(on_press=lambda *_: self.manager.go_to("friends"))
    layout.add_widget(back)
    self.add_widget(layout)

  def setup_challenge(self, opponent):
    self.mode = "challenge"; self.opponent = opponent; self.duel_id = None
    self.seed = random.randint(1, 10 ** 9); self.target = None

  def setup_accept(self, duel_id, challenger, seed, target):
    self.mode = "accept"; self.opponent = challenger; self.duel_id = duel_id
    self.seed = int(seed); self.target = int(target)

  def _reset_ui(self):
    self.board.reset()
    self.state = "idle"
    self.result_lbl.text = ""
    self.start_btn.disabled = False
    if self.mode == "accept":
      self.who_lbl.text = f"Вызов от {self.opponent}"
      self.info_lbl.text = (f"{self.opponent} продержался {self.target} раунд(ов).\n"
                            "Пройди дальше — победишь. Выход = поражение.")
      self.start_btn.text = "ПРИНЯТЬ ВЫЗОВ"
    else:
      self.who_lbl.text = f"Вызов для {self.opponent}"
      self.info_lbl.text = ("Пройди как можно больше раундов, пока не ошибёшься.\n"
                            "Друг получит ту же последовательность и попробует тебя обойти.")
      self.start_btn.text = "НАЧАТЬ ВЫЗОВ"

  def _start(self):
    if self.state == "playing" or not self.mode:
      return
    self.board.reset()
    self.board.configure(rng=random.Random(self.seed), flash_t=.40, gap_t=.17)
    self.state = "playing"
    self.start_btn.disabled = True
    self.result_lbl.text = ""
    self.board.next_round(.7)

  def _on_round_done(self, r):
    if self.state != "playing":
      return
    if self.mode == "accept" and r > self.target:
      self._finish(r)
    else:
      self.info_lbl.text = f"Верно! Раунд {r} пройден."
      self.board.next_round(.7)

  def _on_fail(self, score):
    if self.state == "playing":
      self._finish(score)

  def _finish(self, score, abandoned=False):
    if self.state == "result":
      return
    self.state = "result"
    self.board.stop(lights_off=(self.mode == "accept" and self.target is not None and score > self.target))
    score = max(0, int(score))
    me = _session_user()
    self.start_btn.disabled = True
    if self.mode == "challenge":
      if abandoned:
        return
      duel_id = _create_friend_duel(me, self.opponent, self.seed, score)
      if duel_id is None:
        self.result_lbl.text = "Ты уже отправил вызов этому другу — дождись его ответа."
      else:
        self.result_lbl.text = f"Результат: {score} раунд(ов).\nВызов отправлен — друг увидит его в списке друзей."
      self.info_lbl.text = f"Игра окончена: {score} раунд(ов)."
      return
    # режим «принять вызов»
    _finish_friend_duel(self.duel_id, score)
    if score > self.target:
      _grant_duel_reward(me, FRIEND_DUEL_WIN_COINS, True)
      text = f"ПОБЕДА над {self.opponent}!  +{FRIEND_DUEL_WIN_COINS} монет"
      GameAudio.play("win")
    elif score == self.target:
      _grant_duel_reward(me, FRIEND_DUEL_DRAW_COINS, False)
      _grant_duel_reward(self.opponent, FRIEND_DUEL_DRAW_COINS, False)
      text = f"НИЧЬЯ с {self.opponent}  +{FRIEND_DUEL_DRAW_COINS} монет обоим"
    else:
      _grant_duel_reward(self.opponent, FRIEND_DUEL_WIN_COINS, True)
      text = f"Поражение: {self.opponent} оказался сильнее."
    self.result_lbl.text = text
    self.info_lbl.text = f"Твой результат: {score}  •  {self.opponent}: {self.target}"

  def on_pre_enter(self, *args):
    if not self.mode:
      Clock.schedule_once(lambda dt: self.manager.go_to("friends"), 0)
      return
    self._reset_ui()

  def on_leave(self, *args):
    if self.state == "playing":
      if self.mode == "accept":
        self._finish(max(0, len(self.board.sequence) - 1), abandoned=True)
      else:
        self.state = "idle"
    self.board.stop()
    self.mode = None


# ============================================================
# СБРОС ЗАДАНИЙ, СЕЗОНЫ РЕЙТИНГА, ДОСТИЖЕНИЯ
# ============================================================
def quests_rollover(data):
  """Раз в сутки обнуляет прогресс заданий: запоминает счётчики на начало дня и снимает отметки «получено»."""
  today = date.today().isoformat()
  if data.get("quest_day") == today:
    return False
  data["quest_day"] = today
  data["claimed_quests"] = []
  data["quest_base"] = {q["progress_key"]: int(data.get(q["progress_key"], 0) or 0) for q in DAILY_QUESTS}
  return True


def quest_progress(data, quest):
  base = int((data.get("quest_base") or {}).get(quest["progress_key"], 0) or 0)
  return max(0, int(data.get(quest["progress_key"], 0) or 0) - base)


def quests_reset_text():
  now = datetime.now()
  left = datetime(now.year, now.month, now.day) + timedelta(days=1) - now
  secs = int(left.total_seconds())
  return f"Задания обновятся через {secs // 3600} ч {(secs % 3600) // 60:02d} мин"


SEASON_FIRST_MONTH = (2026, 10)   # сезон 1 = октябрь 2026, дальше каждый месяц новый сезон
SEASON_SOFT_RESET = 0.75          # в начале нового сезона остаётся 75% MMR


def season_number(today=None):
  d = today or date.today()
  return max(1, (d.year - SEASON_FIRST_MONTH[0]) * 12 + d.month - SEASON_FIRST_MONTH[1] + 1)


def season_days_left(today=None):
  d = today or date.today()
  nxt = date(d.year + 1, 1, 1) if d.month == 12 else date(d.year, d.month + 1, 1)
  return (nxt - d).days


def season_label():
  return f"Сезон {season_number()} • до конца {season_days_left()} дн."


def season_reward_for_rank(idx):
  """Награда за итоговый ранг сезона: монеты всем, кейс с Платины, рамка с Элиты."""
  coins = 300 + idx * 250
  case = "ice" if idx >= 9 else None
  frame = "legend_frame" if idx >= 16 else ("rainbow_frame" if idx >= 13 else None)
  return coins, case, frame


def apply_season_rollover(data):
  """Если начался новый сезон — выдаёт награду за ранг, сбрасывает MMR на 25% и готовит уведомление."""
  cur = season_number()
  prev = data.get("season")
  if prev is None:
    data["season"] = cur
    return True
  try:
    prev = int(prev)
  except (TypeError, ValueError):
    prev = cur
  if prev >= cur:
    return False
  data["season"] = cur
  if int(data.get("season_matches", 0) or 0) <= 0:
    return True  # в прошлом сезоне не играл в рейтинге — ничего не меняем
  mmr = max(0, int(data.get("mmr", 0) or 0))
  idx = rank_index_by_mmr(mmr)
  coins, case, frame = season_reward_for_rank(idx)
  data["coins"] = int(data.get("coins", 0) or 0) + coins
  parts = [f"{coins} монет"]
  if case:
    inv = list(data.get("inventory", []))
    inv.append({"type": "case", "kind": case, "case": case})
    data["inventory"] = inv
    parts.append(CASE_INFO[case]["label"])
  if frame:
    frames = list(data.get("owned_frames", ["none"]))
    if frame not in frames:
      frames.append(frame)
    data["owned_frames"] = frames
    parts.append("рамка «" + next((f[1] for f in FRAMES if f[0] == frame), frame) + "»")
  new_mmr = int(mmr * SEASON_SOFT_RESET)
  data["mmr"] = new_mmr
  data["duel_streak"] = 0
  data["season_matches"] = 0
  history = list(data.get("season_history", []))
  history.append({"season": prev, "mmr": mmr, "rank": idx})
  data["season_history"] = history[-12:]
  data["season_notice"] = (f"Сезон {prev} завершён!\nТвой итоговый ранг: {RANKS[idx][1]} ({mmr} MMR).\n"
                           f"Награда: {', '.join(parts)}.\n\nНачался сезон {cur}: MMR сброшен до {new_mmr}.")
  return True


def _owned_avatar_count(data):
  return len(data.get("owned_avatars", [a[0] for a in AVATARS[:6]]))


# (id, название, описание, функция прогресса, цель, награда монетами)
ACHIEVEMENTS = [
  ("first_win", "Первая победа", "Выиграй рейтинговую дуэль", lambda d: int(d.get("duel_wins", 0) or 0), 1, 300),
  ("wins_10", "Десять побед", "Выиграй 10 рейтинговых дуэлей", lambda d: int(d.get("duel_wins", 0) or 0), 10, 1500),
  ("wins_50", "Мастер дуэлей", "Выиграй 50 рейтинговых дуэлей", lambda d: int(d.get("duel_wins", 0) or 0), 50, 6000),
  ("streak_5", "Серия из пяти", "Выиграй 5 дуэлей подряд", lambda d: int(d.get("duel_best_streak", 0) or 0), 5, 2000),
  ("round_10", "Память как у слона", "Продержись 10 раундов в дуэли", lambda d: int(d.get("duel_best_round", 0) or 0), 10, 2500),
  ("gold_rank", "Золотой ранг", "Достигни ранга Золото I", lambda d: max(int(d.get("best_rank", 0) or 0), rank_index_by_mmr(int(d.get("mmr", 0) or 0))), 6, 3000),
  ("diamond_rank", "Алмазный ранг", "Достигни ранга Алмаз", lambda d: max(int(d.get("best_rank", 0) or 0), rank_index_by_mmr(int(d.get("mmr", 0) or 0))), 10, 6000),
  ("mine_lvl_10", "Шахтёр", "Улучши шахту до 10 уровня", lambda d: max(int(d.get("mine_best_level", 0) or 0), mine_level(d)), 10, 2000),
  ("mine_lvl_25", "Горный магнат", "Улучши шахту до 25 уровня", lambda d: max(int(d.get("mine_best_level", 0) or 0), mine_level(d)), 25, 8000),
  ("mine_100k", "Золотая лихорадка", "Добудь в шахте 100 000 монет", lambda d: int(d.get("mine_total", 0) or 0), 100000, 5000),
  ("prestige_1", "Перерождение", "Сделай первый престиж шахты", lambda d: int(d.get("mine_prestige", 0) or 0), 1, 10000),
  ("cases_20", "Любитель кейсов", "Открой 20 кейсов", lambda d: int(d.get("cases_opened", 0) or 0), 20, 3000),
  ("friend_win_3", "Друг-соперник", "Выиграй 3 дуэли у друзей", lambda d: int(d.get("friend_duel_wins", 0) or 0), 3, 2000),
  ("avatars_10", "Коллекционер", "Собери 10 аватарок", _owned_avatar_count, 10, 2500),
]


class AchievementsScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.add_widget(make_game_background())
    data = load_data()
    claimed = set(data.get("claimed_achievements", []))
    layout = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Достижения", font_size=dp(24), bold=True, size_hint_y=None, height=dp(40)))
    layout.add_widget(Label(text=f"Наград получено: {len(claimed)} / {len(ACHIEVEMENTS)}", font_size=dp(13),
                            size_hint_y=None, height=dp(22), color=(1, .85, .4, 1)))
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
    inner = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None, padding=dp(6))
    inner.bind(minimum_height=inner.setter("height"))
    for ach_id, name, desc, getter, target, reward in ACHIEVEMENTS:
      try:
        cur = int(getter(data))
      except Exception:
        cur = 0
      done = cur >= target
      card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(142), padding=dp(10), spacing=dp(3))
      _glass_card(card, color=(0.08, 0.11, 0.22, 0.94), edge=(0.4, 0.6, 1, 0.5), radius=dp(15))
      card.add_widget(Label(text=name, font_size=dp(15), bold=True, size_hint_y=None, height=dp(22)))
      card.add_widget(Label(text=desc, font_size=dp(12), size_hint_y=None, height=dp(18), color=(.8, .85, .95, 1)))
      card.add_widget(Label(text=f"{_fmt_num(min(cur, target))} / {_fmt_num(target)}", font_size=dp(12), size_hint_y=None, height=dp(18)))
      card.add_widget(ProgressBar(max=target, value=min(cur, target), size_hint_y=None, height=dp(8)))
      if ach_id in claimed:
        card.add_widget(Label(text="Награда получена", font_size=dp(13), bold=True, color=(.4, .9, .5, 1), size_hint_y=None, height=dp(30)))
      elif done:
        btn = GlassButton(text=f"Забрать +{_fmt_num(reward)} монет", height=dp(34))
        btn.font_size = dp(13)
        btn.bind(on_press=lambda _b, a=ach_id, r=reward: self._claim(a, r))
        card.add_widget(btn)
      else:
        card.add_widget(Label(text=f"Награда: {_fmt_num(reward)} монет", font_size=dp(12), color=(1, .85, .4, 1), size_hint_y=None, height=dp(30)))
      inner.add_widget(card)
    scroll.add_widget(inner)
    layout.add_widget(scroll)
    back = GlassButton(text="Назад", height=dp(48))
    back.bind(on_press=lambda *_: self.manager.go_to("main"))
    layout.add_widget(back)
    self.add_widget(layout)

  def _claim(self, ach_id, reward):
    data = load_data()
    claimed = list(data.get("claimed_achievements", []))
    if ach_id in claimed:
      return
    entry = next((a for a in ACHIEVEMENTS if a[0] == ach_id), None)
    if entry is None:
      return
    try:
      if int(entry[3](data)) < entry[4]:
        return
    except Exception:
      return
    claimed.append(ach_id)
    data["claimed_achievements"] = claimed
    data["coins"] = int(data.get("coins", 0) or 0) + reward
    save_data(data)
    GameAudio.play("coin")
    self._build_ui()

  def on_pre_enter(self, *args):
    self._build_ui()



# ============================================================
# КАЗИНО (скруглённые кнопки)
# ============================================================
class CasinoScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = make_game_background(None, "waves")
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
    btn_back.bind(on_press=lambda x: self.manager.go_to('fun'))
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
    self.bg_widget = make_game_background(None, "spiral")
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
    btn_back.bind(on_press=lambda x: self.manager.go_to('fun'))
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


class EmojiAvatarArt(Widget):
  """Vector-drawn avatar art. No emoji glyphs or platform-dependent fonts."""
  PALETTES = {
    "moon": ((0.10,0.13,0.32,1),(0.72,0.80,1,1),(0.98,0.88,0.48,1)),
    "comet": ((0.05,0.22,0.35,1),(0.35,0.88,1,1),(0.85,0.98,1,1)),
    "crystal": ((0.10,0.20,0.34,1),(0.30,0.88,1,1),(0.88,0.98,1,1)),
    "phoenix": ((0.30,0.06,0.10,1),(1,0.27,0.08,1),(1,0.78,0.22,1)),
    "ninja": ((0.08,0.08,0.18,1),(0.48,0.30,0.92,1),(0.92,0.95,1,1)),
    "samurai": ((0.22,0.04,0.08,1),(0.88,0.16,0.20,1),(1,0.75,0.45,1)),
    "cyber_cat": ((0.03,0.17,0.25,1),(0.15,0.92,0.95,1),(0.95,0.35,0.95,1)),
    "shark": ((0.04,0.16,0.29,1),(0.30,0.66,0.88,1),(0.90,0.97,1,1)),
    "octopus": ((0.20,0.06,0.30,1),(0.76,0.35,0.92,1),(1,0.72,0.94,1)),
    "raccoon": ((0.13,0.17,0.25,1),(0.58,0.68,0.80,1),(0.97,0.98,1,1)),
    "owl": ((0.20,0.11,0.04,1),(0.85,0.56,0.18,1),(1,0.90,0.57,1)),
    "ghost": ((0.13,0.20,0.38,1),(0.68,0.82,1,1),(1,1,1,1)),
    "dragon": ((0.04,0.20,0.15,1),(0.18,0.78,0.43,1),(1,0.58,0.17,1)),
    "unicorn": ((0.25,0.08,0.27,1),(0.97,0.55,0.83,1),(0.62,0.84,1,1)),
    "robot": ((0.09,0.17,0.27,1),(0.50,0.70,0.83,1),(0.26,1,0.86,1)),
    "alien": ((0.04,0.20,0.12,1),(0.28,0.85,0.45,1),(0.80,1,0.66,1)),
    "slime": ((0.07,0.22,0.10,1),(0.35,0.88,0.32,1),(0.80,1,0.60,1)),
    "fox": ((0.26,0.08,0.03,1),(1,0.43,0.10,1),(1,0.83,0.57,1)),
    "wolf": ((0.12,0.17,0.26,1),(0.55,0.66,0.80,1),(0.93,0.97,1,1)),
    "tiger": ((0.28,0.10,0.02,1),(1,0.52,0.08,1),(1,0.90,0.68,1)),
    "panda": ((0.13,0.18,0.25,1),(0.93,0.96,1,1),(0.12,0.15,0.22,1)),
    "rose": ((0.24,0.04,0.13,1),(0.96,0.20,0.48,1),(0.40,0.92,0.50,1)),
    "sunflower": ((0.25,0.17,0.03,1),(1,0.76,0.12,1),(0.40,0.82,0.25,1)),
    "lotus": ((0.16,0.07,0.28,1),(0.97,0.52,0.83,1),(0.45,0.90,0.82,1)),
    "gold_mineral": ((0.22,0.13,0.02,1),(1,0.72,0.12,1),(1,0.96,0.55,1)),
    "meteorite": ((0.10,0.08,0.26,1),(0.48,0.36,0.88,1),(0.95,0.58,0.25,1)),
    "glow": ((0.10,0.20,0.14,1),(0.76,0.94,0.30,1),(1,1,0.70,1)),
  }
  def __init__(self, key, size, **kwargs):
    super().__init__(**kwargs)
    self.key = str(key)
    self.size_hint = (None, None)
    self.size = (size, size)
    self.bind(pos=self._redraw, size=self._redraw)
    self._redraw()

  def _redraw(self, *_):
    from kivy.graphics import Color, Ellipse, Line, Triangle, RoundedRectangle
    self.canvas.clear()
    x, y = self.pos
    w, h = self.size
    s = min(w, h)
    cx, cy = x + w/2, y + h/2
    bg, main, accent = self.PALETTES.get(self.key, ((0.10,0.14,0.25,1),(0.45,0.70,0.95,1),(0.95,0.95,1,1)))
    def ellipse(px, py, ew, eh, color):
      Color(*color); Ellipse(pos=(px,py), size=(ew,eh))
    def poly(points, color):
      Color(*color); Line(points=points, close=True, width=max(1, s*0.018))
    with self.canvas:
      # Deep colored medallion with a crisp double rim.
      ellipse(x, y, w, h, bg)
      Color(main[0], main[1], main[2], 0.22); Ellipse(pos=(x+s*.07,y+s*.07),size=(s*.86,s*.86))
      Color(*accent); Line(circle=(cx,cy,s*.455),width=max(1,s*.025))
      Color(main[0],main[1],main[2],0.7); Line(circle=(cx,cy,s*.405),width=max(1,s*.012))
      k=self.key
      if k in ("moon","comet","crystal","meteorite","gold_mineral"):
        if k == "moon":
          ellipse(cx-s*.22,cy-s*.22,s*.44,s*.44,accent)
          ellipse(cx-s*.08,cy-s*.14,s*.40,s*.40,bg)
          ellipse(cx+s*.18,cy+s*.19,s*.045,s*.045,main)
          ellipse(cx-s*.24,cy+s*.17,s*.035,s*.035,accent)
        elif k == "comet":
          Color(main[0],main[1],main[2],.65); Line(points=[cx-s*.30,cy-s*.19,cx+s*.02,cy+s*.02,cx+s*.32,cy+s*.31],width=s*.09)
          ellipse(cx-s*.13,cy-s*.10,s*.28,s*.28,accent); ellipse(cx-s*.07,cy-s*.04,s*.16,s*.16,(1,1,1,1))
        elif k == "crystal":
          poly([(cx,cy+s*.31),(cx+s*.23,cy+s*.06),(cx+s*.12,cy-s*.25),(cx-s*.12,cy-s*.25),(cx-s*.23,cy+s*.06)],main)
          poly([(cx,cy+s*.31),(cx,cy-s*.25),(cx+s*.23,cy+s*.06)],accent)
          poly([(cx,cy+s*.31),(cx-s*.12,cy-s*.25),(cx-s*.23,cy+s*.06)],(0.85,0.98,1,1))
        else:
          ellipse(cx-s*.20,cy-s*.18,s*.40,s*.36,main)
          poly([(cx-s*.22,cy+s*.05),(cx-s*.08,cy+s*.26),(cx+s*.04,cy+s*.15),(cx+s*.19,cy+s*.24),(cx+s*.25,cy-s*.05)],accent)
          for dx,dy in [(-.23,.22),(.24,.18),(.28,-.20)]: ellipse(cx+s*dx,cy+s*dy,s*.045,s*.045,(1,1,1,1))
      elif k in ("rose","sunflower","lotus","glow"):
        petal_count = 8 if k == "sunflower" else 6
        for i in range(petal_count):
          a=2*math.pi*i/petal_count
          px=cx+math.cos(a)*s*.16-s*.075; py=cy+math.sin(a)*s*.16-s*.075
          ellipse(px,py,s*.15,s*.15,main if i%2==0 else accent)
        ellipse(cx-s*.105,cy-s*.105,s*.21,s*.21,accent if k!="sunflower" else (0.30,0.16,0.04,1))
        if k in ("rose","lotus"):
          Color(0.25,0.85,0.45,1); Line(points=[cx,cy-s*.10,cx,cy-s*.30],width=s*.035)
          ellipse(cx-s*.17,cy-s*.28,s*.16,s*.08,(0.25,0.85,0.45,1))
      elif k in ("phoenix","dragon","unicorn"):
        # Fantasy crest: layered horns/wings and a bright central face.
        poly([(cx-s*.27,cy-s*.10),(cx-s*.31,cy+s*.27),(cx-s*.04,cy+s*.16),(cx,cy+s*.29),(cx+s*.08,cy+s*.12),(cx+s*.30,cy+s*.25),(cx+s*.24,cy-s*.12)],main)
        ellipse(cx-s*.19,cy-s*.20,s*.38,s*.35,accent)
        ellipse(cx-s*.12,cy-s*.04,s*.045,s*.06,bg); ellipse(cx+s*.07,cy-s*.04,s*.045,s*.06,bg)
        if k=="unicorn": poly([(cx-s*.06,cy+s*.16),(cx,cy+s*.42),(cx+s*.06,cy+s*.16)],(1,0.86,0.35,1))
        elif k=="dragon": poly([(cx-s*.22,cy+s*.15),(cx-s*.36,cy+s*.34),(cx-s*.08,cy+s*.25)],accent)
      elif k in ("robot","alien","ninja","samurai"):
        if k=="robot":
          Color(*main); RoundedRectangle(pos=(cx-s*.25,cy-s*.22),size=(s*.50,s*.45),radius=[s*.07])
          Color(*accent); Line(points=[cx-s*.12,cy+s*.24,cx-s*.12,cy+s*.32,cx+s*.12,cy+s*.32,cx+s*.12,cy+s*.24],width=s*.025)
          ellipse(cx-s*.14,cy-s*.02,s*.08,s*.08,accent); ellipse(cx+s*.06,cy-s*.02,s*.08,s*.08,accent)
          Color(*bg); Line(points=[cx-s*.10,cy-s*.13,cx+s*.10,cy-s*.13],width=s*.025)
        elif k=="alien":
          ellipse(cx-s*.23,cy-s*.22,s*.46,s*.58,main)
          ellipse(cx-s*.16,cy-s*.02,s*.11,s*.17,bg); ellipse(cx+s*.05,cy-s*.02,s*.11,s*.17,bg)
          Color(*accent); Line(points=[cx-s*.10,cy-s*.17,cx,cy-s*.20,cx+s*.10,cy-s*.17],width=s*.025)
        else:
          poly([(cx-s*.30,cy+s*.07),(cx-s*.24,cy+s*.28),(cx+s*.24,cy+s*.28),(cx+s*.30,cy+s*.07)],main)
          Color(*accent); RoundedRectangle(pos=(cx-s*.25,cy-s*.13),size=(s*.50,s*.20),radius=[s*.04])
          Color(*bg); Line(points=[cx-s*.15,cy-s*.03,cx-s*.04,cy-s*.03],width=s*.035); Line(points=[cx+s*.04,cy-s*.03,cx+s*.15,cy-s*.03],width=s*.035)
          if k=="samurai": poly([(cx-s*.08,cy+s*.25),(cx,cy+s*.42),(cx+s*.08,cy+s*.25)],accent)
      elif k in ("shark","octopus","raccoon","owl","cyber_cat","fox","wolf","tiger","panda"):
        # Original cartoon animal faces, drawn from simple vector shapes.
        if k in ("fox","wolf","cyber_cat","tiger"):
          poly([(cx-s*.29,cy+s*.05),(cx-s*.27,cy+s*.34),(cx-s*.06,cy+s*.22),(cx+s*.06,cy+s*.22),(cx+s*.27,cy+s*.34),(cx+s*.29,cy+s*.05),(cx+s*.20,cy-s*.20),(cx,cy-s*.28),(cx-s*.20,cy-s*.20)],main)
          ellipse(cx-s*.18,cy-s*.06,s*.10,s*.10,accent); ellipse(cx+s*.08,cy-s*.06,s*.10,s*.10,accent)
          poly([(cx-s*.08,cy-s*.18),(cx,cy-s*.25),(cx+s*.08,cy-s*.18)],accent)
          if k in ("cyber_cat","tiger"):
            Color(*bg); Line(points=[cx-s*.22,cy+s*.07,cx-s*.12,cy+s*.01],width=s*.035); Line(points=[cx+s*.12,cy+s*.01,cx+s*.22,cy+s*.07],width=s*.035)
        elif k=="panda":
          ellipse(cx-s*.27,cy+s*.08,s*.20,s*.20,main); ellipse(cx+s*.07,cy+s*.08,s*.20,s*.20,main)
          ellipse(cx-s*.25,cy-s*.22,s*.50,s*.50,accent)
          ellipse(cx-s*.17,cy-s*.03,s*.14,s*.17,main); ellipse(cx+s*.03,cy-s*.03,s*.14,s*.17,main)
          ellipse(cx-s*.06,cy-s*.15,s*.12,s*.08,main)
        elif k=="owl":
          ellipse(cx-s*.26,cy-s*.18,s*.28,s*.40,main); ellipse(cx-s*.02,cy-s*.18,s*.28,s*.40,main)
          ellipse(cx-s*.20,cy-s*.01,s*.18,s*.18,accent); ellipse(cx+s*.02,cy-s*.01,s*.18,s*.18,accent)
          ellipse(cx-s*.14,cy+s*.04,s*.06,s*.06,bg); ellipse(cx+s*.08,cy+s*.04,s*.06,s*.06,bg)
          poly([(cx-s*.05,cy-s*.08),(cx,cy-s*.16),(cx+s*.05,cy-s*.08)],(1,0.55,0.10,1))
        elif k=="raccoon":
          ellipse(cx-s*.24,cy-s*.20,s*.48,s*.48,accent)
          Color(*main); Line(points=[cx-s*.24,cy+s*.01,cx-s*.05,cy-s*.06,cx+s*.05,cy-s*.06,cx+s*.24,cy+s*.01],width=s*.09)
          ellipse(cx-s*.15,cy-s*.01,s*.07,s*.08,bg); ellipse(cx+s*.08,cy-s*.01,s*.07,s*.08,bg)
        elif k=="shark":
          poly([(cx-s*.28,cy+s*.03),(cx-s*.18,cy+s*.20),(cx-s*.03,cy+s*.13),(cx+s*.11,cy+s*.18),(cx+s*.27,cy+s*.04),(cx+s*.18,cy-s*.20),(cx-s*.15,cy-s*.20)],main)
          poly([(cx-s*.16,cy-s*.15),(cx+s*.18,cy-s*.15),(cx+s*.09,cy-s*.25),(cx-s*.06,cy-s*.25)],accent)
          ellipse(cx+s*.10,cy+s*.02,s*.05,s*.05,(0.03,0.08,0.14,1))
        else:
          # Octopus: round head plus seven tentacles.
          ellipse(cx-s*.22,cy-s*.06,s*.44,s*.40,main)
          for i in range(7):
            xx=cx-s*.24+i*s*.08
            Color(*main); Line(points=[xx,cy-s*.12,xx-s*.025,cy-s*.23,xx+s*.02,cy-s*.30],width=s*.045)
          ellipse(cx-s*.12,cy+s*.03,s*.06,s*.07,accent); ellipse(cx+s*.06,cy+s*.03,s*.06,s*.07,accent)
      else:
        # Safe, polished abstract emblem for any future avatar key.
        poly([(cx,cy+s*.30),(cx+s*.25,cy),(cx,cy-s*.30),(cx-s*.25,cy)],main)
        ellipse(cx-s*.08,cy-s*.08,s*.16,s*.16,accent)

# ============================================================
# ЕЖЕДНЕВНЫЕ ЗАДАНИЯ (новый способ MMR и монет)
# ============================================================
class QuestsScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.bg_widget = make_game_background(None, "corners")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
    layout.add_widget(Label(text="Ежедневные задания", font_size=dp(22), bold=True,
                size_hint_y=None, height=dp(36)))
    data = load_data()
    if data and quests_rollover(data):
      save_data(data)
    self.coins_lbl = Label(text=f"Монеты: {data.get('coins', 0)}",
                font_size=dp(14), size_hint_y=None, height=dp(24))
    layout.add_widget(self.coins_lbl)
    layout.add_widget(Label(text=quests_reset_text(), font_size=dp(12), size_hint_y=None, height=dp(20),
                            color=(.75, .85, 1, 1)))
    scroll = ScrollView(size_hint=(1, 1))
    inner = BoxLayout(orientation='vertical', spacing=dp(10),
              size_hint_y=None, padding=dp(6))
    inner.bind(minimum_height=inner.setter('height'))
    claimed = data.get("claimed_quests", [])

    for q in DAILY_QUESTS:
      current = quest_progress(data, q)
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
    btn_back.bind(on_press=lambda x: self.manager.go_to('main'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def _claim(self, q):
    data = load_data()
    if quests_rollover(data):
      save_data(data)
      self._build_ui()
      return
    claimed = data.get("claimed_quests", [])
    if q["id"] in claimed: return
    current = quest_progress(data, q)
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
  """Local coin market: cases enter case inventory; rare items enter item inventory."""
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self.add_widget(make_game_background(None, "waves"))
    layout = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(7))
    layout.add_widget(Label(text="Рынок кейсов и редких предметов", font_size=dp(22), bold=True,
                            size_hint_y=None, height=dp(42)))
    data = load_data()
    self.coins_lbl = Label(text=f"Монеты: {int(data.get('coins', 0)):,}".replace(',', ' '),
                           font_size=dp(14), size_hint_y=None, height=dp(25))
    layout.add_widget(self.coins_lbl)
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=dp(4))
    inner = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, padding=dp(4))
    inner.bind(minimum_height=inner.setter('height'))
    inner.add_widget(Label(text="КЕЙСЫ — после покупки отправляются в инвентарь кейсов",
                           font_size=dp(14), bold=True, size_hint_y=None, height=dp(30)))
    case_offers = [
      ("cats", "Кейс с котами", 5000),
      ("planets", "Космический кейс", 25000),
      ("ice", "Ледяной кейс", 100000),
      ("fire", "Огненный кейс", 250000),
      ("cosmic", "Легендарный космический кейс", 1000000),
      ("magic", "Мифический магический кейс", 2500000),
    ]
    for case_id, title, price in case_offers:
      card = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(76), padding=dp(8), spacing=dp(8))
      _glass_card(card, color=(0.08,0.11,0.22,0.96), edge=CASE_BTN_COLORS.get(case_id,(0.4,0.6,1,1)), radius=dp(14))
      icon = ChestArt(case_id, dp(54)); icon.size_hint=(None,None); icon.size=(dp(54),dp(54)); card.add_widget(icon)
      info = BoxLayout(orientation='vertical', spacing=dp(2))
      info.add_widget(Label(text=title, font_size=dp(12), bold=True, halign='left', valign='middle'))
      info.add_widget(Label(text=f"{price:,} монет".replace(',', ' '), font_size=dp(12), color=(1,.82,.35,1), halign='left'))
      card.add_widget(info)
      buy = GlassButton(text="Купить", height=dp(40), size_hint_x=None, width=dp(82))
      buy.bind(on_press=lambda _b, cid=case_id, cost=price: self._buy_case(cid,cost))
      card.add_widget(buy); inner.add_widget(card)

    inner.add_widget(Label(text="РЕДКИЕ ПРЕДМЕТЫ — коллекционные лоты", font_size=dp(14), bold=True,
                           size_hint_y=None, height=dp(32)))
    rare_items = [
      ("knives", "karambit_black_pearl", "Керамбит Чёрная жемчужина", 1000000),
      ("knives", "karambit_talisman", "Керамбит Талисман", 1500000),
      ("guns", "dragon_lore", "Deagle Дракон", 2000000),
      ("rainbow", "rainbow_neon", "Радужный кот Неон", 3000000),
      ("cosmic", "multiverse", "Мультивселенная", 5000000),
      ("magic", "philosopher_stone", "Философский камень", 10000000),
    ]
    for item_type, kind, title, price in rare_items:
      card = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(78), padding=dp(8), spacing=dp(8))
      _glass_card(card, color=(0.10,0.08,0.18,0.97), edge=(0.76,0.48,1,0.9), radius=dp(14))
      art_holder = FloatLayout(size_hint_x=None, width=dp(60))
      art = make_art(item_type, kind, dp(54))
      if art is not None:
        art.size_hint=(None,None); art.size=(dp(54),dp(54)); art.pos_hint={'center_x':.5,'center_y':.5}; art_holder.add_widget(art)
      card.add_widget(art_holder)
      info = BoxLayout(orientation='vertical', spacing=dp(2))
      info.add_widget(Label(text=title, font_size=dp(12), bold=True, halign='left', valign='middle'))
      info.add_widget(Label(text=f"{price:,} монет".replace(',', ' '), font_size=dp(12), color=(1,.82,.35,1), halign='left'))
      card.add_widget(info)
      buy = GlassButton(text="Купить", height=dp(40), size_hint_x=None, width=dp(82))
      buy.bind(on_press=lambda _b, t=item_type, k=kind, cost=price: self._buy_item(t,k,cost))
      card.add_widget(buy); inner.add_widget(card)

    scroll.add_widget(inner); layout.add_widget(scroll)
    nav = GridLayout(cols=3, size_hint_y=None, height=dp(46), spacing=dp(7))
    for label, target in [("Кейсы", "cases"), ("Инвентарь кейсов", "cases_inventory"), ("Назад", "main")]:
      btn=GlassButton(text=label,height=dp(46)); btn.font_size=dp(11)
      btn.bind(on_press=lambda _b,t=target:self.manager.go_to(t)); nav.add_widget(btn)
    layout.add_widget(nav); self.add_widget(layout)

  def _buy_case(self, case_id, price):
    data=load_data(); coins=int(data.get('coins',0) or 0)
    if coins < price:
      self.coins_lbl.text=f"Не хватает монет: нужно {price:,}, у тебя {coins:,}".replace(',', ' ')
      return
    data['coins']=coins-price
    inv=list(data.get('inventory',[])); inv.append({'type':'case','kind':case_id,'case':case_id,'market_price':price})
    data['inventory']=inv; save_data(data); self._build_ui()

  def _buy_item(self, item_type, kind, price):
    data=load_data(); coins=int(data.get('coins',0) or 0)
    if coins < price:
      self.coins_lbl.text=f"Не хватает монет: нужно {price:,}, у тебя {coins:,}".replace(',', ' ')
      return
    data['coins']=coins-price
    inv=list(data.get('inventory',[])); inv.append({'type':item_type,'kind':kind,'case':'market','market_price':price})
    data['inventory']=inv; save_data(data); self._build_ui()

  def on_pre_enter(self, *args):
    self._build_ui()


# ============================================================
# РАЗВЛЕЧЕНИЯ
# ============================================================
class FunScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.bg_widget = make_game_background(None, "corners")
    self.add_widget(self.bg_widget)
    layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
    layout.add_widget(Label(text="Развлечения", font_size=dp(26), bold=True,
                size_hint_y=None, height=dp(40)))
    self.coins_lbl = Label(text="", font_size=dp(14), size_hint_y=None, height=dp(26))
    layout.add_widget(self.coins_lbl)
    layout.add_widget(Label(text="", size_hint_y=None, height=dp(10)))
    for text, target, sub in [
      ("Рейтинговая дуэль", "ranked", "Победи соперника в дуэли памяти → MMR"),
      ("Казино", "casino", "Красно-чёрное и зелёное x14"),
      ("Охота за сокровищами", "treasure", "500 монет → ищи клад в сундуках"),
      ("Задания", "quests", "Ежедневные квесты — монеты + MMR"),
      ("Рынок скинов", "market", "Покупай редкие скины за монеты"),
    ]:
      btn = GlassButton(text=text, height=dp(56))
      btn.bind(on_press=lambda x, t=target: self.manager.go_to(t))
      layout.add_widget(btn)
      layout.add_widget(Label(text=sub, font_size=dp(11),
                   size_hint_y=None, height=dp(18),
                   color=(0.85, 0.85, 0.9, 1)))
    layout.add_widget(Label(text="", size_hint_y=None, height=dp(10)))
    btn_back = GlassButton(text="Назад", height=dp(50))
    btn_back.bind(on_press=lambda x: self.manager.go_to('main'))
    layout.add_widget(btn_back)
    self.add_widget(layout)

  def on_pre_enter(self, *args):
    data = load_data()
    self.coins_lbl.text = f"Монеты: {data.get('coins', 0)}"


# ============================================================
# ВХОД И РЕГИСТРАЦИЯ
# ============================================================
class GlassTextInput(TextInput):
  """Скруглённое поле ввода в стиле Liquid Glass."""
  def __init__(self, **kwargs):
    kwargs.setdefault("background_normal", "")
    kwargs.setdefault("background_active", "")
    kwargs.setdefault("background_color", (0, 0, 0, 0))
    kwargs.setdefault("foreground_color", (1, 1, 1, 1))
    kwargs.setdefault("hint_text_color", (0.78, 0.82, 0.9, 0.85))
    kwargs.setdefault("cursor_color", (0.55, 0.85, 1, 1))
    kwargs.setdefault("padding", [dp(14), dp(13), dp(14), dp(10)])
    super().__init__(**kwargs)
    with self.canvas.before:
      self._glass_color = Color(0.12, 0.16, 0.23, 0.55)
      self._glass_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
      self._edge_color = Color(0.65, 0.82, 1, 0.62)
      self._glass_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(15)), width=1.05)
    self.bind(pos=self._sync_glass, size=self._sync_glass)
  def _sync_glass(self, *_):
    self._glass_rect.pos = self.pos
    self._glass_rect.size = self.size
    self._glass_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(15))

class AuthScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.mode = "login"
    self._build_ui()
  def _build_ui(self):
    self.clear_widgets()
    self.add_widget(make_game_background("cosmic", "particles_up"))
    root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(10))
    root.add_widget(Label(text="CataBox", font_size=dp(28), bold=True, size_hint_y=None, height=dp(60)))
    self.mode_label = Label(text="Вход в аккаунт", font_size=dp(18), size_hint_y=None, height=dp(30))
    root.add_widget(self.mode_label)
    self.username = GlassTextInput(hint_text="Email", multiline=False, size_hint_y=None, height=dp(48))
    self.password = GlassTextInput(hint_text="Пароль (минимум 6 символов)", password=True, multiline=False, size_hint_y=None, height=dp(48))
    root.add_widget(self.username)
    self.nick_input = GlassTextInput(hint_text="Ник в игре (3–16 символов)", multiline=False, size_hint_y=None, height=0, opacity=0, disabled=True)
    root.add_widget(self.nick_input)
    pass_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(48))
    pass_row.add_widget(self.password)
    self.show_btn = GlassButton(text="Показать", height=dp(48), size_hint_x=None, width=dp(94))
    self.show_btn.bind(on_press=lambda *_: self._toggle_password(self.password, self.show_btn))
    pass_row.add_widget(self.show_btn)
    root.add_widget(pass_row)
    self.repeat_password = GlassTextInput(hint_text="Повторите пароль", password=True, multiline=False, size_hint_y=None, height=dp(48), opacity=0, disabled=True)
    self.repeat_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=0, opacity=0)
    self.repeat_row.add_widget(self.repeat_password)
    self.repeat_show_btn = GlassButton(text="Показать", height=dp(48), size_hint_x=None, width=dp(94))
    self.repeat_show_btn.bind(on_press=lambda *_: self._toggle_password(self.repeat_password, self.repeat_show_btn))
    self.repeat_row.add_widget(self.repeat_show_btn)
    root.add_widget(self.repeat_row)
    self.status = Label(text="Вход и регистрация через Supabase", font_size=dp(11), size_hint_y=None, height=dp(48), halign="center", valign="middle")
    self.status.bind(size=lambda w, v: setattr(w, "text_size", v))
    root.add_widget(self.status)
    self.action_btn = GlassButton(text="Войти", height=dp(48))
    self.action_btn.bind(on_press=lambda *_: self._submit())
    root.add_widget(self.action_btn)
    self.switch_btn = GlassButton(text="Создать аккаунт", height=dp(48))
    self.switch_btn.bind(on_press=lambda *_: self._switch_mode())
    root.add_widget(self.switch_btn)
    self.add_widget(root)
  def _toggle_password(self, field, button):
    # Переключаем только маскировку пароля; ник всегда остаётся обычным текстом.
    field.password = not field.password
    button.text = "Показать" if field.password else "Скрыть"
    field.cursor = (len(field.text), 0)
    field.focus = True
  def _clear_fields(self):
    self.username.text = ""
    self.nick_input.text = ""
    self.password.text = ""
    self.repeat_password.text = ""
    # Не включаем password=True для username: иначе ник маскируется точками.
    self.password.password = True
    self.repeat_password.password = True
    self.show_btn.text = "Показать"
    self.repeat_show_btn.text = "Показать"
  def _switch_mode(self):
    self._clear_fields()
    self.mode = "register" if self.mode == "login" else "login"
    self.mode_label.text = "Регистрация аккаунта" if self.mode == "register" else "Вход в аккаунт"
    self.action_btn.text = "Зарегистрироваться" if self.mode == "register" else "Войти"
    self.switch_btn.text = "Уже есть аккаунт? Войти" if self.mode == "register" else "Создать аккаунт"
    self.nick_input.height = dp(48) if self.mode == "register" else 0
    self.nick_input.opacity = 1 if self.mode == "register" else 0
    self.nick_input.disabled = self.mode != "register"
    self.repeat_row.height = dp(48) if self.mode == "register" else 0
    self.repeat_row.opacity = 1 if self.mode == "register" else 0
    self.repeat_password.disabled = self.mode != "register"
    self.repeat_password.opacity = 1 if self.mode == "register" else 0
    self.status.text = "Укажи email, ник и пароль" if self.mode == "register" else "Вход через онлайн-аккаунт Supabase"
    # Небольшая плавная анимация при смене режима.
    self.opacity = 0.65
    Animation(opacity=1, duration=0.22, t="out_quad").start(self)
  def _submit(self):
    # Каждая попытка имеет номер: поздний ответ зависшего запроса не должен
    # внезапно переключать экран после того, как пользователь увидел тайм-аут.
    self._auth_generation = getattr(self, "_auth_generation", 0) + 1
    request_id = self._auth_generation
    self._auth_timed_out = False
    email = self.username.text.strip().lower()
    password = self.password.text
    nickname = self.nick_input.text.strip() if self.mode == "register" else ""
    if self.mode == "register" and not re.fullmatch(r"[A-Za-zА-Яа-яЁё0-9_]{3,16}", nickname):
      self.status.text = "Ник: 3–16 символов, только буквы, цифры и _"
      return
    if self.mode == "register" and password != self.repeat_password.text:
      self.status.text = "Пароли не совпадают"
      return
    self.action_btn.disabled = True
    self.status.text = "Связываемся с сервером..."
    action = "signup" if self.mode == "register" else "login"
    # Независимый таймер интерфейса: даже если сетевой вызов зависнет,
    # кнопка разблокируется и пользователь получит понятное сообщение.
    Clock.schedule_once(lambda dt: self._auth_timeout(request_id), 12)
    def worker(_dt=None):
      try:
        auth, error = _supabase_auth(action, email, password, nickname)
        if error:
          Clock.schedule_once(lambda dt: self._auth_finished(False, error, email, password, request_id=request_id), 0)
          return
        if action == "signup" and not auth.get("token"):
          msg = "Аккаунт создан. Подтверди email в письме, затем войди. Если письма нет — проверь спам."
          Clock.schedule_once(lambda dt: self._auth_finished(False, msg, email, password, keep_fields=True, request_id=request_id), 0)
          return
        # Local profile is only a gameplay cache. Authentication is handled by Supabase.
        # Local SQLite is only a cache. Never bind a Supabase user to an old local account.
        base = re.sub(r"[^A-Za-zА-Яа-яЁё0-9_]", "_", email.split("@")[0])[:10].strip("_") or "Player"
        if len(base) < 3: base = (base + "Player")[:10]
        user_id = str((auth.get("user") or {}).get("id", ""))
        suffix = re.sub(r"[^A-Fa-f0-9]", "", user_id)[-5:] or uuid.uuid4().hex[:5]
        local_name = (base[:10] + "_" + suffix)[:16]
        c = _db()
        exists = c.execute("SELECT 1 FROM players WHERE username=?", (local_name,)).fetchone()
        c.close()
        if not exists:
          # Random cache password; the real credential is managed by Supabase Auth.
          ok, msg = create_account(local_name, uuid.uuid4().hex + "aA1!")
          if not ok:
            Clock.schedule_once(lambda dt: self._auth_finished(False, "Не удалось создать локальный кэш: " + msg, email, password, request_id=request_id), 0)
            return
        else:
          _set_session(local_name)
        # Start each online account with its own clean cache and sync it to the server.
        cached = load_data()
        if not cached:
          cached = {"account_id": uuid.uuid4().hex[:12].upper(), "mmr": 0, "coins": 0}
          save_data(cached)
        # Новый телефон: если локальный кэш пустой, подтягиваем прогресс с сервера.
        if set(cached.keys()) <= {"account_id", "mmr", "coins"}:
          remote = _supabase_fetch_save()
          if remote and len(remote) > 3:
            remote.pop("custom_avatar_photo", None)
            if remote.get("avatar") == PHOTO_AVATAR_KEY: remote["avatar"] = "cat_orange"
            remote.setdefault("account_id", cached.get("account_id"))
            save_data(remote)
        # Ник игрока никогда не берётся из почты.
        meta = (auth.get("user") or {}).get("user_metadata") or {}
        cur = load_data()
        if cur and not str(cur.get("nickname") or "").strip():
          chosen = str(meta.get("nickname") or "") if meta.get("nick_chosen") else ""
          if action == "signup" and nickname: chosen = nickname
          if chosen:
            cur["nickname"] = chosen[:16]
          else:
            cur["nickname"] = "Игрок" + str(random.randint(1000, 9999)); cur["nickname_auto"] = True
          save_data(cur)
        # Бан и VIP выдаются на сервере (колонки banned / vip в player_profiles).
        status, _status_error = _supabase_account_status()
        if status and status["banned"]:
          _clear_online_session(); logout_account()
          ban_msg = "Аккаунт заблокирован" + (": " + status["reason"] if status["reason"] else "")
          Clock.schedule_once(lambda dt: self._auth_finished(False, ban_msg, email, password, request_id=request_id), 0)
          return
        if status: _apply_account_status(status)
        Clock.schedule_once(lambda dt: self._auth_finished(True, "Вход выполнен!", email, password, request_id=request_id), 0)
      except Exception as exc:
        err = "Ошибка входа: " + str(exc)[:160]
        Clock.schedule_once(lambda dt: self._auth_finished(False, err, email, password, request_id=request_id), 0)
    threading.Thread(target=worker, daemon=True).start()
  def _auth_timeout(self, request_id):
    # ВАЖНО: таймер не должен блокировать настоящий ответ фонового запроса.
    # Раньше _auth_timed_out=True заставлял _auth_finished игнорировать
    # реальную ошибку Supabase, поэтому пользователь видел только общий таймаут.
    if request_id != getattr(self, "_auth_generation", 0):
      return
    if self.action_btn.disabled:
      self.action_btn.disabled = False
      self.status.text = "Подключение занимает больше 12 секунд. Жду ответ сервера; если он придёт, покажу точную ошибку."
  def _auth_finished(self, ok, msg, email, password, keep_fields=False, request_id=None):
    if request_id is not None and request_id != getattr(self, "_auth_generation", 0):
      return
    self.action_btn.disabled = False
    self.status.text = msg
    if ok:
      self._clear_fields()
      self.manager.current = "main"
    elif not keep_fields and ("Подтверди email" not in msg):
      pass
  def _login(self):
    self.mode = "login"
    self._submit()
  def _register(self):
    self.mode = "register"
    self._submit()
  def on_pre_enter(self, *args):
    self._clear_fields()

# ============================================================
# ИГРА
# ============================================================
class AdminGateScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs); self.build_ui()
  def build_ui(self):
    self.clear_widgets(); self.add_widget(make_game_background("cosmic", "particles_up"))
    root=BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(10))
    root.add_widget(Label(text="ADMIN ACCESS", font_size=dp(26), bold=True, size_hint_y=None, height=dp(58)))
    root.add_widget(Label(text="Защищённый локальный раздел", font_size=dp(13), size_hint_y=None, height=dp(30)))
    self.password_input=GlassTextInput(hint_text="Пароль администратора", password=True, multiline=False, size_hint_y=None, height=dp(50))
    root.add_widget(self.password_input)
    self.status=Label(text="", size_hint_y=None, height=dp(40))
    root.add_widget(self.status)
    enter=GlassButton(text="ВОЙТИ В ADMIN", height=dp(50)); enter.bind(on_press=lambda *_: self.enter_admin()); root.add_widget(enter)
    back=GlassButton(text="Назад", height=dp(46)); back.bind(on_press=lambda *_: self.manager.go_to("main")); root.add_widget(back)
    self.add_widget(root)
  def enter_admin(self):
    from time import monotonic
    now = monotonic()
    if now < getattr(self, "_lock_until", 0):
      self.status.text = "Слишком много попыток. Подождите " + str(int(self._lock_until - now) + 1) + " с"
      return
    if _check_admin_password(self.password_input.text):
      self._fails = 0
      _admin_log("Вход в админ-панель: " + str(ACTIVE_USER or "unknown"))
      self.password_input.text=""; self.manager.current="admin_panel"
    else:
      self._fails = getattr(self, "_fails", 0) + 1
      if self._fails >= 5:
        self._fails = 0; self._lock_until = monotonic() + 30
        self.status.text = "Слишком много попыток. Подождите 30 с"
      else:
        self.status.text = "Неверный пароль"
      _admin_log("Неудачная попытка входа в админ-панель")
  def on_pre_enter(self,*args): self.password_input.text=""; self.status.text=""

class AdminPanelScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs); self.selected=None; self.build_ui()
  def create_settings_snapshot(self):
    try:
      data = load_data()
      snapshot = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "global_theme": current_theme_key(),
        "promo_codes": len(_load_admin_settings().get("promos", [])),
        "case_count": len(data.get("cases", [])) if isinstance(data.get("cases", []), list) else 0,
      }
      with open("admin_settings_snapshot.json", "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, ensure_ascii=False, indent=2)
      if hasattr(self, "status"):
        self.status.text = "Снимок настроек сохранён: admin_settings_snapshot.json"
    except Exception as exc:
      if hasattr(self, "status"):
        self.status.text = "Не удалось сохранить снимок настроек: " + str(exc)
  def build_ui(self):
    self.clear_widgets(); self.add_widget(make_game_background("cosmic", "particles_up"))
    outer=BoxLayout(orientation="vertical", padding=(dp(14),dp(10)), spacing=dp(8))
    head=BoxLayout(orientation="vertical", size_hint_y=None,
             height=dp(92 if Window.width < dp(420) else 84), spacing=dp(6))
    title_label=Label(text="ADMIN PANEL",bold=True,font_size=dp(20),halign="center",valign="middle",size_hint_y=None,height=dp(34))
    title_label.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(8)),v[1])))
    head.add_widget(title_label)
    nav_row=GridLayout(cols=3, spacing=dp(7), size_hint_y=None, height=dp(44),
               row_default_height=dp(44), row_force_default=True)
    accounts_btn=GlassButton(text="Аккаунты",height=dp(44)); accounts_btn.font_size=dp(11); accounts_btn.bind(on_press=lambda *_:self.open_accounts()); nav_row.add_widget(accounts_btn)
    manage_btn=GlassButton(text="Управление",height=dp(44)); manage_btn.font_size=dp(11); manage_btn.bind(on_press=lambda *_:self.open_management()); nav_row.add_widget(manage_btn)
    back=GlassButton(text="В меню",height=dp(44)); back.font_size=dp(11); back.bind(on_press=lambda *_:self.manager.go_to("main")); nav_row.add_widget(back)
    head.add_widget(nav_row)
    outer.add_widget(head)
    tools_row = GridLayout(cols=2, size_hint_y=None, height=dp(48), spacing=dp(7),
               row_default_height=dp(48), row_force_default=True)
    refresh_btn = GlassButton(text="Обновить панель", height=dp(48))
    refresh_btn.font_size = dp(10)
    refresh_btn.bind(on_press=lambda *_: self.build_ui())
    backup_btn = GlassButton(text="Снимок настроек", height=dp(48))
    backup_btn.font_size = dp(10)
    backup_btn.bind(on_press=lambda *_: self.create_settings_snapshot())
    tools_row.add_widget(refresh_btn)
    tools_row.add_widget(backup_btn)
    outer.add_widget(tools_row)
    self.status=Label(text="Локальное управление аккаунтами",font_size=dp(12),size_hint_y=None,height=dp(38),halign="center",valign="middle")
    self.status.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(12)),max(0,v[1]-dp(4)))))
    outer.add_widget(self.status)
    # Старый встроенный список аккаунтов убран: полный список открывается
    # только в отдельном окне по кнопке «Аккаунты».
    self.players_box=GridLayout(cols=1,spacing=dp(7),size_hint_y=None,padding=(0,dp(2)))
    self.players_box.bind(minimum_height=self.players_box.setter("height"))
    details_scroll=ScrollView(size_hint=(1,0.90),do_scroll_x=False,bar_width=dp(3))
    details=BoxLayout(orientation="vertical",spacing=dp(8),size_hint_y=None,padding=(0,dp(4)))
    details.bind(minimum_height=details.setter("height"))
    section_title=Label(text="Выбранный аккаунт",size_hint_y=None,height=dp(34),bold=True,font_size=dp(17),halign="center",valign="middle")
    section_title.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(12)),v[1])))
    details.add_widget(section_title)
    self.selected_label=Label(text="Выбери игрока выше",size_hint_y=None,height=dp(42),font_size=dp(14),halign="center",valign="middle")
    self.selected_label.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(16)),max(0,v[1]-dp(4)))))
    details.add_widget(self.selected_label)
    self.coins_input=GlassTextInput(hint_text="Монеты",multiline=False,size_hint_y=None,height=dp(50)); details.add_widget(self.coins_input)
    self.mmr_input=GlassTextInput(hint_text="MMR",multiline=False,size_hint_y=None,height=dp(50)); details.add_widget(self.mmr_input)
    actions=GridLayout(cols=2,spacing=(dp(8),dp(8)),size_hint_y=None,
             height=dp(3*54+2*8+8),row_default_height=dp(54),row_force_default=True,padding=dp(4))
    save=GlassButton(text="Сохранить статы",height=dp(48),size_hint_y=None); save.font_size=dp(11); save.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(8)),max(0,v[1]-dp(4))))); save.halign="center"; save.valign="middle"; save.bind(on_press=lambda *_:self.save_stats()); actions.add_widget(save)
    self.ban_button=GlassButton(text="Забанить",height=dp(48),size_hint_y=None); self.ban_button.font_size=dp(11); self.ban_button.halign="center"; self.ban_button.valign="middle"; self.ban_button.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(12)),max(0,v[1]-dp(8))))); self.ban_button.bind(on_press=lambda *_:self.toggle_ban()); actions.add_widget(self.ban_button)
    refresh=GlassButton(text="Обновить список",height=dp(48),size_hint_y=None); refresh.font_size=dp(10); refresh.halign="center"; refresh.valign="middle"; refresh.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(12)),max(0,v[1]-dp(8))))); refresh.bind(on_press=lambda *_:self.refresh_players()); actions.add_widget(refresh)
    logs=GlassButton(text="Показать журнал",height=dp(48),size_hint_y=None); logs.font_size=dp(10); logs.halign="center"; logs.valign="middle"; logs.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(12)),max(0,v[1]-dp(8))))); logs.bind(on_press=lambda *_:self.show_logs()); actions.add_widget(logs)
    self.leaderboard_button=GlassButton(text="Убрать из лидерборда",height=dp(48),size_hint_y=None); self.leaderboard_button.font_size=dp(10); self.leaderboard_button.halign="center"; self.leaderboard_button.valign="middle"; self.leaderboard_button.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(12)),max(0,v[1]-dp(8))))); self.leaderboard_button.bind(on_press=lambda *_:self.toggle_leaderboard_visibility()); actions.add_widget(self.leaderboard_button)
    self.vip_button=GlassButton(text="Выдать VIP",height=dp(48),size_hint_y=None); self.vip_button.font_size=dp(11); self.vip_button.halign="center"; self.vip_button.valign="middle"; self.vip_button.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(12)),max(0,v[1]-dp(8))))); self.vip_button.bind(on_press=lambda *_:self.grant_vip()); actions.add_widget(self.vip_button)
    details.add_widget(actions)
    details_scroll.add_widget(details); outer.add_widget(details_scroll)
    self.add_widget(outer); self.refresh_players()
  def open_accounts(self):
    body=BoxLayout(orientation="vertical",spacing=dp(8),padding=(dp(2),dp(4)))
    search=GlassTextInput(hint_text="Поиск аккаунта по нику...",multiline=False,size_hint_y=None,height=dp(46))
    body.add_widget(search)
    count=Label(text="",size_hint_y=None,height=dp(25),font_size=dp(12)); body.add_widget(count)
    scroll=ScrollView(do_scroll_x=False,bar_width=dp(3))
    rows=GridLayout(cols=1,spacing=dp(6),size_hint_y=None,padding=dp(2)); rows.bind(minimum_height=rows.setter("height")); scroll.add_widget(rows); body.add_widget(scroll)
    pop=_open_glass_popup("ВСЕ АККАУНТЫ",body,(.93,.84))
    def refresh(*_):
      rows.clear_widgets(); _ensure_account_ids(); c=sqlite3.connect(DB_FILE)
      data=c.execute("SELECT username,created_at,data_json FROM players ORDER BY username COLLATE NOCASE").fetchall(); c.close()
      term=search.text.strip().casefold(); filtered=[r for r in data if term in r[0].casefold()]
      count.text=f"Найдено аккаунтов: {len(filtered)} / {len(data)}"
      for username,created,raw in filtered:
        try: d=json.loads(raw or "{}")
        except Exception: d={}
        info=f"{username}  •  ID: {d.get('account_id','—')}\nСоздан: {created or 'неизвестно'}"
        b=GlassButton(text=info,height=dp(58)); b.font_size=dp(12); b.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(18)),max(0,v[1]-dp(8)))))
        b.bind(on_press=lambda _b,u=username:(self.select_player(u),pop.dismiss()))
        rows.add_widget(b)
      if not filtered: rows.add_widget(Label(text="Ничего не найдено",size_hint_y=None,height=dp(42)))
    search.bind(text=refresh); refresh()
    return pop
  def open_management(self):
    body=BoxLayout(orientation="vertical",spacing=dp(10),padding=dp(4))
    intro=Label(text="Общее оформление и акции CataBox",size_hint_y=None,height=dp(42),font_size=dp(13)); body.add_widget(intro)
    shop=GlassButton(text="Магазин акций",height=dp(54)); shop.bind(on_press=lambda *_:self.open_offer_manager()); body.add_widget(shop)
    themes=GlassButton(text="Темы оформления",height=dp(54)); themes.bind(on_press=lambda *_:self.open_theme_manager()); body.add_widget(themes)
    promos=GlassButton(text="Промокоды",height=dp(54)); promos.bind(on_press=lambda *_:self.open_promo_manager()); body.add_widget(promos)
    offers=GlassButton(text="Акции: добавить / убрать",height=dp(54)); offers.bind(on_press=lambda *_:self.open_offer_manager()); body.add_widget(offers)
    tools=GlassButton(text="Инструменты разработчика",height=dp(54)); tools.bind(on_press=lambda *_:self.open_dev_tools()); body.add_widget(tools)
    return _open_glass_popup("УПРАВЛЕНИЕ ИГРОЙ",body,(.90,.84))
  def open_offer_manager(self):
    data=_load_admin_settings(); body=BoxLayout(orientation="vertical",spacing=dp(7),padding=dp(3))
    body.add_widget(Label(text="Добавление акций в магазин",size_hint_y=None,height=dp(32),font_size=dp(12)))
    scroll=ScrollView(do_scroll_x=False,bar_width=dp(3)); rows=BoxLayout(orientation="vertical",spacing=dp(7),size_hint_y=None,padding=dp(2)); rows.bind(minimum_height=rows.setter("height")); scroll.add_widget(rows); body.add_widget(scroll)
    def refresh():
      rows.clear_widgets(); current=_load_admin_settings(); active=current.get("offers",[])
      for offer in DEFAULT_OFFERS:
        is_on=any(o.get("id")==offer["id"] for o in active)
        row=BoxLayout(orientation="horizontal",spacing=dp(5),size_hint_y=None,height=dp(64))
        label=Label(text=f"{offer['title']}\n{offer['description']}",font_size=dp(10),halign="left",valign="middle")
        label.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(4)),max(0,v[1]-dp(4)))))
        row.add_widget(label)
        btn=GlassButton(text="Убрать" if is_on else "Добавить",height=dp(42),size_hint_x=None,width=dp(92)); btn.font_size=dp(11)
        def toggle(_b, item=offer, enabled=is_on):
          fresh=_load_admin_settings(); offers=fresh.get("offers",[])
          if enabled:
            offers=[o for o in offers if o.get("id") != item["id"]]
            msg="Акция убрана: "+item["title"]
          else:
            if any(o.get("id")==item["id"] for o in offers): return
            offers.append(dict(item)); msg="Акция добавлена: "+item["title"]
          fresh["offers"]=offers
          if _save_admin_settings(fresh): self.status.text=msg; _admin_log(str(ACTIVE_USER)+": "+msg); refresh()
        btn.bind(on_press=toggle); row.add_widget(btn); rows.add_widget(row)
      rows.add_widget(Label(text="Активных акций: "+str(len(active)),size_hint_y=None,height=dp(28),bold=True))
    refresh(); _open_glass_popup("МАГАЗИН АКЦИЙ",body,(.94,.82))
  def open_theme_manager(self):
    body=BoxLayout(orientation="vertical",spacing=dp(7),padding=dp(3))
    intro=Label(text="Тема меняет фон и иконку шахты для всех игроков. Анимированных обоев в игре больше нет.",size_hint_y=None,height=dp(50),font_size=dp(12),halign="center",valign="middle")
    intro.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(12)),None))); body.add_widget(intro)
    sc=ScrollView(do_scroll_x=False,bar_width=dp(3)); rows=BoxLayout(orientation="vertical",spacing=dp(8),size_hint_y=None,padding=dp(2)); rows.bind(minimum_height=rows.setter("height")); sc.add_widget(rows); body.add_widget(sc)
    holder={"pop":None}
    def build_rows():
      rows.clear_widgets(); current=current_theme_key()
      for key,theme in THEMES.items():
        row=BoxLayout(orientation="horizontal",spacing=dp(8),size_hint_y=None,height=dp(104))
        preview=StaticWallpaperBg(theme["wallpaper"],rounded_preview=True,size_hint=(None,1),width=dp(90)); row.add_widget(preview)
        col=BoxLayout(orientation="vertical",spacing=dp(4))
        info=Label(text=("✓  " if key==current else "")+theme["name"]+"\n"+theme["desc"],font_size=dp(11),halign="left",valign="middle")
        info.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(4)),max(0,v[1]-dp(2)))))
        col.add_widget(info)
        btn=GlassButton(text="Выбрана" if key==current else "Применить",height=dp(38),size_hint_y=None); btn.font_size=dp(12); btn.disabled=(key==current)
        btn.bind(on_press=lambda _b,k=key,t=theme:apply(k,t)); col.add_widget(btn)
        row.add_widget(col); rows.add_widget(row)
    def apply(key,theme):
      fresh=_load_admin_settings(); fresh["global_theme"]=key
      if not _save_admin_settings(fresh):
        self.status.text="Не удалось сохранить тему"; return
      _admin_log(str(ACTIVE_USER)+": тема оформления -> "+key)
      self.status.text="Тема: "+theme["name"]
      apply_theme_everywhere()
      try: self.manager.get_screen("main")._build_ui()
      except Exception: pass
      build_rows()
    build_rows()
    holder["pop"]=_open_glass_popup("ТЕМЫ ОФОРМЛЕНИЯ",body,(.94,.88)); return holder["pop"]
  def open_promo_manager(self):
    body=BoxLayout(orientation="vertical",spacing=dp(6),padding=dp(3))
    sc=ScrollView(do_scroll_x=False,bar_width=dp(3),size_hint=(1,.42)); rows=BoxLayout(orientation="vertical",spacing=dp(5),size_hint_y=None,padding=dp(2)); rows.bind(minimum_height=rows.setter("height")); sc.add_widget(rows); body.add_widget(sc)
    kinds=["coins","case","frame","avatar"]; hints={"coins":"Сумма монет, например 5000","case":"Ключ кейса: cats, ice, fire, magic...","frame":"Ключ рамки: gold_frame, ruby_frame...","avatar":"Ключ аватарки: fy_crown, cat_orange..."}
    state={"i":0}
    code_in=GlassTextInput(hint_text="Код промокода (буквы и цифры)",multiline=False,size_hint_y=None,height=dp(42))
    type_btn=GlassButton(text="Награда: Монеты",height=dp(40),size_hint_y=None); type_btn.font_size=dp(12)
    val_in=GlassTextInput(hint_text=hints["coins"],multiline=False,size_hint_y=None,height=dp(42))
    limit_in=GlassTextInput(hint_text="Лимит активаций (пусто = без лимита)",multiline=False,size_hint_y=None,height=dp(42))
    days_in=GlassTextInput(hint_text="Срок действия в днях (пусто = бессрочно)",multiline=False,size_hint_y=None,height=dp(42))
    msg=Label(text="",font_size=dp(11),size_hint_y=None,height=dp(30),halign="center",valign="middle",color=(1,.8,.5,1))
    msg.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(8)),None)))
    def cycle(*_):
      state["i"]=(state["i"]+1)%len(kinds); k=kinds[state["i"]]
      type_btn.text="Награда: "+PROMO_TYPE_LABELS[k]; val_in.hint_text=hints[k]; val_in.text=""
    type_btn.bind(on_press=cycle)
    def refresh():
      rows.clear_widgets(); promos=_load_admin_settings().get("promos",[])
      if not promos: rows.add_widget(Label(text="Созданных промокодов пока нет",size_hint_y=None,height=dp(30),font_size=dp(12)))
      for item in promos:
        code=_norm_promo(item.get("code")); ptype=item.get("type","coins")
        value=item.get("amount") if ptype=="coins" else item.get("kind")
        limit=int(item.get("max_uses",0) or 0)
        text=f"{code}\n{PROMO_TYPE_LABELS.get(ptype,ptype)}: {value}  •  активаций {int(item.get('uses',0) or 0)}/{limit or '∞'}  •  до {item.get('expires') or '∞'}"
        row=BoxLayout(orientation="horizontal",spacing=dp(5),size_hint_y=None,height=dp(52))
        lbl=Label(text=text,font_size=dp(10),halign="left",valign="middle"); lbl.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(4)),None))); row.add_widget(lbl)
        d=GlassButton(text="Удалить",height=dp(38),size_hint=(None,None),size=(dp(84),dp(38))); d.font_size=dp(11)
        d.bind(on_press=lambda _b,c=code:delete(c)); row.add_widget(d); rows.add_widget(row)
    def delete(code):
      fresh=_load_admin_settings(); fresh["promos"]=[p for p in fresh.get("promos",[]) if _norm_promo(p.get("code"))!=code]
      if _save_admin_settings(fresh): _admin_log(str(ACTIVE_USER)+": удалён промокод "+code); msg.text="Промокод удалён: "+code; refresh()
    def create(*_):
      code=_norm_promo(code_in.text); ptype=kinds[state["i"]]; value=val_in.text.strip()
      if len(code)<4 or not re.fullmatch(r"[A-Z0-9_\-]+",code): msg.text="Код: минимум 4 символа, только латиница, цифры, _ и -"; return
      if code in _all_promos(): msg.text="Такой промокод уже существует"; return
      item={"code":code,"type":ptype,"uses":0}
      if ptype=="coins":
        try: amount=int(value)
        except ValueError: amount=0
        if amount<=0: msg.text="Укажи сумму монет числом больше нуля"; return
        item["amount"]=amount
      else:
        if not promo_kind_is_valid(ptype,value): msg.text="Неизвестный ключ награды: "+(value or "пусто"); return
        item["kind"]=value
      try: limit=int(limit_in.text.strip() or 0)
      except ValueError: msg.text="Лимит должен быть числом"; return
      if limit>0: item["max_uses"]=limit
      try: days=int(days_in.text.strip() or 0)
      except ValueError: msg.text="Срок должен быть числом дней"; return
      if days>0: item["expires"]=(date.today()+timedelta(days=days)).isoformat()
      fresh=_load_admin_settings(); fresh["promos"]=list(fresh.get("promos",[]))+[item]
      if _save_admin_settings(fresh):
        _admin_log(str(ACTIVE_USER)+": создан промокод "+code); msg.text="Промокод создан: "+code
        code_in.text=""; val_in.text=""; limit_in.text=""; days_in.text=""; refresh()
      else: msg.text="Не удалось сохранить промокод"
    create_btn=GlassButton(text="Создать промокод",height=dp(44),size_hint_y=None); create_btn.bind(on_press=create)
    for w in (code_in,type_btn,val_in,limit_in,days_in,create_btn,msg): body.add_widget(w)
    refresh(); return _open_glass_popup("ПРОМОКОДЫ",body,(.94,.92))
  def open_dev_tools(self):
    body=BoxLayout(orientation="vertical",spacing=dp(7),padding=dp(3))
    body.add_widget(Label(text="Безопасные инструменты для разработки",size_hint_y=None,height=dp(34),font_size=dp(13)))
    def add_button(title, callback):
      b=GlassButton(text=title,height=dp(46),size_hint_y=None); b.bind(on_press=callback); body.add_widget(b)
    def summary(*_):
      c=sqlite3.connect(DB_FILE); accounts=c.execute("SELECT COUNT(*) FROM players").fetchone()[0]; c.close()
      settings=_load_admin_settings(); offers=len(settings.get("offers",[]))
      self.status.text=f"Аккаунтов: {accounts} | Активных акций: {offers} | База: players.db"
    def export_report(*_):
      c=sqlite3.connect(DB_FILE); rows=c.execute("SELECT username,created_at FROM players ORDER BY username COLLATE NOCASE").fetchall(); c.close()
      report_path=os.path.join(DATA_DIR,"admin_report.txt")
      with open(report_path,"w",encoding="utf-8") as f:
        f.write("CataBox — локальный отчёт\n")
        f.write(f"Аккаунтов: {len(rows)}\n")
        f.write("\n".join(f"{u} | {created}" for u,created in rows))
      self.status.text="Отчёт сохранён: admin_report.txt"
      _admin_log("Создан локальный отчёт администратора")
    add_button("Сводка состояния игры",summary)
    add_button("Создать отчёт аккаунтов",export_report)
    add_button("Открыть журнал действий",lambda *_:self.show_logs())
    add_button("Обновить список аккаунтов",lambda *_:self.refresh_players())
    return _open_glass_popup("ИНСТРУМЕНТЫ РАЗРАБОТЧИКА",body,(.90,.62))

  def refresh_players(self):
    self.players_box.clear_widgets(); _admin_tables(); _ensure_account_ids()
    c=sqlite3.connect(DB_FILE); rows=c.execute("SELECT username,data_json FROM players ORDER BY username COLLATE NOCASE").fetchall(); c.close()
    for username, raw in rows:
      try: d=json.loads(raw or "{}")
      except Exception: d={}
      # Кнопка выбора содержит только ник аккаунта.
      b=GlassButton(text=username,height=dp(46))
      b.font_size=dp(14)
      b.halign="center"; b.valign="middle"
      b.bind(size=lambda w,v:setattr(w,"text_size",(max(0,v[0]-dp(22)),max(0,v[1]-dp(8)))))
      b.bind(on_press=lambda _b,u=username:self.select_player(u)); self.players_box.add_widget(b)
    if not rows: self.status.text="Аккаунтов пока нет"
  def select_player(self, username):
    self.selected=username; c=sqlite3.connect(DB_FILE); row=c.execute("SELECT data_json FROM players WHERE username=?",(username,)).fetchone(); c.close()
    try: d=json.loads(row[0] or "{}") if row else {}
    except Exception: d={}
    self.selected_label.text="Выбран: "+username; self.coins_input.text=str(d.get("coins",0)); self.mmr_input.text=str(d.get("mmr",0))
    is_banned = _is_banned(username) is not None
    self.status.text="Заблокирован" if is_banned else "Аккаунт выбран"
    if hasattr(self, "ban_button"): self.ban_button.text = "Снять бан" if is_banned else "Забанить"
    if hasattr(self, "leaderboard_button"): self.leaderboard_button.text = "Вернуть в лидерборд" if d.get("leaderboard_hidden", False) else "Убрать из лидерборда"
    if hasattr(self, "vip_button"): self.vip_button.text = "VIP уже выдан" if d.get("vip", False) else "Выдать VIP"
  def save_stats(self):
    if not self.selected: self.status.text="Сначала выбери аккаунт"; return
    try: coins=max(0,int(self.coins_input.text)); mmr=max(0,int(self.mmr_input.text))
    except ValueError: self.status.text="Монеты и MMR должны быть целыми числами"; return
    c=sqlite3.connect(DB_FILE); row=c.execute("SELECT data_json FROM players WHERE username=?",(self.selected,)).fetchone()
    if not row: c.close(); self.status.text="Аккаунт не найден"; return
    try: d=json.loads(row[0] or "{}")
    except Exception: d={}
    d["coins"]=coins; d["mmr"]=mmr
    c.execute("UPDATE players SET data_json=? WHERE username=?",(json.dumps(d,ensure_ascii=False),self.selected)); c.commit(); c.close()
    _admin_log(f"{ACTIVE_USER}: изменены монеты/MMR игрока {self.selected} -> coins={coins}, mmr={mmr}")
    self.status.text="Сохранено"; self.refresh_players(); self.select_player(self.selected)
  def toggle_ban(self):
    if not self.selected: self.status.text="Сначала выбери аккаунт"; return
    if self.selected.lower() == str(ACTIVE_USER or "").lower(): self.status.text="Нельзя заблокировать свой аккаунт"; return
    _admin_tables(); c=sqlite3.connect(DB_FILE); row=c.execute("SELECT reason FROM local_bans WHERE username=?",(self.selected,)).fetchone()
    if row:
      c.execute("DELETE FROM local_bans WHERE username=?",(self.selected,)); msg="Снят бан с " + self.selected
    else:
      c.execute("INSERT INTO local_bans(username,reason) VALUES(?,?)",(self.selected,"Блокировка администратором")); msg="Заблокирован " + self.selected
    c.commit(); c.close(); _admin_log(str(ACTIVE_USER)+": "+msg); self.status.text=msg; self.refresh_players(); self.select_player(self.selected)
  def toggle_leaderboard_visibility(self):
    if not self.selected:
      self.status.text="Сначала выбери аккаунт"; return
    c=sqlite3.connect(DB_FILE)
    row=c.execute("SELECT data_json FROM players WHERE username=?",(self.selected,)).fetchone()
    if not row:
      c.close(); self.status.text="Аккаунт не найден"; return
    try: d=json.loads(row[0] or "{}")
    except Exception: d={}
    hidden=not bool(d.get("leaderboard_hidden",False))
    d["leaderboard_hidden"]=hidden
    c.execute("UPDATE players SET data_json=? WHERE username=?",(json.dumps(d,ensure_ascii=False),self.selected)); c.commit(); c.close()
    msg=("Убран из лидерборда: " if hidden else "Возвращён в лидерборд: ")+self.selected
    _admin_log(str(ACTIVE_USER)+": "+msg); self.status.text=msg
    self.select_player(self.selected)
  def grant_vip(self):
    if not self.selected:
      self.status.text="Сначала выбери аккаунт"; return
    c=sqlite3.connect(DB_FILE)
    row=c.execute("SELECT data_json FROM players WHERE username=?",(self.selected,)).fetchone()
    if not row:
      c.close(); self.status.text="Аккаунт не найден"; return
    try: d=json.loads(row[0] or "{}")
    except Exception: d={}
    if d.get("vip",False):
      c.close(); self.status.text="У этого аккаунта уже есть VIP"; self.select_player(self.selected); return
    d["vip"]=True
    d["tap_boost"]=5
    d["coins"]=max(0,int(d.get("coins",0) or 0))+10000
    c.execute("UPDATE players SET data_json=? WHERE username=?",(json.dumps(d,ensure_ascii=False),self.selected)); c.commit(); c.close()
    msg="VIP выдан: "+self.selected+" (+10000 монет, добыча x5)"
    _admin_log(str(ACTIVE_USER)+": "+msg); self.status.text=msg
    self.select_player(self.selected)
  def show_logs(self):
    _admin_tables(); c=sqlite3.connect(DB_FILE); rows=c.execute("SELECT created_at,action FROM admin_log ORDER BY id DESC LIMIT 15").fetchall(); c.close()
    self.status.text="Журнал открыт — последние 15 действий" if rows else "Журнал пока пуст"
    if rows:
      from kivy.uix.popup import Popup
      body=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(8))
      log_text=Label(text="\n".join(f"{t}: {a}" for t,a in rows),halign="left",valign="top",font_size=dp(12),size_hint_y=None)
      log_text.bind(width=lambda w,v:setattr(w,"text_size",(v,None)), texture_size=lambda w,v:setattr(w,"height",v[1]))
      sc=ScrollView(); sc.add_widget(log_text); body.add_widget(sc)
      close=GlassButton(text="Закрыть",height=dp(44),size_hint_y=None); body.add_widget(close)
      pop=Popup(title="Журнал администратора",content=body,size_hint=(0.92,0.75)); close.bind(on_press=pop.dismiss); pop.open()
  def on_pre_enter(self,*args): self.refresh_players()

class LeaderboardScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.build_ui()

  def build_ui(self):
    self.clear_widgets()
    self.add_widget(make_game_background("cosmic", "particles_up"))
    root = BoxLayout(orientation="vertical", padding=(dp(12), dp(12)), spacing=dp(8))
    head = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
    title = Label(text="ТОП ПО MMR", bold=True, font_size=dp(21), halign="left", valign="middle")
    title.bind(size=lambda w, v: setattr(w, "text_size", v))
    head.add_widget(title)
    back = GlassButton(text="Назад", height=dp(42), size_hint_x=None, width=dp(96))
    back.bind(on_press=lambda *_: self.manager.go_to("main"))
    head.add_widget(back)
    root.add_widget(head)
    root.add_widget(Label(text="Локальный рейтинг аккаунтов", size_hint_y=None, height=dp(25), font_size=dp(12)))
    self.online_status = Label(text="Supabase: проверяем подключение…", size_hint_y=None, height=dp(22), font_size=dp(10), color=(0.65, 0.78, 1, 1))
    root.add_widget(self.online_status)
    scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
    self.rows_box = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=(0, dp(4)))
    self.rows_box.bind(minimum_height=self.rows_box.setter("height"))
    scroll.add_widget(self.rows_box)
    root.add_widget(scroll)
    refresh = GlassButton(text="Обновить рейтинг", height=dp(46), size_hint_y=None)
    refresh.bind(on_press=lambda *_: self.refresh_players())
    root.add_widget(refresh)
    self.add_widget(root)
    self.refresh_players()
    self.check_online_connection()

  def check_online_connection(self):
    def worker():
      rows, error = _supabase_get_profiles()
      def update_status(_dt):
        if not hasattr(self, "online_status"): return
        if error is None:
          self.online_status.text = "Supabase подключён: онлайн-профилей " + str(len(rows))
          self.online_status.color = (0.35, 1, 0.65, 1)
        else:
          self.online_status.text = "Supabase: " + error
          self.online_status.color = (1, 0.68, 0.38, 1)
      Clock.schedule_once(update_status, 0)
    threading.Thread(target=worker, daemon=True).start()

  def refresh_players(self):
    # Online leaderboard only: deliberately do not read local players.db here.
    self.rows_box.clear_widgets()
    self.online_status.text = "Загружаем онлайн-рейтинг…"
    self.online_status.color = (0.65, 0.78, 1, 1)
    def worker():
      rows, error = _supabase_get_profiles()
      def show(_dt):
        if not hasattr(self, "rows_box"):
          return
        self.rows_box.clear_widgets()
        if error:
          self.online_status.text = "Supabase: " + error
          self.online_status.color = (1, 0.68, 0.38, 1)
          self.rows_box.add_widget(Label(text="Не удалось загрузить онлайн-рейтинг\nПроверь подключение и настройки Supabase.", size_hint_y=None, height=dp(70), halign="center", valign="middle"))
          return
        self.online_status.text = "Supabase подключён: онлайн-профилей " + str(len(rows))
        self.online_status.color = (0.35, 1, 0.65, 1)
        players = []
        for row in rows:
          if not isinstance(row, dict):
            continue
          nickname = str(row.get("nickname") or "Player")[:32]
          try: mmr = max(0, int(row.get("mmr", 0) or 0))
          except Exception: mmr = 0
          avatar = str(row.get("avatar") or "cat_orange")
          players.append((mmr, nickname, avatar))
        players.sort(key=lambda item: (-item[0], item[1].lower()))
        for place, (mmr, nickname, avatar_key) in enumerate(players, 1):
          card = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(88), spacing=dp(8), padding=(dp(8), dp(6)))
          from kivy.graphics import Color, RoundedRectangle, Line
          with card.canvas.before:
            Color(0.075, 0.085, 0.17, 0.96)
            card._bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(15)])
            Color(0.42, 0.40, 0.72, 1)
            card._outline = Line(rounded_rectangle=(card.x, card.y, card.width, card.height, dp(15)), width=dp(1.1))
          def _redraw_card(w, *_):
            w._bg.pos = w.pos; w._bg.size = w.size
            w._outline.rounded_rectangle = (w.x, w.y, w.width, w.height, dp(15))
          card.bind(pos=_redraw_card, size=_redraw_card)
          avatar_holder = FloatLayout(size_hint=(None, None), size=(dp(66), dp(66)))
          try:
            art = avatar_to_art(avatar_key, dp(42))
            art.size_hint = (None, None); art.size = (dp(42), dp(42))
            art.pos_hint = {"center_x": 0.5, "center_y": 0.5}
            avatar_holder.add_widget(art)
          except Exception:
            pass
          card.add_widget(avatar_holder)
          info = BoxLayout(orientation="vertical", spacing=dp(2))
          name = Label(text=f"#{place}  {nickname}", bold=True, font_size=dp(14), halign="left", valign="middle", size_hint_y=None, height=dp(28), shorten=True, shorten_from="right")
          name.bind(size=lambda w, v: setattr(w, "text_size", v))
          info.add_widget(name)
          rank_idx = max(0, min(rank_index_by_mmr(mmr), len(RANKS)-1))
          meta = Label(text=f"{mmr} MMR  |  {RANKS[rank_idx][1]}", font_size=dp(11), halign="left", valign="middle", size_hint_y=None, height=dp(22))
          meta.bind(size=lambda w, v: setattr(w, "text_size", v))
          info.add_widget(meta)
          card.add_widget(info)
          badge_holder = FloatLayout(size_hint=(None, None), size=(dp(40), dp(48)))
          badge = RankIcon(rank_idx, dp(38)); badge.size_hint=(None, None); badge.size=(dp(38), dp(38)); badge.pos_hint={"center_x":0.5,"center_y":0.5}
          badge_holder.add_widget(badge); card.add_widget(badge_holder)
          self.rows_box.add_widget(card)
        if not players:
          self.rows_box.add_widget(Label(text="Онлайн-игроков пока нет.\nСоздай аккаунт и войди, чтобы появиться в рейтинге.", size_hint_y=None, height=dp(70), halign="center", valign="middle"))
      Clock.schedule_once(show, 0)
    threading.Thread(target=worker, daemon=True).start()

  def on_pre_enter(self, *args):
    self.refresh_players()



# ============================================================
# ДРУЗЬЯ И ПУБЛИЧНЫЕ ПРОФИЛИ
# Работает между аккаунтами в локальной базе этого приложения.
# Для приглашений между разными телефонами нужен онлайн-сервер.
# ============================================================
def _ensure_social_tables():
  c = _db()
  c.execute("CREATE TABLE IF NOT EXISTS friend_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT NOT NULL COLLATE NOCASE, receiver TEXT NOT NULL COLLATE NOCASE, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(sender, receiver))")
  c.execute("CREATE TABLE IF NOT EXISTS friendships (user_a TEXT NOT NULL COLLATE NOCASE, user_b TEXT NOT NULL COLLATE NOCASE, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_a, user_b))")
  c.commit(); c.close()

def _social_status(me, other):
  if not me or not other or me.lower() == other.lower(): return 'self'
  _ensure_social_tables(); c = _db()
  pair = c.execute("SELECT 1 FROM friendships WHERE (user_a=? AND user_b=?) OR (user_a=? AND user_b=?)", (me, other, other, me)).fetchone()
  if pair: status = 'friends'
  else:
    incoming = c.execute("SELECT status FROM friend_requests WHERE sender=? AND receiver=?", (other, me)).fetchone()
    outgoing = c.execute("SELECT status FROM friend_requests WHERE sender=? AND receiver=?", (me, other)).fetchone()
    status = 'incoming' if incoming and incoming[0] == 'pending' else ('outgoing' if outgoing and outgoing[0] == 'pending' else 'none')
  c.close(); return status

def _send_friend_request(sender, receiver):
  if not sender or not receiver or sender.lower() == receiver.lower(): return False, 'Нельзя добавить этот аккаунт'
  _ensure_social_tables(); c = _db()
  exists = c.execute("SELECT username FROM players WHERE username=?", (receiver,)).fetchone()
  if not exists: c.close(); return False, 'Игрок не найден'
  status = _social_status(sender, receiver)
  if status == 'friends': c.close(); return False, 'Вы уже друзья'
  if status == 'incoming': c.close(); return False, 'У этого игрока уже есть приглашение для вас'
  if status == 'outgoing': c.close(); return False, 'Приглашение уже отправлено'
  try:
    c.execute("INSERT INTO friend_requests(sender,receiver,status) VALUES(?,?,'pending')", (sender, receiver)); c.commit()
    return True, 'Приглашение отправлено'
  except sqlite3.IntegrityError:
    return False, 'Приглашение уже существует'
  finally: c.close()

def _accept_friend_request(sender, receiver):
  _ensure_social_tables(); c = _db()
  row = c.execute("SELECT id FROM friend_requests WHERE sender=? AND receiver=? AND status='pending'", (sender, receiver)).fetchone()
  if not row: c.close(); return False
  a, b = sorted((sender.lower(), receiver.lower()))
  c.execute("INSERT OR IGNORE INTO friendships(user_a,user_b) VALUES(?,?)", (a,b))
  c.execute("UPDATE friend_requests SET status='accepted' WHERE id=?", (row[0],))
  c.commit(); c.close(); return True

class PublicProfileScreen(Screen):
  def __init__(self, **kwargs):
    super().__init__(**kwargs); self.target_username = None
  def show_player(self, username):
    self.target_username = username; self.clear_widgets()
    self.add_widget(make_game_background('cosmic', 'particles_up'))
    root = BoxLayout(orientation='vertical', padding=dp(18), spacing=dp(10))
    root.add_widget(Label(text='ПРОФИЛЬ ИГРОКА', font_size=dp(22), bold=True, size_hint_y=None, height=dp(42)))
    c = _db(); row = c.execute('SELECT data_json FROM players WHERE username=?', (username,)).fetchone(); c.close()
    if not row:
      root.add_widget(Label(text='Игрок не найден')); self.add_widget(root); return
    try: d = json.loads(row[0] or '{}')
    except Exception: d = {}
    root.add_widget(ProfileDecorBanner(
      title='VIP PROFILE' if d.get('vip', False) else 'PLAYER CARD',
      subtitle='РАДУЖНЫЙ НИК АКТИВЕН' if d.get('vip', False) else 'ПРОФИЛЬ ИГРОКА'))
    mmr = max(0, int(d.get('mmr',0) or 0)); ri = max(0,min(int(d.get('profile_rank',rank_index_by_mmr(mmr))),len(RANKS)-1))
    avatar_holder = FloatLayout(size_hint_y=None, height=dp(145))
    frame = FrameArt(str(d.get('frame','none')), dp(145)); frame.pos_hint={'center_x':.5,'center_y':.5}; avatar_holder.add_widget(frame)
    art = avatar_to_art(str(d.get('avatar','cat_orange')), dp(54)); art.size_hint=(None,None); art.size=(dp(54),dp(54)); art.pos_hint={'center_x':.5,'center_y':.5}; avatar_holder.add_widget(art)
    root.add_widget(avatar_holder)
    public_name = str(d.get('nickname') or username)
    public_name_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=dp(5), padding=(dp(20),0))
    NameLabel = RainbowNickLabel if d.get('vip', False) else Label
    public_name_kwargs = {"rainbow_style": d.get("rainbow_nick_style", "classic")} if d.get('vip', False) else {}
    public_name_label = NameLabel(**public_name_kwargs, text=public_name, font_size=dp(21), bold=True, shorten=True, shorten_from='right', halign='right', valign='middle')
    public_name_label.bind(size=lambda w,v:setattr(w,'text_size',v))
    public_name_row.add_widget(public_name_label)
    root.add_widget(public_name_row)
    root.add_widget(Label(text=f"Ранг: {RANKS[ri][1]}    MMR: {mmr}", font_size=dp(16), size_hint_y=None, height=dp(28)))
    root.add_widget(Label(text=f"ID игрока: {d.get('account_id','—')}", font_size=dp(12), size_hint_y=None, height=dp(24)))
    me = _session_user(); status = _social_status(me, username)
    self.status_label = Label(text='', size_hint_y=None, height=dp(30)); root.add_widget(self.status_label)
    if status == 'none':
      btn = GlassButton(text='Добавить в друзья', height=dp(46)); btn.bind(on_press=lambda *_: self._invite()); root.add_widget(btn)
    elif status == 'incoming':
      btn = GlassButton(text='Принять приглашение', height=dp(46)); btn.bind(on_press=lambda *_: self._accept()); root.add_widget(btn)
    elif status == 'outgoing': self.status_label.text = 'Приглашение отправлено'
    elif status == 'friends': self.status_label.text = 'Вы уже друзья'
    else: self.status_label.text = 'Это ваш профиль'
    friends_btn = GlassButton(text='Друзья и приглашения', height=dp(44)); friends_btn.bind(on_press=lambda *_: self.manager.go_to('friends')); root.add_widget(friends_btn)
    back = GlassButton(text='Назад к лидерборду', height=dp(44)); back.bind(on_press=lambda *_: self.manager.go_to('leaderboard')); root.add_widget(back)
    self.add_widget(root)
  def _invite(self):
    ok, msg = _send_friend_request(_session_user(), self.target_username)
    self.status_label.text = msg
    if ok: Clock.schedule_once(lambda dt: self.show_player(self.target_username), .5)
  def _accept(self):
    if _accept_friend_request(self.target_username, _session_user()): self.show_player(self.target_username)
    else: self.status_label.text = 'Приглашение уже недоступно'

class FriendsScreen(Screen):
  def __init__(self, **kwargs): super().__init__(**kwargs); self.build_ui()
  def build_ui(self):
    self.clear_widgets(); self.add_widget(make_game_background())
    root=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(8))
    root.add_widget(Label(text='ДРУЗЬЯ',font_size=dp(23),bold=True,size_hint_y=None,height=dp(42)))
    self.status_lbl=Label(text='',font_size=dp(12),size_hint_y=None,height=dp(22),color=(1,.8,.5,1)); root.add_widget(self.status_lbl)
    scroll=ScrollView(do_scroll_x=False); self.items=BoxLayout(orientation='vertical',spacing=dp(7),size_hint_y=None,padding=dp(3)); self.items.bind(minimum_height=self.items.setter('height')); scroll.add_widget(self.items); root.add_widget(scroll)
    refresh=GlassButton(text='Обновить',height=dp(42)); refresh.bind(on_press=lambda *_: self.refresh()); root.add_widget(refresh)
    back=GlassButton(text='Назад',height=dp(42)); back.bind(on_press=lambda *_: self.manager.go_to('leaderboard')); root.add_widget(back)
    self.add_widget(root); self.refresh()
  def on_pre_enter(self, *args): self.refresh()
  def refresh(self):
    self.items.clear_widgets(); me=_session_user()
    if not me: return
    _ensure_social_tables(); c=_db()
    incoming=c.execute("SELECT sender FROM friend_requests WHERE receiver=? AND status='pending' ORDER BY created_at DESC",(me,)).fetchall()
    outgoing=c.execute("SELECT receiver FROM friend_requests WHERE sender=? AND status='pending' ORDER BY created_at DESC",(me,)).fetchall()
    friends=c.execute("SELECT user_a,user_b FROM friendships WHERE user_a=? OR user_b=?",(me,me)).fetchall(); c.close()
    duels=_open_duels_for(me); recent=_recent_duels_for(me)
    def add_line(title, actions=()):
      row=BoxLayout(orientation='horizontal',size_hint_y=None,height=dp(54),spacing=dp(6))
      lbl=Label(text=title,halign='left',valign='middle',size_hint_x=1); lbl.bind(size=lambda w,v:setattr(w,'text_size',(v[0],None))); row.add_widget(lbl)
      for text,fn in actions:
        b=GlassButton(text=text,height=dp(40),size_hint_x=None,width=dp(96)); b.font_size=dp(12); b.bind(on_press=lambda *_,f=fn: f()); row.add_widget(b)
      self.items.add_widget(row)
    def header(text): self.items.add_widget(Label(text=text,size_hint_y=None,height=dp(30),bold=True))
    def empty(text): self.items.add_widget(Label(text=text,size_hint_y=None,height=dp(28)))
    header('ВХОДЯЩИЕ ПРИГЛАШЕНИЯ')
    for (u,) in incoming: add_line(u,[('Принять',lambda u=u:self._accept(u))])
    if not incoming: empty('Нет новых приглашений')
    header('ВЫЗОВЫ НА ДУЭЛЬ')
    for duel_id,challenger,seed,score in duels:
      add_line(f"{challenger}: {score} раунд(ов)",[('Принять',lambda d=duel_id,ch=challenger,sd=seed,sc=score:self._accept_duel(d,ch,sd,sc))])
    if not duels: empty('Нет вызовов')
    header('МОИ ДРУЗЬЯ')
    for a,b in friends:
      other=b if a.lower()==me.lower() else a
      add_line(other,[('Профиль',lambda o=other:self._profile(o)),('Дуэль',lambda o=other:self._challenge(o))])
    if not friends: empty('Пока нет друзей')
    header('ОТПРАВЛЕННЫЕ ПРИГЛАШЕНИЯ')
    for (u,) in outgoing: add_line(u)
    if not outgoing: empty('Нет отправленных приглашений')
    header('РЕЗУЛЬТАТЫ ДУЭЛЕЙ')
    for ch,op,cs,os_ in recent:
      mine_is_ch = ch.lower()==me.lower(); my=cs if mine_is_ch else os_; their=os_ if mine_is_ch else cs; who=op if mine_is_ch else ch
      verdict='победа' if my>their else ('ничья' if my==their else 'поражение')
      add_line(f"С {who}: {my}:{their} — {verdict}")
    if not recent: empty('Дуэлей пока не было')
  def _accept(self, username): _accept_friend_request(username,_session_user()); self.refresh()
  def _profile(self, username): self.manager.get_screen('public_profile').show_player(username); self.manager.current='public_profile'
  def _challenge(self, username):
    me=_session_user()
    if _open_duel_exists(me, username):
      self.status_lbl.text=f'Ты уже вызвал {username} — жди ответа'; return
    scr=self.manager.get_screen('friend_duel'); scr.setup_challenge(username); self.manager.current='friend_duel'
  def _accept_duel(self, duel_id, challenger, seed, score):
    scr=self.manager.get_screen('friend_duel'); scr.setup_accept(duel_id, challenger, seed, score); self.manager.current='friend_duel'


class PromoScreen(Screen):
  """Вкладка профиля «Промокод»."""
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._reward_key = None
    self._build_ui()

  def _build_ui(self):
    self.clear_widgets()
    self._reward_key = None
    self.add_widget(make_game_background(None, "corners"))
    root = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(10), size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))
    root.add_widget(Label(text="ПРОМОКОД", font_size=dp(25), bold=True, size_hint_y=None,
                          height=dp(44), color=(1, .86, .36, 1)))
    hint = Label(text="Введи промокод и получи награду.\nКаждый промокод активируется один раз на аккаунт.",
                 font_size=dp(13), halign="center", valign="middle", size_hint_y=None, height=dp(48))
    hint.bind(size=lambda w, v: setattr(w, "text_size", (v[0], None)))
    root.add_widget(hint)
    self.input = GlassTextInput(hint_text="Введи промокод", multiline=False, size_hint_y=None,
                                height=dp(50), font_size=dp(17), write_tab=False)
    self.input.bind(on_text_validate=lambda *_: self._activate())
    root.add_widget(self.input)
    activate = GlassButton(text="Активировать", height=dp(52))
    activate.bind(on_press=lambda *_: self._activate())
    root.add_widget(activate)
    self.status = Label(text="", font_size=dp(14), halign="center", valign="middle",
                        size_hint_y=None, height=dp(56))
    self.status.bind(size=lambda w, v: setattr(w, "text_size", (v[0], None)))
    root.add_widget(self.status)
    self.reward_holder = FloatLayout(size_hint_y=None, height=dp(130))
    root.add_widget(self.reward_holder)
    self.equip_btn = GlassButton(text="Надеть аватарку", height=dp(0))
    self.equip_btn.opacity = 0
    self.equip_btn.disabled = True
    self.equip_btn.bind(on_press=lambda *_: self._equip())
    root.add_widget(self.equip_btn)
    back = GlassButton(text="Назад в профиль", height=dp(46))
    back.bind(on_press=lambda *_: self.manager.go_to("profile"))
    root.add_widget(back)
    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True, bar_width=dp(4))
    scroll.add_widget(root)
    self.add_widget(scroll)

  def _activate(self):
    ok, message, key = redeem_promo(self.input.text)
    self.status.text = message
    self.status.color = (.5, 1, .65, 1) if ok else (1, .5, .5, 1)
    if not ok:
      return
    self.input.text = ""
    self._reward_key = key
    self.reward_holder.clear_widgets()
    if key is None:  # награда без аватарки: монеты, кейс или рамка
      self.equip_btn.height = dp(0); self.equip_btn.opacity = 0; self.equip_btn.disabled = True
      return
    art = avatar_to_art(key, dp(110))
    art.size_hint = (None, None); art.size = (dp(110), dp(110))
    art.pos_hint = {"center_x": .5, "center_y": .5}
    self.reward_holder.add_widget(art)
    self.equip_btn.height = dp(48)
    self.equip_btn.opacity = 1
    self.equip_btn.disabled = False
    self.equip_btn.text = "Надеть аватарку"

  def _equip(self):
    if not self._reward_key:
      return
    data = load_data()
    data["avatar"] = self._reward_key
    save_data(data)
    self.equip_btn.text = "Аватарка надета!"
    self.equip_btn.disabled = True

  def on_pre_enter(self, *args):
    self._build_ui()


class JellyScreenManager(ScreenManager):
  """Keep the pressed screen alive briefly so button feedback can be seen."""
  _pending_navigation = None
  def go_to(self, screen_name, delay=0):
    # Immediate navigation: no artificial button delay.
    try:
      if self._pending_navigation is not None:
        self._pending_navigation.cancel()
      self._pending_navigation = None
      if self.has_screen(screen_name):
        self.current = screen_name
    except Exception:
      self.current = screen_name

  def _finish_go_to(self, screen_name):
    self._pending_navigation = None
    if self.has_screen(screen_name):
      self.current = screen_name

class GamesApp(App):
  def _flush_profile_sync(self):
    try:
      with _SYNC_LOCK: pending = _SYNC_STATE["args"] is not None
      if pending: _fire_profile_sync()
    except Exception: pass
  def on_pause(self):
    self._flush_profile_sync()
    return True
  def on_stop(self):
    self._flush_profile_sync()
  def build(self):
    root = FloatLayout()
    sm = JellyScreenManager()
    sm.transition = FadeTransition(duration=0)
    sm.size_hint = (1, 1); sm.pos_hint = {'x': 0, 'y': 0}
    sm.add_widget(AuthScreen(name='auth'))
    sm.add_widget(AdminGateScreen(name='admin_gate'))
    sm.add_widget(AdminPanelScreen(name='admin_panel'))
    sm.add_widget(LeaderboardScreen(name='leaderboard'))
    sm.add_widget(PublicProfileScreen(name='public_profile'))
    sm.add_widget(FriendsScreen(name='friends'))
    sm.add_widget(FriendDuelScreen(name='friend_duel'))
    sm.add_widget(AchievementsScreen(name='achievements'))
    sm.add_widget(MainMenuScreen(name='main'))
    sm.add_widget(MineScreen(name='mine'))
    sm.add_widget(PromoScreen(name='promo'))
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
    sm.add_widget(CasesInventoryScreen(name='cases_inventory'))
    sm.add_widget(NicknameScreen(name='nickname'))
    sm.add_widget(MemoryDuelScreen(name='ranked'))
    sm.add_widget(CasinoScreen(name='casino'))
    sm.add_widget(TreasureHuntScreen(name='treasure'))
    sm.add_widget(FunScreen(name='fun'))
    sm.add_widget(QuestsScreen(name='quests'))
    sm.add_widget(MarketScreen(name='market'))
    def _on_back_key(window, key, *args):
      # 27 = системная кнопка «Назад» (Android) или Esc (ПК).
      if key == 27:
        if sm.current in ('main', 'auth'):
          return False  # на главном экране - обычный выход
        sm.go_to('main')
        return True
      return False
    Window.bind(on_keyboard=_on_back_key)
    root.add_widget(sm)
    # Always require Supabase login; a leftover local session must never bypass online auth.
    sm.current = 'auth'
    return root


if __name__ == "__main__":
  try:
    GamesApp().run()
  except BaseException:
    _save_crash_log(*sys.exc_info())
    raise
