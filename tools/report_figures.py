"""Diagram primitives and all figures of the lab 2 report (reportlab vector graphics)."""
import math
from reportlab.graphics.shapes import Drawing, Rect, PolyLine, Polygon, String, Circle, Line
from reportlab.lib import colors

BLACK = colors.black
WHITE = colors.white
MEM = colors.Color(0.85, 0.85, 0.85)
LIGHT = colors.Color(0.93, 0.93, 0.93)
SANS, SANSB = "Sans", "Sans-Bold"
LW = 0.7


class Fig:
    def __init__(self, w, h):
        self.d = Drawing(w, h)
        self.H = h
        self.W = w

    def Y(self, y):
        return self.H - y

    def text(self, x, y, s, size=7.5, anchor="middle", font=SANS, color=BLACK):
        self.d.add(String(x, self.Y(y) - size * 0.35, s, fontName=font, fontSize=size,
                          textAnchor=anchor, fillColor=color))

    def lines(self, x, y, items, size=7.5, anchor="middle", bold_first=False):
        lh = size * 1.3
        y0 = y - (len(items) - 1) * lh / 2
        for i, s in enumerate(items):
            self.text(x, y0 + i * lh, s, size, anchor, SANSB if bold_first and i == 0 else SANS)

    def rect(self, x, y, w, h, fill=WHITE, dashed=False, rx=0, lw=LW):
        self.d.add(Rect(x, self.Y(y + h), w, h, rx=rx, ry=rx, fillColor=fill, strokeColor=BLACK,
                        strokeWidth=lw, strokeDashArray=[3, 2] if dashed else None))

    def box(self, x, y, w, h, items, mem=False, size=7.5, bold_first=True, fill=None, dashed=False, rx=0):
        self.rect(x, y, w, h, fill if fill is not None else (MEM if mem else WHITE), dashed, rx)
        self.lines(x + w / 2, y + h / 2, items, size, bold_first=bold_first)

    def poly(self, pts, fill=WHITE, dashed=False):
        flat = []
        for x, y in pts:
            flat += [x, self.Y(y)]
        self.d.add(Polygon(flat, fillColor=fill, strokeColor=BLACK, strokeWidth=LW,
                           strokeDashArray=[3, 2] if dashed else None))

    def trap(self, x, y, w, h, items, size=7.5):
        """Arithmetic unit: inputs on the wide top side, output on the narrow bottom side."""
        k = w * 0.18
        self.poly([(x, y), (x + w, y), (x + w - k, y + h), (x + k, y + h)])
        self.lines(x + w / 2, y + h / 2, items, size, bold_first=True)

    def trap_lr(self, x, y, w, h, items, size=7.5):
        """Arithmetic unit drawn left to right: inputs on the wide left side."""
        k = h * 0.18
        self.poly([(x, y), (x + w, y + k), (x + w, y + h - k), (x, y + h)])
        self.lines(x + w / 2, y + h / 2, items, size, bold_first=True)

    def mux(self, x, y, w, h, labels):
        k = h * 0.2
        self.poly([(x, y), (x + w, y + k), (x + w, y + h - k), (x, y + h)])
        n = len(labels)
        for i, s in enumerate(labels):
            self.text(x + 5, y + h * (i + 1) / (n + 1), s, 6.5, "start")

    def head(self, p_from, p_to, size=4.2):
        (x1, y1), (x2, y2) = p_from, p_to
        a = math.atan2(-(y2 - y1), x2 - x1)
        X, Y = x2, self.Y(y2)
        pts = [X, Y,
               X - size * math.cos(a) + size * 0.45 * math.sin(a), Y - size * math.sin(a) - size * 0.45 * math.cos(a),
               X - size * math.cos(a) - size * 0.45 * math.sin(a), Y - size * math.sin(a) + size * 0.45 * math.cos(a)]
        self.d.add(Polygon(pts, fillColor=BLACK, strokeColor=BLACK, strokeWidth=0.3))

    def wire(self, pts, dashed=False, end=True, start=False, bits=None, bits_seg=0, bits_t=0.5, bits_side=1):
        flat = []
        for x, y in pts:
            flat += [x, self.Y(y)]
        self.d.add(PolyLine(flat, strokeColor=BLACK, strokeWidth=LW, strokeDashArray=[3, 2] if dashed else None))
        if end:
            self.head(pts[-2], pts[-1])
        if start:
            self.head(pts[1], pts[0])
        if bits is not None:
            (x1, y1), (x2, y2) = pts[bits_seg], pts[bits_seg + 1]
            mx, my = x1 + (x2 - x1) * bits_t, y1 + (y2 - y1) * bits_t
            self.d.add(Line(mx - 3, self.Y(my + 3), mx + 3, self.Y(my - 3), strokeColor=BLACK, strokeWidth=LW))
            if abs(x2 - x1) < 1e-6:
                self.text(mx + 5 * bits_side, my, str(bits), 6.5, "start" if bits_side > 0 else "end")
            else:
                self.text(mx + 5, my - 6, str(bits), 6.5, "start")

    def dot(self, x, y, r=1.6):
        self.d.add(Circle(x, self.Y(y), r, fillColor=BLACK, strokeColor=BLACK, strokeWidth=0.3))

    # flowchart symbols
    def term(self, cx, y, w, h, items):
        self.rect(cx - w / 2, y, w, h, rx=h / 2)
        self.lines(cx, y + h / 2, items, 7.5)

    def proc(self, cx, y, w, h, items):
        self.rect(cx - w / 2, y, w, h)
        self.lines(cx, y + h / 2, items, 7.5)

    def io(self, cx, y, w, h, items):
        k = 8
        self.poly([(cx - w / 2 + k, y), (cx + w / 2 + k, y), (cx + w / 2 - k, y + h), (cx - w / 2 - k, y + h)])
        self.lines(cx, y + h / 2, items, 7.5)

    def decision(self, cx, y, w, h, items):
        self.poly([(cx, y), (cx + w / 2, y + h / 2), (cx, y + h), (cx - w / 2, y + h / 2)])
        self.lines(cx, y + h / 2, items, 7.5)


# ---------------------------------------------------------------- figures

def fig_legend():
    f = Fig(470, 244)
    rows = [
        ("block", "Функциональный блок: логика управления, вычисления или передачи данных"),
        ("mem", "Память: хранит данные (SRAM, ROM, регистровый файл, регистры состояния)"),
        ("trap", "Арифметический узел: операнды входят с широкой стороны, результат выходит с узкой"),
        ("mux", "Мультиплексор: пропускает на выход один из входов по сигналу выбора"),
        ("data", "Линия данных; число у косой черты: ширина в битах"),
        ("ctrl", "Линия управления: сигнал, который запускает, останавливает или выбирает"),
        ("frame", "Граница устройства (кристалл, PE); имя устройства в углу рамки"),
        ("dot", "Точка: линии соединены; пересечение без точки означает, что соединения нет"),
    ]
    y = 6
    for kind, s in rows:
        cy = y + 11
        if kind == "block":
            f.box(10, y + 2, 60, 18, ["Блок"], bold_first=False)
        elif kind == "mem":
            f.box(10, y + 2, 60, 18, ["Память"], mem=True, bold_first=False)
        elif kind == "trap":
            f.trap(18, y + 1, 44, 20, ["FMA"])
        elif kind == "mux":
            f.mux(30, y, 18, 20, ["0", "1"])
            f.wire([(18, y + 6), (30, y + 6)])
            f.wire([(18, y + 14), (30, y + 14)])
            f.wire([(48, cy - 1), (60, cy - 1)])
            f.wire([(39, y + 26), (39, y + 18)], dashed=True)
        elif kind == "data":
            f.wire([(8, cy), (72, cy)], bits=64)
        elif kind == "ctrl":
            f.wire([(8, cy), (72, cy)], dashed=True)
        elif kind == "frame":
            f.rect(10, y + 1, 60, 20, dashed=True)
            f.text(13, y + 7, "PE0", 6.5, "start")
        elif kind == "dot":
            f.wire([(8, cy), (72, cy)], end=False)
            f.wire([(40, cy), (40, y + 22)], end=False)
            f.dot(40, cy)
        f.text(90, cy, s, 7.5, "start")
        y += 36 if kind == "mux" else 28
    return f.d


def fig_network():
    f = Fig(470, 200)
    bw, bh = 86, 34
    xs = [0, 124, 248, 372]
    # row 1
    f.box(xs[0], 50, bw, bh, ["x", "49 чисел"], mem=True)
    f.box(xs[1], 50, bw, bh, ["Σ W¹·x", "8 сумм по 49"])
    f.box(xs[2], 50, bw, bh, ["σ", "8 раз"])
    f.box(xs[3], 50, bw, bh, ["h", "8 чисел"], mem=True)
    f.box(xs[1], 0, bw, 30, ["W¹", "8 × 49 весов"], mem=True)
    f.wire([(xs[1] + bw / 2, 30), (xs[1] + bw / 2, 50)])
    for a, b in ((0, 1), (1, 2), (2, 3)):
        f.wire([(xs[a] + bw, 67), (xs[b], 67)])
    # row 2
    f.box(xs[0], 150, bw, bh, ["Σ W²·h", "3 суммы по 8"])
    f.box(xs[1], 150, bw, bh, ["σ", "3 раза"])
    f.box(xs[2], 150, bw, bh, ["y", "3 числа"], mem=True)
    f.box(xs[3], 150, bw, bh, ["Выбор класса", "max и порог 0.5"])
    f.box(xs[0], 100, bw, 30, ["W²", "3 × 8 весов"], mem=True)
    f.wire([(xs[0] + bw / 2, 130), (xs[0] + bw / 2, 150)])
    f.wire([(xs[3] + bw / 2, 84), (xs[3] + bw / 2, 92), (xs[0] + bw + 18, 92), (xs[0] + bw + 18, 167), (xs[0] + bw, 167)])
    for a, b in ((0, 1), (1, 2), (2, 3)):
        f.wire([(xs[a] + bw, 167), (xs[b], 167)]) if a > 0 else None
    f.wire([(xs[0] + bw + 18, 167), (xs[1], 167)], end=True) if False else None
    f.text(xs[3] + bw / 2, 194, "класс: 0, 1, 2 или 3 (шум)", 7)
    f.wire([(xs[3] + bw / 2, 184), (xs[3] + bw / 2, 190)], end=False)
    return f.d


def fig_network_v2():
    f = Fig(470, 226)
    bw, bh = 82, 34
    xs = [0, 128, 256, 384]
    r1, r2 = 50, 160
    f.text(0, 8, "Скрытый слой", 7.5, "start", SANSB)
    f.box(xs[1], 0, bw, 30, ["W¹", "8 × 49 весов"], mem=True)
    f.box(xs[0], r1, bw, bh, ["x", "49 пикселей"], mem=True)
    f.box(xs[1], r1, bw, bh, ["Σ W¹·x", "8 сумм по 49"])
    f.box(xs[2], r1, bw, bh, ["σ", "8 раз"])
    f.box(xs[3], r1, bw, bh, ["h", "8 чисел"], mem=True)
    f.wire([(xs[1] + bw / 2, 30), (xs[1] + bw / 2, r1)])
    for a in range(3):
        f.wire([(xs[a] + bw, r1 + bh / 2), (xs[a + 1], r1 + bh / 2)])
    f.text(0, 118, "Выходной слой", 7.5, "start", SANSB)
    f.box(0, 128, 54, 26, ["W²", "3 × 8"], mem=True)
    f.box(xs[0], r2, bw, bh, ["Σ W²·h", "3 суммы по 8"])
    f.box(xs[1], r2, bw, bh, ["σ", "3 раза"])
    f.box(xs[2], r2, bw, bh, ["y", "3 числа"], mem=True)
    f.box(xs[3], r2, bw, bh, ["Выбор класса", "max, порог 0.5"])
    f.wire([(27, 154), (27, r2)])
    f.wire([(xs[3] + bw / 2, r1 + bh), (xs[3] + bw / 2, 100), (68, 100), (68, r2)])
    for a in range(3):
        f.wire([(xs[a] + bw, r2 + bh / 2), (xs[a + 1], r2 + bh / 2)])
    f.wire([(xs[3] + bw / 2, r2 + bh), (xs[3] + bw / 2, 208)])
    f.text(xs[3] + bw / 2, 218, "класс 0, 1, 2 или 3 (шум)", 6.8)
    return f.d


def fig_system():
    f = Fig(470, 340)
    f.box(160, 0, 150, 30, ["Хост", "консоль оператора, файл весов"])
    f.rect(0, 46, 470, 290, dashed=True)
    f.text(6, 56, "Кристалл процессора", 7.5, "start", SANSB)
    f.box(40, 70, 150, 40, ["IO controller", "пакеты, DMA, START/DONE"])
    f.box(280, 70, 150, 40, ["Shared SRAM 4 КиБ", "буферы входа, MBOX"], mem=True)
    f.wire([(235, 30), (235, 56), (115, 56), (115, 70)], start=True)
    f.text(240, 41, "последовательный канал", 6.8, "start")
    f.box(10, 140, 450, 26, ["Bus matrix: коммутатор шин, 64 бит"], bold_first=True)
    f.wire([(115, 110), (115, 140)], start=True, bits=64)
    f.wire([(355, 110), (355, 140)], start=True, bits=64)
    for i in range(4):
        x = 10 + i * 117
        f.rect(x, 190, 100, 136, dashed=True)
        f.text(x + 4, 199, f"PE{i}", 7.5, "start", SANSB)
        f.box(x + 8, 210, 76, 38, ["SIMT-ядро", "2 варпа, 4 FMA"])
        f.box(x + 8, 276, 76, 38, ["Local SRAM", "2 КиБ"], mem=True)
        f.wire([(x + 46, 166), (x + 46, 210)], start=True, bits=64, bits_t=0.3)
        f.wire([(x + 46, 248), (x + 46, 276)], start=True, bits=128)
        f.wire([(x + 92, 166), (x + 92, 295), (x + 84, 295)], start=True, bits=64, bits_t=0.08)
    return f.d


def fig_warp_lanes():
    f = Fig(470, 196)
    cw, ch = 34, 16
    for panel, (x0, title, active) in enumerate([(56, "Маска: потоки 0–31", set(range(32))),
                                                 (300, "Маска: потоки 0–16", set(range(17)))]):
        f.text(x0 + 2 * cw, 8, title, 7.5, font=SANSB)
        for c in range(4):
            f.text(x0 + c * cw + cw / 2, 22, f"линия {c}", 6.5)
        n_issue = 0
        for r in range(8):
            y = 30 + r * ch
            row_active = any((4 * r + c) in active for c in range(4))
            if row_active:
                n_issue += 1
            for c in range(4):
                t = 4 * r + c
                f.rect(x0 + c * cw, y, cw, ch, fill=WHITE if t in active else MEM)
                f.text(x0 + c * cw + cw / 2, y + ch / 2, f"t{t}", 6.8)
            lab = f"такт {n_issue}" if row_active else "пропуск"
            f.text(x0 - 4, y + ch / 2, lab, 6.5, "end")
        f.text(x0 + 2 * cw, 30 + 8 * ch + 12, f"выдача команды: {n_issue} тактов", 7.5)
    f.rect(56, 186, 10, 8)
    f.text(70, 190, "поток активен", 6.8, "start")
    f.rect(160, 186, 10, 8, fill=MEM)
    f.text(174, 190, "поток выключен маской", 6.8, "start")
    return f.d


def fig_pe():
    f = Fig(470, 330)
    # control column
    f.box(0, 0, 150, 40, ["Контексты 2 варпов", "PC, маска, признак ожидания"], mem=True)
    f.box(20, 60, 130, 34, ["Табло готовности", "такт готовности регистров"], mem=True)
    f.box(0, 114, 150, 34, ["Планировщик", "выбор готового варпа"])
    f.box(0, 168, 150, 34, ["Память команд", "128 команд × 128 бит"], mem=True)
    f.box(0, 222, 150, 30, ["Дешифратор"])
    f.wire([(8, 40), (8, 114)])
    f.wire([(85, 94), (85, 114)])
    f.wire([(75, 148), (75, 168)], bits=7, bits_side=1)
    f.text(70, 158, "PC", 6.5, "end")
    f.wire([(75, 202), (75, 222)], bits=128)
    f.wire([(150, 237), (165, 237), (165, 81), (180, 81)], dashed=True)
    f.text(75, 266, "управляющие сигналы идут во все", 6.5)
    f.text(75, 275, "блоки тракта данных (справа)", 6.5)
    # datapath
    f.box(180, 0, 290, 40, ["Регистровый файл 4 КиБ", "64 потока × 16 регистров × 32 бит, 4 банка"], mem=True)
    f.box(180, 64, 290, 34, ["Выдача операндов: 4 потока за такт", "порции без активных потоков пропускаются"])
    f.wire([(325, 40), (325, 64)], bits=384)
    xs = [(180, 80), (268, 46), (322, 46), (376, 40), (424, 46)]
    f.wire([(325, 98), (325, 112)], end=False)
    f.wire([(220, 112), (447, 112)], end=False)
    f.dot(325, 112)
    for (x, w) in xs:
        cx = x + w / 2
        f.wire([(cx, 112), (cx, 130)])
        if cx not in (220, 447):
            f.dot(cx, 112)
    f.trap(180, 130, 80, 32, ["4 × FMA", "FP32"])
    f.box(268, 130, 46, 32, ["SHFL"], bold_first=True)
    f.box(322, 130, 46, 32, ["SIG"], bold_first=True)
    f.box(376, 130, 40, 32, ["CLS"], bold_first=True)
    f.box(424, 130, 46, 32, ["LSU"], bold_first=True)
    # write-back bus
    for cx in (220, 291, 335, 396, 437):
        f.wire([(cx, 162), (cx, 180)], end=False)
        f.dot(cx, 180)
    f.wire([(437, 180), (175, 180), (175, 20), (180, 20)])
    f.text(262, 189, "запись результатов в регистровый файл", 6.5)
    # ROM for SIG, local SRAM for LSU, bus port
    f.box(298, 206, 72, 32, ["ROM σ", "257 × 32 бит"], mem=True)
    f.wire([(355, 206), (355, 162)])
    f.box(382, 206, 72, 34, ["Local SRAM", "2 КиБ, 4 банка"], mem=True)
    f.wire([(422, 162), (422, 206)], start=True, bits=128, bits_t=0.75)
    f.box(392, 262, 78, 26, ["Порт шины"])
    f.wire([(422, 240), (422, 262)], start=True)
    f.wire([(462, 162), (462, 262)], start=True)
    f.wire([(431, 288), (431, 306)], start=True, bits=64)
    f.text(431, 318, "к bus matrix", 7)
    return f.d


def fig_sig():
    f = Fig(470, 196)
    f.text(0, 36, "z, FP32", 7, "start")
    f.wire([(0, 60), (22, 60)])
    f.box(22, 43, 80, 34, ["u = 16·(z + 8)"], bold_first=False)
    f.wire([(102, 60), (124, 60)])
    f.box(124, 43, 80, 34, ["k = ⌊u⌋", "a = u − k"], bold_first=False)
    f.wire([(204, 52), (226, 52)], bits=8, bits_t=0.4)
    f.box(226, 32, 60, 58, ["ROM σ", "257 × 32", "L[k], L[k+1]"], mem=True)
    f.trap_lr(310, 30, 36, 42, ["−"])
    f.wire([(286, 41), (310, 41)])
    f.wire([(286, 78), (298, 78), (298, 61), (310, 61)])
    f.dot(298, 78)
    f.trap_lr(368, 40, 40, 66, ["FMA"])
    f.wire([(346, 51), (368, 51)])
    f.text(357, 46, "Δ", 6.5)
    f.wire([(298, 78), (298, 96), (360, 96), (360, 73), (368, 73)])
    f.text(330, 91, "L[k]", 6.5)
    f.wire([(164, 77), (164, 120), (364, 120), (364, 95), (368, 95)])
    f.text(250, 115, "a", 6.5)
    f.mux(428, 40, 22, 70, [])
    f.wire([(408, 73), (428, 73)])
    f.wire([(418, 55), (428, 55)])
    f.text(415, 55, "0", 6.5, "end")
    f.wire([(418, 96), (428, 96)])
    f.text(415, 96, "1", 6.5, "end")
    f.wire([(450, 75), (470, 75)])
    f.text(468, 66, "σ̃", 7.5, "end")
    f.box(124, 150, 150, 30, ["Сравнение z с −8 и с 8"], bold_first=False)
    f.wire([(10, 60), (10, 165), (124, 165)])
    f.dot(10, 60)
    f.wire([(274, 165), (439, 165), (439, 106)], dashed=True)
    f.text(442, 140, "выбор", 6.5, "start")
    return f.d


def fig_formats():
    f = Fig(470, 120)
    s = 12.5
    x0 = 50
    f.text(0, 30, "FP32", 8, "start", SANSB)
    f.rect(x0, 20, s, 20); f.text(x0 + s / 2, 30, "s", 7)
    f.rect(x0 + s, 20, 8 * s, 20); f.text(x0 + 5 * s, 30, "порядок, 8 бит", 7)
    f.rect(x0 + 9 * s, 20, 23 * s, 20); f.text(x0 + 20.5 * s, 30, "мантисса, 23 бита", 7)
    for b, xx in ((31, x0), (23, x0 + 9 * s), (0, x0 + 32 * s)):
        f.text(xx + (s / 2 if b != 0 else -s / 2), 12, str(b), 6.5)
    f.text(0, 80, "BF16", 8, "start", SANSB)
    f.rect(x0, 70, s, 20); f.text(x0 + s / 2, 80, "s", 7)
    f.rect(x0 + s, 70, 8 * s, 20); f.text(x0 + 5 * s, 80, "порядок, 8 бит", 7)
    f.rect(x0 + 9 * s, 70, 7 * s, 20); f.text(x0 + 12.5 * s, 80, "мантисса, 7", 7)
    f.rect(x0 + 16 * s, 70, 16 * s, 20, fill=LIGHT, dashed=True)
    f.text(x0 + 24 * s, 80, "16 нулевых бит при загрузке в регистр", 7)
    f.text(x0 + 8 * s, 104, "BF16 совпадает со старшими 16 битами FP32 того же числа", 7)
    return f.d


def fig_instr():
    f = Fig(470, 70)
    fields = [("код оп.", 8), ("rd", 4), ("ra", 4), ("rb", 4), ("rc", 4), ("модиф.", 8),
              ("маска потоков", 32), ("непосредственный операнд", 32), ("база адреса", 16),
              ("шаг", 8), ("смещ.", 8)]
    s = 470 / 128
    x, bit = 0, 127
    for name, n in fields:
        w = n * s
        f.rect(x, 22, w, 22)
        f.text(x + w / 2, 33, name, 6.2 if n <= 8 else 7)
        f.text(x + 2, 14, str(bit), 5.8, "start")
        x += w
        bit -= n
    f.text(470, 14, "0", 5.8, "end")
    f.text(235, 58, "Команда 128 бит; номера битов указаны над полями", 7)
    return f.d


def fig_mapping():
    f = Fig(470, 250)
    lx, cw, rh = 118, 7.0, 13
    top = 28
    # W1 grid
    for i in range(8):
        y = top + i * rh
        p, w = i // 2, i % 2
        f.text(lx - 4, y + rh / 2, f"нейрон {i}: PE{p}, варп {w}", 6.6, "end")
        for (c0, c1, fill) in ((0, 32, WHITE), (32, 49, LIGHT)):
            f.rect(lx + c0 * cw, y, (c1 - c0) * cw, rh, fill=fill, lw=0.4)
    for c in range(1, 49):
        f.d.add(Line(lx + c * cw, f.Y(top), lx + c * cw, f.Y(top + 8 * rh),
                     strokeColor=colors.Color(0.55, 0.55, 0.55), strokeWidth=0.25))
    for i in range(0, 9, 2):
        y = top + i * rh
        f.d.add(Line(lx, f.Y(y), lx + 49 * cw, f.Y(y), strokeColor=BLACK, strokeWidth=1.3))
    f.text(lx + 16 * cw, top - 16, "проход 1: столбец j обрабатывает поток l = j", 6.6)
    f.text(lx + 40.5 * cw, top - 16, "проход 2: поток l = j − 32", 6.6)
    f.text(lx + 16 * cw, top - 6, "j = 0 … 31", 6.6)
    f.text(lx + 40.5 * cw, top - 6, "j = 32 … 48", 6.6)
    f.text(lx + 24.5 * cw, top + 8 * rh + 10, "W¹: 8 строк × 49 столбцов; строка = веса одного скрытого нейрона", 7)
    # W2 grid
    t2 = top + 8 * rh + 34
    c2 = 30
    names = ["y₀ круг", "y₁ квадрат", "y₂ треугольник"]
    for o in range(3):
        y = t2 + o * rh
        f.text(lx - 4, y + rh / 2, f"выход {o}", 6.6, "end")
        for i in range(8):
            f.rect(lx + i * c2, y, c2, rh, lw=0.4)
    for i in range(0, 9, 2):
        x = lx + i * c2
        f.d.add(Line(x, f.Y(t2), x, f.Y(t2 + 3 * rh), strokeColor=BLACK, strokeWidth=1.3))
    for i in range(8):
        f.text(lx + i * c2 + c2 / 2, t2 - 6, f"h{i}", 6.6)
    for p in range(4):
        x = lx + 2 * p * c2
        f.wire([(x + 3, t2 + 3 * rh + 8), (x + 2 * c2 - 3, t2 + 3 * rh + 8)], end=False)
        f.text(x + c2, t2 + 3 * rh + 17, f"PE{p}", 6.6)
    f.text(lx + 4 * c2, t2 + 3 * rh + 32, "W²: 3 строки × 8 столбцов; столбец i = веса от скрытого нейрона i к трём выходам", 7)
    return f.d


def fig_config_flow():
    f = Fig(470, 530)
    cx, w = 190, 250
    y = 0
    nodes = [
        ("term", ["Начало"], 24),
        ("io", ["Хост читает описание сети (файл JSON из лабораторной работы 1)"], 28),
        ("proc", ["Хост проверяет размеры, округляет веса до BF16,", "делит нейроны между PE, пишет программы варпов"], 34),
        ("io", ["Хост отправляет RESET и пакеты загрузки"], 28),
        ("proc", ["IO controller пишет программы в память команд,", "веса в local SRAM каждого PE"], 34),
        ("dec", ["Есть изображение?"], 44),
        ("io", ["Хост отправляет пакет IMAGE"], 28),
        ("proc", ["IO controller кладёт изображение в буфер shared SRAM,", "рассылает копию в local SRAM всех PE, подаёт START"], 34),
        ("proc", ["PE считают выход сети (раздел 6)"], 26),
        ("proc", ["PE0 пишет y и класс в регистры IO controller, DONE"], 26),
        ("io", ["IO controller отправляет RESULT, хост печатает ответ"], 28),
    ]
    gap = 14
    ys = []
    for kind, items, h in nodes:
        ys.append((y, h))
        if kind == "term":
            f.term(cx, y, 110, h, items)
        elif kind == "io":
            f.io(cx, y, w, h, items)
        elif kind == "proc":
            f.proc(cx, y, w + 20, h, items)
        elif kind == "dec":
            f.decision(cx, y, 150, h, items)
        y += h + gap
    for i in range(len(nodes) - 1):
        f.wire([(cx, ys[i][0] + ys[i][1]), (cx, ys[i + 1][0])])
    f.text(cx + 6, ys[5][0] + ys[5][1] + 6, "да", 6.8, "start")
    # loop back from last node to decision
    yl = ys[-1][0] + ys[-1][1]
    f.wire([(cx, yl), (cx, yl + 10), (cx + 165, yl + 10), (cx + 165, ys[5][0] + 22), (cx + 75, ys[5][0] + 22)])
    # no -> end
    ye = yl + 26
    f.wire([(cx - 75, ys[5][0] + 22), (cx - 175, ys[5][0] + 22), (cx - 175, ye + 12), (cx - 55, ye + 12)])
    f.text(cx - 80, ys[5][0] + 16, "нет", 6.8, "end")
    f.term(cx, ye, 110, 24, ["Конец"])
    return f.d


def fig_warp_flow():
    f = Fig(470, 600)
    cx, w = 160, 270
    rx = 385
    y = 0
    seq = [
        ("term", ["Начало: варп w ядра PEp считает нейрон n = 2p + w"], 26, 300),
        ("proc", ["Проход 1, потоки 0–31: загрузить x[l] и W¹[n][l],", "acc = W¹[n][l] · x[l]"], 34, w),
        ("proc", ["Проход 2, потоки 0–16: загрузить x[l+32] и W¹[n][l+32],", "acc = acc + W¹[n][l+32] · x[l+32]"], 34, w),
        ("proc", ["Свёртка за 5 шагов: поток l прибавляет acc потока l + 16,", "затем l + 8, l + 4, l + 2, l + 1; сумма у потока 0"], 34, w),
        ("proc", ["Поток 0: h = σ(сумма), округлить h до BF16"], 26, w),
        ("proc", ["Потоки 0–2: получить h от потока 0,", "вклад в выход o = l: c = W²[l][n] · h"], 34, w),
        ("dec", ["w = 1?"], 40, 110),
        ("proc", ["Барьер: ждать варп 1 этого PE"], 26, w),
        ("proc", ["Потоки 0–2: q = c + (вклад варпа 1 из local SRAM),", "записать q в MBOX shared SRAM"], 34, w),
        ("dec", ["p = 0?"], 40, 110),
        ("proc", ["Ждать 4 тройки q в MBOX"], 26, w),
        ("proc", ["Потоки 0–11: загрузить 12 чисел MBOX, сложить по выходам,", "y = σ(z), выбрать класс"], 34, w),
        ("proc", ["Записать y и класс в регистры IO controller"], 26, w),
        ("term", ["Конец"], 24, 110),
    ]
    gap = 12
    ys = []
    for kind, items, h, ww in seq:
        ys.append((y, h))
        {"term": f.term, "proc": f.proc, "dec": f.decision}[kind](cx, y, ww, h, items)
        y += h + gap
    for i in range(len(seq) - 1):
        f.wire([(cx, ys[i][0] + ys[i][1]), (cx, ys[i + 1][0])])
    # decision w = 1 -> yes branch to the right
    d1y = ys[6][0] + 20
    f.text(cx + 4, ys[6][0] + ys[6][1] + 6, "нет", 6.8, "start")
    f.text(cx + 60, d1y - 6, "да", 6.8, "start")
    f.proc(rx, d1y - 13 + 0, 140, 26, ["Записать c в local SRAM"])
    f.wire([(cx + 55, d1y), (rx - 70, d1y)])
    f.proc(rx, d1y + 30, 140, 26, ["Барьер: ждать варп 0"])
    f.wire([(rx, d1y + 13), (rx, d1y + 30)])
    f.term(rx, d1y + 72, 90, 22, ["Конец"])
    f.wire([(rx, d1y + 56), (rx, d1y + 72)])
    # decision p = 0 -> "no" branch to the right end
    d2y = ys[9][0] + 20
    f.text(cx + 4, ys[9][0] + ys[9][1] + 6, "да", 6.8, "start")
    f.text(cx + 60, d2y - 6, "нет", 6.8, "start")
    f.term(rx, d2y - 11, 90, 22, ["Конец"])
    f.wire([(cx + 55, d2y), (rx - 45, d2y)])
    return f.d


def fig_gantt(trace, bus, t_end, phases):
    f = Fig(470, 272)
    lx = 92
    scale = (470 - lx - 6) / 240.0
    X = lambda t: lx + t * scale
    rows = [(f"PE{p}, варп {w}", ("pe", p, w)) for p in range(4) for w in range(2)]
    rows += [("Шина → shared", ("bus", "shared")), ("Шина → IO", ("bus", "io"))]
    top = 40
    rh = 18
    # phase band
    for i, (a, b, _) in enumerate(phases):
        f.rect(X(a), 8, X(b) - X(a), 14, fill=LIGHT if i % 2 == 0 else WHITE, lw=0.4)
        f.text((X(a) + X(b)) / 2, 15, str(i + 1), 6.8, font=SANSB)
    f.text(lx - 4, 15, "этап", 7, "end")
    for r, (name, key) in enumerate(rows):
        y = top + r * rh
        f.text(lx - 4, y + rh / 2, name, 7, "end")
        f.d.add(Line(lx, f.Y(y + rh / 2), X(240), f.Y(y + rh / 2), strokeColor=colors.Color(0.8, 0.8, 0.8), strokeWidth=0.3))
        if key[0] == "pe":
            for ins in trace:
                if ins["pe"] == key[1] and ins["warp"] == key[2]:
                    fill = MEM if ins["op"] in ("LD", "LDS", "STL", "STS", "STIO") else WHITE
                    f.rect(X(ins["start"]), y + 4, max(X(ins["issue_end"]) - X(ins["start"]), 0.8), rh - 8, fill=fill, lw=0.4)
        else:
            for b in bus:
                if b["port"] == key[1]:
                    f.rect(X(b["start"]), y + 4, X(b["end"]) - X(b["start"]), rh - 8, fill=MEM, lw=0.4)
    yb = top + len(rows) * rh + 4
    f.d.add(Line(lx, f.Y(yb), X(240), f.Y(yb), strokeColor=BLACK, strokeWidth=0.6))
    for t in range(0, 241, 20):
        f.d.add(Line(X(t), f.Y(yb), X(t), f.Y(yb + 3), strokeColor=BLACK, strokeWidth=0.6))
        f.text(X(t), yb + 10, str(t), 6.5)
    f.text(X(240), yb + 21, "такт", 7, "end")
    f.wire([(X(t_end), top - 2), (X(t_end), yb)], dashed=True, end=False)
    f.text(X(t_end) - 3, top - 8, f"результат на такте {t_end}", 6.5, "end")
    f.rect(lx, yb + 16, 10, 7)
    f.text(lx + 14, yb + 20, "вычисление или обмен в регистрах", 6.5, "start")
    f.rect(lx + 160, yb + 16, 10, 7, fill=MEM)
    f.text(lx + 174, yb + 20, "обращение к памяти или шине", 6.5, "start")
    return f.d


# ---------------------------------------------------------------- sequence diagram
SEQ_COLS = [["Хост"], ["IO", "controller"], ["Bus", "matrix"], ["Shared", "SRAM"],
            ["Планиров-", "щик, память", "команд"], ["Local", "SRAM"], ["LSU"], ["Регистро-", "вый файл"],
            ["FMA, SHFL,", "SIG, CLS"]]
SEQ_MEM = {3, 5, 7}
SEQ_PHASES = [
    "Настройка, один раз до первого изображения",
    "Такты 0–16: изображение копируется в каждое ядро",
    "Такты 16–94: два прохода по 49 входам",
    "Такты 94–139: свёртка частичных сумм",
    "Такты 139–174: сигмоида, вклады в выходы, сумма двух варпов",
    "Такты 174–190: запись частичных сумм в MBOX",
    "Такты 190–238: выходной слой в PE0",
]
# (phase, source column, destination column, label on the arrow)
SEQ_MSGS = [
    (0, 0, 1, "RESET, LOAD"), (0, 1, 2, "конфигурация"), (0, 2, 4, "программы"), (0, 2, 5, "W¹, W²"),
    (1, 0, 1, "IMAGE"), (1, 1, 2, "x, 98 Б"), (1, 2, 3, "x в буфер A"), (1, 2, 5, "x во все PE"),
    (1, 1, 4, "START"),
    (2, 4, 6, "LD x, LD W¹"), (2, 5, 6, "x, W¹ BF16"), (2, 6, 7, "в FP32"),
    (2, 4, 8, "MUL, FMA"), (2, 7, 8, "операнды"), (2, 8, 7, "acc"),
    (3, 4, 8, "SHFL, ADD"), (3, 7, 8, "acc"), (3, 8, 7, "сумма z"),
    (4, 7, 8, "z"), (4, 8, 7, "h = σ(z)"), (4, 5, 6, "W²"), (4, 6, 7, "W²"), (4, 8, 7, "c = W²·h"),
    (4, 7, 6, "c варпа 1"), (4, 6, 5, "ST.L"), (4, 4, 4, "BAR"), (4, 5, 6, "LD c"),
    (4, 6, 7, "c варпа 1"), (4, 8, 7, "q = c + c"),
    (5, 7, 6, "q"), (5, 6, 2, "ST.S"), (5, 2, 3, "MBOX"),
    (6, 4, 4, "WAIT 4"), (6, 3, 2, "12 чисел q"), (6, 2, 6, "LD.S"), (6, 6, 7, "q"),
    (6, 8, 8, "SHFL, ADD, SIG, CLS"), (6, 8, 7, "y, класс"), (6, 7, 6, "y, класс"), (6, 6, 2, "ST.IO"),
    (6, 2, 1, "y, класс"), (6, 1, 0, "RESULT"),
]


def fig_sequence():
    n = len(SEQ_COLS)
    step = 470 / n
    cx = [step / 2 + i * step for i in range(n)]
    rows = len(SEQ_MSGS)
    top, hh, rh, ph = 0, 34, 12.0, 16
    H = top + hh + 6 + rows * rh + len(SEQ_PHASES) * ph + 8
    f = Fig(470, H)
    for i, c in enumerate(SEQ_COLS):
        f.box(cx[i] - step / 2 + 2, top, step - 4, hh, c, mem=i in SEQ_MEM, size=6.2, bold_first=False)
    y = top + hh + 6
    end_y = H - 4
    for i in range(n):
        f.d.add(Line(cx[i], f.Y(top + hh), cx[i], f.Y(end_y), strokeColor=BLACK, strokeWidth=0.4,
                     strokeDashArray=[1.5, 2]))
    ph_prev = -1
    for k, (p, s, d, lab) in enumerate(SEQ_MSGS, start=1):
        if p != ph_prev:
            f.d.add(Rect(1, f.Y(y + ph - 3), 468, ph - 4, fillColor=LIGHT, strokeColor=BLACK, strokeWidth=0.4))
            f.text(5, y + (ph - 3) / 2 + 1, SEQ_PHASES[p], 6.6, "start", SANSB)
            y += ph
            ph_prev = p
        ya = y + rh - 3
        if s == d:
            x = cx[s]
            f.wire([(x, ya - 6), (x - 9, ya - 6), (x - 9, ya), (x, ya)], dashed=False)
            f.text(x - 12, ya - 3, f"{k}  {lab}", 6.0, "end")
        else:
            dirn = 1 if d > s else -1
            f.wire([(cx[s], ya), (cx[d] - 1.5 * dirn, ya)])
            tx = cx[s] + 3 * dirn
            f.text(tx, ya - 4.2, f"{k}  {lab}", 6.0, "start" if dirn > 0 else "end")
        y += rh
    return f.d
