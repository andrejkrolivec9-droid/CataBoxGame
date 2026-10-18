import kivy
kivy.require('2.0.0')

import os
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse, Line
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition


BG_FILE = "bg.jpg"
HAS_BG = os.path.exists(BG_FILE)

if not HAS_BG:
    Window.clearcolor = (0.05, 0.05, 0.1, 1)
else:
    Window.clearcolor = (0, 0, 0, 1)


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
    except:
        pass


CAT_COLORS = {
    "gray":   ((0.75, 0.75, 0.8), (0.92, 0.92, 0.97), (0.7, 0.7, 0.75)),
    "orange": ((1, 0.65, 0.3),    (1, 0.85, 0.6),    (1, 0.65, 0.3)),
    "black":  ((0.18, 0.18, 0.22), (0.35, 0.35, 0.4), (0.18, 0.18, 0.22)),
    "gold":   ((1, 0.85, 0.2),    (1, 0.95, 0.6),    (1, 0.85, 0.2)),
}

CAT_NAMES = {
    "gray":   "Серый",
    "orange": "Рыжий",
    "black":  "Чёрный",
    "gold":   "ЗОЛОТОЙ",
}

CAT_PRICES = {
    "gray":   5,
    "orange": 15,
    "black":  50,
    "gold":   200,
}


class RootLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self.bg_color = Color(1, 1, 1, 1)
            if HAS_BG:
                self.bg = Rectangle(source=BG_FILE, pos=self.pos, size=self.size)
            else:
                self.bg = Rectangle(pos=self.pos, size=self.size)
                self.bg_color.rgba = (0.05, 0.05, 0.1, 1)
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


class GlassButton(Button):
    radius = NumericProperty(dp(25))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = dp(18)
        self.size_hint_y = None
        self.height = dp(60)

        with self.canvas.before:
            Color(1, 1, 1, 0.20)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size,
                                         radius=[self.radius])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.rect.radius = [self.radius]


class CatDraw:
    def __init__(self, canvas, size=dp(80), cat_type="orange"):
        self.canvas = canvas
        self.size = size
        self.cx = 0
        self.cy = 0
        self.cat_type = cat_type
        self.active = False

        body_c, belly_c, ear_c = CAT_COLORS[cat_type]

        with canvas:
            self.ear_color = Color(*ear_c, 0)
            self.ear_l = Line(points=[], width=dp(10), cap='round', joint='round', close=True)
            self.ear_r = Line(points=[], width=dp(10), cap='round', joint='round', close=True)

            self.ear_inner_color = Color(*belly_c, 0)
            self.ear_inner_l = Line(points=[], width=dp(5), cap='round', joint='round', close=True)
            self.ear_inner_r = Line(points=[], width=dp(5), cap='round', joint='round', close=True)

            self.body_color = Color(*body_c, 0)
            self.body = Ellipse()

            self.belly_color = Color(*belly_c, 0)
            self.belly = Ellipse()

            self.paw_color = Color(*belly_c, 0)
            self.paw_l = Ellipse()
            self.paw_r = Ellipse()

            self.head_color = Color(*body_c, 0)
            self.head = Ellipse()

            self.face_color = Color(*belly_c, 0)
            self.face = Ellipse()

            self.eye_color = Color(0.1, 0.1, 0.1, 0)
            self.eye_l = Ellipse()
            self.eye_r = Ellipse()

            self.nose_color = Color(1, 0.4, 0.5, 0)
            self.nose = Ellipse()

    def set_position(self, cx, cy, clip_x_min=-99999, clip_x_max=99999):
        self.cx = cx
        self.cy = cy
        half = self.size * 0.5
        visible = (cx + half > clip_x_min) and (cx - half < clip_x_max)
        if visible:
            if not self.active:
                self.activate()
            self.redraw()
        else:
            if self.active:
                self.deactivate()

    def activate(self):
        self.active = True
        for c in [self.ear_color, self.ear_inner_color, self.body_color,
                  self.belly_color, self.paw_color, self.head_color,
                  self.face_color, self.eye_color, self.nose_color]:
            c.a = 1

    def deactivate(self):
        self.active = False
        for c in [self.ear_color, self.ear_inner_color, self.body_color,
                  self.belly_color, self.paw_color, self.head_color,
                  self.face_color, self.eye_color, self.nose_color]:
            c.a = 0
        self.ear_l.points = []
        self.ear_r.points = []
        self.ear_inner_l.points = []
        self.ear_inner_r.points = []
        self.body.pos = (-100, -100); self.body.size = (0, 0)
        self.belly.pos = (-100, -100); self.belly.size = (0, 0)
        self.paw_l.pos = (-100, -100); self.paw_l.size = (0, 0)
        self.paw_r.pos = (-100, -100); self.paw_r.size = (0, 0)
        self.head.pos = (-100, -100); self.head.size = (0, 0)
        self.face.pos = (-100, -100); self.face.size = (0, 0)
        self.eye_l.pos = (-100, -100); self.eye_l.size = (0, 0)
        self.eye_r.pos = (-100, -100); self.eye_r.size = (0, 0)
        self.nose.pos = (-100, -100); self.nose.size = (0, 0)

    def destroy(self):
        self.deactivate()

    def redraw(self):
        s = self.size
        cx, cy = self.cx, self.cy
        body_w = s * 0.85
        body_h = s * 0.7
        body_x = cx - body_w / 2
        body_y = cy - s * 0.55
        self.body.pos = (body_x, body_y)
        self.body.size = (body_w, body_h)

        belly_w = body_w * 0.55
        belly_h = body_h * 0.7
        self.belly.pos = (cx - belly_w / 2, body_y + body_h * 0.08)
        self.belly.size = (belly_w, belly_h)

        paw_w = body_w * 0.22
        paw_h = body_h * 0.18
        self.paw_l.pos = (cx - body_w * 0.32, body_y - paw_h * 0.3)
        self.paw_l.size = (paw_w, paw_h)
        self.paw_r.pos = (cx + body_w * 0.1, body_y - paw_h * 0.3)
        self.paw_r.size = (paw_w, paw_h)

        head_size = s * 0.6
        head_x = cx - head_size / 2
        head_y = cy - s * 0.1
        self.head.pos = (head_x, head_y)
        self.head.size = (head_size, head_size)

        ear_h = head_size * 0.35

        l_ear_x1 = head_x + head_size * 0.12
        l_ear_y1 = head_y + head_size * 0.7
        l_ear_x2 = head_x + head_size * 0.05
        l_ear_y2 = head_y + head_size * 0.7 + ear_h
        l_ear_x3 = head_x + head_size * 0.45
        l_ear_y3 = head_y + head_size * 0.75
        self.ear_l.points = [l_ear_x1, l_ear_y1, l_ear_x2, l_ear_y2, l_ear_x3, l_ear_y3]

        r_ear_x1 = head_x + head_size * 0.55
        r_ear_y1 = head_y + head_size * 0.75
        r_ear_x2 = head_x + head_size * 0.95
        r_ear_y2 = head_y + head_size * 0.7 + ear_h
        r_ear_x3 = head_x + head_size * 0.88
        r_ear_y3 = head_y + head_size * 0.7
        self.ear_r.points = [r_ear_x1, r_ear_y1, r_ear_x2, r_ear_y2, r_ear_x3, r_ear_y3]

        l_inner_x1 = l_ear_x1 + head_size * 0.05
        l_inner_y1 = l_ear_y1 + head_size * 0.04
        l_inner_x2 = l_ear_x2 + head_size * 0.06
        l_inner_y2 = l_ear_y2 - head_size * 0.06
        l_inner_x3 = l_ear_x3 - head_size * 0.05
        l_inner_y3 = l_ear_y3 + head_size * 0.04
        self.ear_inner_l.points = [l_inner_x1, l_inner_y1, l_inner_x2, l_inner_y2, l_inner_x3, l_inner_y3]

        r_inner_x1 = r_ear_x1 + head_size * 0.05
        r_inner_y1 = r_ear_y1 + head_size * 0.04
        r_inner_x2 = r_ear_x2 - head_size * 0.06
        r_inner_y2 = r_ear_y2 - head_size * 0.06
        r_inner_x3 = r_ear_x3 - head_size * 0.05
        r_inner_y3 = r_ear_y3 + head_size * 0.04
        self.ear_inner_r.points = [r_inner_x1, r_inner_y1, r_inner_x2, r_inner_y2, r_inner_x3, r_inner_y3]

        face_w = head_size * 0.55
        face_h = head_size * 0.4
        self.face.pos = (head_x + head_size * 0.225, head_y + head_size * 0.1)
        self.face.size = (face_w, face_h)

        eye_w = head_size * 0.13
        eye_h = head_size * 0.15

        self.eye_l.pos = (head_x + head_size * 0.32 - eye_w/2, head_y + head_size * 0.55)
        self.eye_l.size = (eye_w, eye_h)
        self.eye_r.pos = (head_x + head_size * 0.68 - eye_w/2, head_y + head_size * 0.55)
        self.eye_r.size = (eye_w, eye_h)

        nose_w = head_size * 0.08
        nose_h = head_size * 0.06
        self.nose.pos = (head_x + head_size * 0.46, head_y + head_size * 0.32)
        self.nose.size = (nose_w, nose_h)


class CatArt(FloatLayout):
    """Кот рисуется на своём canvas. Центр задаётся ВРУЧНУЮ."""
    def __init__(self, cat_type="orange", size_cat=dp(70), **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (size_cat, size_cat)
        self.cat_type = cat_type
        self._draw = None
        self._center_x = 0
        self._center_y = 0

        Clock.schedule_once(self._init_draw, 0.05)

    def _init_draw(self, dt):
        if self.width < 5:
            Clock.schedule_once(self._init_draw, 0.1)
            return
        self._draw = CatDraw(self.canvas, self.width, self.cat_type)
        self._draw.activate()
        self._redraw_now()

    def set_center(self, cx, cy):
        """Устанавливает центр кота в АБСОЛЮТНЫХ координатах."""
        self._center_x = cx
        self._center_y = cy
        self._redraw_now()

    def _redraw_now(self):
        if self._draw:
            self._draw.set_position(self._center_x, self._center_y)


class DollarWidget(FloatLayout):
    def __init__(self, size_d=dp(240), **kwargs):
        super().__init__(**kwargs)
        self.base_size = size_d
        self.size_hint = (None, None)
        self.size = (size_d, size_d)
        self._event = None
        self.jumping = False

        with self.canvas:
            self.rim_color = Color(0.75, 0.55, 0.05, 1)
            self.rim = Ellipse()
            self.circle_color = Color(1, 0.85, 0.2, 1)
            self.circle = Ellipse()
            self.inner_color = Color(1, 0.93, 0.55, 1)
            self.inner = Ellipse()
            self.sym_color = Color(0.3, 0.2, 0.0, 1)
            self.sym_v = Line(points=[], width=dp(12), cap='round')
            self.sym_top = Line(points=[], width=dp(10), cap='round')
            self.sym_bot = Line(points=[], width=dp(10), cap='round')
            self.sym_s_top = Line(points=[], width=dp(10), cap='round')
            self.sym_s_bot = Line(points=[], width=dp(10), cap='round')

        self.bind(pos=self.redraw, size=self.redraw)
        self.redraw()

    def redraw(self, *args):
        s = self.width
        if s < 5:
            return
        cx = self.x + s / 2
        cy = self.y + s / 2

        self.rim.pos = (cx - s/2, cy - s/2)
        self.rim.size = (s, s)

        circle_s = s * 0.9
        self.circle.pos = (cx - circle_s/2, cy - circle_s/2)
        self.circle.size = (circle_s, circle_s)

        inner_s = s * 0.72
        self.inner.pos = (cx - inner_s/2, cy - inner_s/2)
        self.inner.size = (inner_s, inner_s)

        vh = s * 0.44
        hw = s * 0.14
        s_h = s * 0.1

        top = cy + vh / 2
        bot = cy - vh / 2

        self.sym_v.points = [cx, bot, cx, top]
        self.sym_top.points = [cx - hw, top, cx + hw, top]
        self.sym_bot.points = [cx - hw, bot, cx + hw, bot]
        self.sym_s_top.points = [cx + hw, top, cx + hw, top - s_h]
        self.sym_s_bot.points = [cx - hw, bot, cx - hw, bot + s_h]

    def pulse(self):
        if self.jumping:
            return
        self.jumping = True
        self._step = 0
        self._total = 30
        self._event = Clock.schedule_interval(self._tick, 0.02)

    def _tick(self, dt):
        self._step += 1

        if self._step <= 8:
            p = self._step / 8.0
            scale = 1.0 + 0.12 * p
        elif self._step <= 18:
            p = (self._step - 8) / 10.0
            scale = 1.12 - 0.12 * p * p
        elif self._step <= 23:
            p = (self._step - 18) / 5.0
            scale = 1.0 - 0.04 * p
        else:
            p = (self._step - 23) / 7.0
            scale = 0.96 + 0.04 * p

        new_size = self.base_size * scale
        self.size = (new_size, new_size)
        if self.parent:
            self.center_x = self.parent.center_x
            self.center_y = self.parent.center_y

        if self._step >= self._total:
            self.size = (self.base_size, self.base_size)
            self._event.cancel()
            self._event = None
            self.jumping = False


class ClickerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        data = load_data()
        self.coins = data.get("coins", 0)
        self.dollar = None

        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        self.coins_label = Label(text=f"Монеты: {self.coins}", font_size=dp(30),
                                 size_hint_y=None, height=dp(50))
        layout.add_widget(self.coins_label)

        layout.add_widget(Label(text="Тапай по доллару!", font_size=dp(16),
                                size_hint_y=None, height=dp(30)))

        self.dollar_holder = FloatLayout(size_hint_y=None, height=dp(340))
        layout.add_widget(self.dollar_holder)

        btn_box = GlassButton(text="Открыть кейс")
        btn_box.bind(on_press=lambda x: setattr(self.manager, 'current', 'box'))
        layout.add_widget(btn_box)

        btn_inv = GlassButton(text="Инвентарь")
        btn_inv.bind(on_press=lambda x: setattr(self.manager, 'current', 'inventory'))
        layout.add_widget(btn_inv)

        self.add_widget(layout)

        self.dollar_holder.bind(size=self._on_holder_resize)

    def _on_holder_resize(self, *args):
        if self.dollar is not None:
            return
        if self.dollar_holder.width < 10 or self.dollar_holder.height < 10:
            return
        self._create_dollar(0)

    def _create_dollar(self, dt):
        try:
            self.dollar = DollarWidget(dp(240))
            self.dollar.size_hint = (None, None)
            self.dollar.size = (dp(240), dp(240))

            def center(*a):
                self.dollar.center_x = self.dollar_holder.center_x
                self.dollar.center_y = self.dollar_holder.center_y

            self.dollar_holder.bind(pos=center, size=center)
            center()
            self.dollar.bind(on_touch_down=self._on_tap)
            self.dollar_holder.add_widget(self.dollar)
        except Exception as e:
            print("ОШИБКА доллара:", e)

    def _on_tap(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.coins += 1
            self.coins_label.text = f"Монеты: {self.coins}"
            if self.dollar:
                self.dollar.pulse()
            data = load_data()
            data["coins"] = self.coins
            save_data(data)
            return True
        return False

    def update_coins(self):
        data = load_data()
        self.coins = data.get("coins", 0)
        self.coins_label.text = f"Монеты: {self.coins}"

    def on_pre_enter(self, *args):
        self.update_coins()


class RouletteWidget(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cats = []
        self._event = None
        self.spinning = False

        with self.canvas.before:
            Color(1, 1, 1, 0.05)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[dp(20)])

        with self.canvas.after:
            self.line_color = Color(0.75, 0.75, 0.8, 0.7)
            self.line = Line(points=[], width=dp(4), cap='round')

        self.bind(pos=self._update_graphics, size=self._update_graphics)
        Clock.schedule_once(lambda dt: self._update_graphics(), 0.1)

    def _update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        cx = self.x + self.width / 2
        self.line.points = [cx, self.y + dp(10), cx, self.y + self.height - dp(10)]
        if self.cats:
            self._redraw_all()

    def start_spin(self, sequence, on_finish):
        if self.spinning:
            return
        self.spinning = True
        self._on_finish = on_finish

        if self.width < 10:
            Clock.schedule_once(lambda dt: self.start_spin(sequence, on_finish), 0.1)
            return

        self.clear_all()
        cat_size = dp(80)
        spacing = dp(105)

        display_sequence = sequence + [
            random.choice(["gray", "orange", "black", "gold"]) for _ in range(5)
        ]

        final_i = len(sequence) - 1

        for i, cat_type in enumerate(display_sequence):
            cat = CatDraw(self.canvas, cat_size, cat_type)
            self.cats.append(cat)

        self._cat_size = cat_size
        self._spacing = spacing
        self._start_x = self.x + self.width
        self._final_i = final_i

        final_center_x = self.x + self.width / 2
        final_start_x = self._start_x + final_i * spacing
        self._end_offset = final_center_x - final_start_x

        self._offset = 0
        self._redraw_all()

        self._step = 0
        self._total = 80
        self._event = Clock.schedule_interval(self._tick, 0.015)

    def _redraw_all(self):
        base_y = self.y + self.height / 2
        clip_x_min = self.x
        clip_x_max = self.x + self.width
        for i, cat in enumerate(self.cats):
            base_x = self._start_x + i * self._spacing + self._offset
            cat.set_position(base_x, base_y, clip_x_min, clip_x_max)

    def _tick(self, dt):
        self._step += 1
        progress = self._step / self._total
        ease = 1 - (1 - progress) ** 3
        self._offset = self._end_offset * ease

        self._redraw_all()

        if self._step >= self._total:
            self._event.cancel()
            self._event = None
            self.spinning = False
            if self._on_finish:
                self._on_finish()

    def clear_all(self):
        for cat in self.cats:
            cat.destroy()
        self.cats = []


class BoxScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.spinning = False
        self.popup = None

        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(6))

        layout.add_widget(Label(text="Кейс удачи", font_size=dp(24),
                                size_hint_y=None, height=dp(40)))

        self.coins_label = Label(text="", font_size=dp(18),
                                 size_hint_y=None, height=dp(30))
        layout.add_widget(self.coins_label)

        self.roulette = RouletteWidget(size_hint_y=None, height=dp(170))
        layout.add_widget(self.roulette)

        self.result_label = Label(
            text="Крути!",
            font_size=dp(15),
            size_hint_y=None, height=dp(40),
            halign='center', valign='middle'
        )
        self.result_label.bind(size=lambda s, v: setattr(s, 'text_size', (v[0], None)))
        layout.add_widget(self.result_label)

        btn1 = GlassButton(text="1 прокрут — 100 монет", height=dp(50))
        btn1.bind(on_press=lambda x: self.spin(1, 100))
        layout.add_widget(btn1)

        btn5 = GlassButton(text="5 прокрутов — 500 монет", height=dp(50))
        btn5.bind(on_press=lambda x: self.spin(5, 500))
        layout.add_widget(btn5)

        btn10 = GlassButton(text="10 прокрутов — 1000 монет", height=dp(50))
        btn10.bind(on_press=lambda x: self.spin(10, 1000))
        layout.add_widget(btn10)

        btn_back = GlassButton(text="Назад", height=dp(50))
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'clicker'))
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def on_pre_enter(self, *args):
        data = load_data()
        self.coins = data.get("coins", 0)
        self.coins_label.text = f"Монеты: {self.coins}"
        self.roulette.clear_all()
        self.result_label.text = "Крути!"
        self.spinning = False

        if self.popup:
            self.remove_widget(self.popup)
            self.popup = None

    def spin(self, count, cost):
        if self.spinning:
            return

        data = load_data()
        coins = data.get("coins", 0)
        if coins < cost:
            self.result_label.text = f"Не хватает! Нужно {cost}, есть {coins}"
            return

        coins -= cost
        data["coins"] = coins
        save_data(data)
        self.coins_label.text = f"Монеты: {coins}"

        self.spinning = True
        results = []
        for _ in range(count):
            r = random.choices(
                ["gray", "orange", "black", "gold"],
                weights=[50, 30, 15, 5]
            )[0]
            results.append(r)

        data = load_data()
        inventory = data.get("inventory", [])
        for r in results:
            inventory.append(r)
        data["inventory"] = inventory

        gold_count = results.count("gold")
        if gold_count > 0:
            data["coins"] = data.get("coins", 0) + 500 * gold_count
        save_data(data)
        self.coins_label.text = f"Монеты: {data['coins']}"

        if count == 1:
            self.result_label.text = "Крутим..."
            self._final_cat = results[0]
            seq = [random.choice(["gray", "orange", "black", "gold"])
                   for _ in range(12)]
            seq.append(self._final_cat)

            def on_finish():
                self.result_label.text = f"Выпал: {CAT_NAMES[self._final_cat]}"
                self.spinning = False

            self.roulette.start_spin(seq, on_finish)
        else:
            self._show_popup(results)

    def _show_popup(self, results):
        if self.popup:
            self.remove_widget(self.popup)
        popup = PopupResult(results, on_close=self._close_popup)
        self.add_widget(popup)
        self.popup = popup

    def _close_popup(self):
        if self.popup:
            self.remove_widget(self.popup)
            self.popup = None
        self.spinning = False
        self.result_label.text = "Готово!"


class PopupResult(FloatLayout):
    def __init__(self, results, on_close, **kwargs):
        super().__init__(**kwargs)
        self.on_close = on_close

        with self.canvas.before:
            self.dim_color = Color(0, 0, 0, 0.85)
            self.dim = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_dim, size=self._update_dim)

        panel_w = min(Window.width * 0.9, dp(400))
        panel_h = dp(420)

        with self.canvas:
            Color(0.15, 0.15, 0.2, 0.98)
            self.panel = RoundedRectangle(
                pos=(Window.width / 2 - panel_w / 2,
                     Window.height / 2 - panel_h / 2),
                size=(panel_w, panel_h),
                radius=[dp(30)]
            )

        title = Label(
            text=f"Ты получил {len(results)} котов:",
            font_size=dp(20),
            size_hint=(None, None),
            size=(panel_w, dp(40)),
            pos=(Window.width / 2 - panel_w / 2,
                 Window.height / 2 + panel_h / 2 - dp(50)),
            color=(1, 1, 1, 1)
        )
        self.add_widget(title)

        close_btn = GlassButton(text="Забрать")
        close_btn.size_hint = (None, None)
        close_btn.size = (panel_w - dp(60), dp(60))
        close_btn.pos = (Window.width / 2 - (panel_w - dp(60)) / 2,
                         Window.height / 2 - panel_h / 2 + dp(20))
        close_btn.bind(on_press=self._close)
        self.add_widget(close_btn)

        Clock.schedule_once(lambda dt: self._place_cats(results, panel_w, panel_h), 0.05)

    def _place_cats(self, results, panel_w, panel_h):
        cols = 5
        cat_size = dp(50)
        pad = dp(8)

        grid_w = cols * cat_size + (cols - 1) * pad
        rows = (len(results) + cols - 1) // cols
        grid_h = rows * cat_size + (rows - 1) * pad

        start_x = Window.width / 2 - grid_w / 2
        start_y = Window.height / 2 + panel_h / 2 - dp(100) - grid_h

        for i, cat_type in enumerate(results):
            col = i % cols
            row = i // cols
            cx = start_x + col * (cat_size + pad)
            cy = start_y + grid_h - row * (cat_size + pad) - cat_size

            cat = CatArt(cat_type, cat_size)
            cat.size = (cat_size, cat_size)
            cat.pos = (cx, cy)
            self.add_widget(cat)

    def _update_dim(self, *args):
        self.dim.pos = self.pos
        self.dim.size = self.size

    def _close(self, *args):
        if self.on_close:
            self.on_close()


class InventoryCard(BoxLayout):
    """Карточка кота. Кот центрируется по АБСОЛЮТНЫМ координатам."""
    def __init__(self, cat_type="gray", on_sell=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = dp(8)
        self.spacing = dp(4)
        self.cat_type = cat_type
        self.on_sell = on_sell

        with self.canvas.before:
            Color(1, 1, 1, 0.08)
            self.card_bg = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(15)]
            )
            Color(1, 1, 1, 0.25)
            self.card_border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(15)),
                width=dp(1.5)
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Слот кота — он же «якорь». Кот привязывается к центру слота.
        self.cat_holder = FloatLayout(size_hint_y=None, height=dp(120))
        self.cat = CatArt(cat_type, dp(100))
        self.cat.size_hint = (None, None)
        self.cat.size = (dp(100), dp(100))

        self.cat_holder.add_widget(self.cat)
        self.add_widget(self.cat_holder)

        # При изменении размеров/позиции холдера — центрируем кота
        self.cat_holder.bind(pos=self._center_cat, size=self._center_cat)
        Clock.schedule_once(lambda dt: self._center_cat(), 0.1)

        # Подпись
        price = CAT_PRICES[cat_type]
        label = Label(
            text=f"{CAT_NAMES[cat_type]} ({price}м)",
            font_size=dp(12),
            size_hint_y=None,
            height=dp(20),
            color=(1, 1, 1, 1)
        )
        self.add_widget(label)

        # Кнопка «Продать»
        sell_btn = GlassButton(text="Продать", height=dp(40))
        sell_btn.font_size = dp(14)
        if on_sell:
            sell_btn.bind(on_press=lambda x: on_sell(cat_type))
        self.add_widget(sell_btn)

    def _center_cat(self, *args):
        """Центрируем кота в холдере через АБСОЛЮТНЫЕ координаты."""
        if self.cat and self.cat_holder:
            cx = self.cat_holder.center_x
            cy = self.cat_holder.center_y
            self.cat.set_center(cx, cy)

    def _update_bg(self, *args):
        self.card_bg.pos = self.pos
        self.card_bg.size = self.size
        self.card_border.rounded_rectangle = (
            self.x, self.y, self.width, self.height, dp(15)
        )


class InventoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))

        root_layout.add_widget(Label(text="Инвентарь", font_size=dp(26),
                                      size_hint_y=None, height=dp(40)))

        self.count_label = Label(text="", font_size=dp(14),
                                  size_hint_y=None, height=dp(30))
        root_layout.add_widget(self.count_label)

        self.sell_all_btn = GlassButton(text="Продать всех", height=dp(50))
        self.sell_all_btn.bind(on_press=self.sell_all)
        root_layout.add_widget(self.sell_all_btn)

        scroll = ScrollView(size_hint=(1, 1))
        self.grid = GridLayout(cols=2, spacing=dp(12), padding=dp(10),
                                size_hint_y=None, row_default_height=dp(210),
                                row_force_default=True)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        root_layout.add_widget(scroll)

        btn_back = GlassButton(text="Назад", height=dp(55))
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'clicker'))
        root_layout.add_widget(btn_back)

        self.add_widget(root_layout)

    def on_pre_enter(self, *args):
        Clock.schedule_once(lambda dt: self.refresh(), 0.1)

    def refresh(self):
        self.grid.clear_widgets()

        data = load_data()
        inventory = data.get("inventory", [])
        self.count_label.text = f"Всего котов: {len(inventory)}"

        order = {"gold": 0, "black": 1, "orange": 2, "gray": 3}
        sorted_cats = sorted(inventory, key=lambda c: order.get(c, 99))

        for cat_type in sorted_cats:
            card = InventoryCard(cat_type, on_sell=self.sell_one)
            self.grid.add_widget(card)

    def sell_one(self, cat_type):
        data = load_data()
        inventory = data.get("inventory", [])
        if cat_type in inventory:
            inventory.remove(cat_type)
            data["inventory"] = inventory
            price = CAT_PRICES[cat_type]
            data["coins"] = data.get("coins", 0) + price
            save_data(data)
            self.refresh()

    def sell_all(self, *args):
        data = load_data()
        inventory = data.get("inventory", [])
        total = 0
        for cat in inventory:
            total += CAT_PRICES.get(cat, 0)
        data["inventory"] = []
        data["coins"] = data.get("coins", 0) + total
        save_data(data)
        self.refresh()


class GamesApp(App):
    def build(self):
        root = RootLayout()

        sm = ScreenManager()
        sm.transition = FadeTransition(duration=0.3)
        sm.size_hint = (1, 1)
        sm.pos_hint = {'x': 0, 'y': 0}

        sm.add_widget(ClickerScreen(name='clicker'))
        sm.add_widget(BoxScreen(name='box'))
        sm.add_widget(InventoryScreen(name='inventory'))

        root.add_widget(sm)
        return root


if __name__ == "__main__":
    GamesApp().run()
