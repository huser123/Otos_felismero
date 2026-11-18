"""
Ötös számjegy felismerő – csak tkinter használatával.

Működés:
  1. Tanítás: a program ötször kéri, hogy rajzolj egy 5-ös számjegyet
     egy 10×10-es rácsra.
  2. Tesztelés: háromszor kéri, hogy rajzolj egy tetszőleges számjegyet,
     és megmondja, hogy szerinte 5-ös-e.
  3. Visszajelzés: minden tipp után megmondhatod, hogy jó volt-e.
     A program ebből is tanul:
       - ami valójában 5-ös volt, az bekerül a pozitív minták közé,
       - ami nem 5-ös volt, az a negatív minták ("ellenpéldák") közé.

A felismerés lépései:
  - a rajzot a befoglaló téglalapjára vágjuk és visszanagyítjuk 10×10-re
    (így mindegy, hogy hova és mekkorára rajzolsz),
  - enyhén elmossuk, hogy az egy cellányi elcsúszás ne számítson sokat,
  - az új rajzot minden eltárolt mintához hasonlítjuk (koszinusz-hasonlóság),
  - 5-ös, ha a leghasonlóbb pozitív minta elég közel van (küszöb felett),
    ÉS közelebb van, mint a leghasonlóbb ellenpélda.
  - A küszöböt a pozitív minták egymáshoz mért hasonlóságából számoljuk,
    az ellenpéldák pedig felfelé tolhatják.
"""

import math
import tkinter as tk

RACS = 10           # 10×10-es terület
CELLA = 40          # egy cella mérete pixelben a képernyőn
TANITO_DB = 5       # ennyi tanító rajz kell
TESZT_DB = 3        # ennyi teszt rajz lesz egy körben
TURES = 0.02        # ennyivel lehet a küszöb alatt is még "ötös"
SZOMSZED_SULY = 0.25  # elmosásnál a szomszéd cellák súlya


# ---------------------------------------------------------------- feldolgozás

def normalizal(racs):
    """A rajzot a befoglaló téglalapjára vágja és 10×10-re skálázza."""
    sorok = [s for s in range(RACS) if any(racs[s])]
    oszlopok = [o for o in range(RACS) if any(racs[s][o] for s in range(RACS))]
    if not sorok:
        return [0.0] * (RACS * RACS)

    s0, s1 = min(sorok), max(sorok)
    o0, o1 = min(oszlopok), max(oszlopok)
    mag = s1 - s0 + 1
    szel = o1 - o0 + 1

    eredmeny = []
    for s in range(RACS):
        for o in range(RACS):
            # a cél cella közepe melyik forrás cellára esik
            fs = s0 + int((s + 0.5) * mag / RACS)
            fo = o0 + int((o + 0.5) * szel / RACS)
            eredmeny.append(float(racs[fs][fo]))
    return eredmeny


def elmos(v):
    """Enyhe elmosás: minden cella a szomszédaiból is kap egy kicsit."""
    eredmeny = []
    for s in range(RACS):
        for o in range(RACS):
            osszeg = suly = 0.0
            for ds in (-1, 0, 1):
                for do in (-1, 0, 1):
                    ss, oo = s + ds, o + do
                    if 0 <= ss < RACS and 0 <= oo < RACS:
                        k = 1.0 if ds == 0 and do == 0 else SZOMSZED_SULY
                        osszeg += k * v[ss * RACS + oo]
                        suly += k
            eredmeny.append(osszeg / suly)
    return eredmeny


def jellemzok(racs):
    return elmos(normalizal(racs))


def atlag(vektorok):
    n = len(vektorok)
    return [sum(v[i] for v in vektorok) / n for i in range(RACS * RACS)]


def koszinusz(a, b):
    skalar = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return skalar / (na * nb)


def legjobb(v, mintak):
    """A leghasonlóbb minta hasonlósága (0, ha nincs minta)."""
    return max((koszinusz(v, m) for m in mintak), default=0.0)


# ---------------------------------------------------------------- alkalmazás

class OtosFelismero:
    def __init__(self, ablak):
        self.ablak = ablak
        ablak.title("Ötös felismerő")
        ablak.resizable(False, False)

        self.racs = [[0] * RACS for _ in range(RACS)]
        self.pozitiv = []         # 5-ös minták (jellemző vektorok)
        self.negativ = []         # ellenpéldák (nem 5-ös rajzok)
        self.kuszob = None
        self.teszt_szam = 0
        self.fuggo = None         # (vektor, tipp) – visszajelzésre vár
        self.elozo = None         # előző cella húzáskor (hézagok kitöltéséhez)

        self.utasitas = tk.Label(ablak, font=("Arial", 14, "bold"))
        self.utasitas.pack(padx=10, pady=(10, 4))

        keret = tk.Frame(ablak)
        keret.pack(padx=10)

        meret = RACS * CELLA
        self.vaszon = tk.Canvas(keret, width=meret, height=meret, bg="white",
                                highlightthickness=1, highlightbackground="gray")
        self.vaszon.grid(row=0, column=0)

        # a tanult minta kis előnézete és a statisztika
        jobb = tk.Frame(keret)
        jobb.grid(row=0, column=1, padx=(12, 0), sticky="n")
        tk.Label(jobb, text="Tanult minta:").pack()
        self.elonezet = tk.Canvas(jobb, width=RACS * 12, height=RACS * 12,
                                  bg="white", highlightthickness=1,
                                  highlightbackground="gray")
        self.elonezet.pack()
        self.statisztika = tk.Label(jobb, justify="left", font=("Arial", 10))
        self.statisztika.pack(pady=(8, 0), anchor="w")

        self.cellak = [[self.vaszon.create_rectangle(
            o * CELLA, s * CELLA, (o + 1) * CELLA, (s + 1) * CELLA,
            fill="white", outline="#dddddd") for o in range(RACS)]
            for s in range(RACS)]

        self.vaszon.bind("<Button-1>", self.rajzol)
        self.vaszon.bind("<B1-Motion>", self.rajzol)
        self.vaszon.bind("<ButtonRelease-1>", lambda e: setattr(self, "elozo", None))
        # jobb gombbal radírozni lehet
        self.vaszon.bind("<Button-3>", self.radiroz)
        self.vaszon.bind("<B3-Motion>", self.radiroz)

        gombok = tk.Frame(ablak)
        gombok.pack(pady=8)
        self.kesz_gomb = tk.Button(gombok, text="Kész", width=12, command=self.kesz)
        self.kesz_gomb.pack(side="left", padx=5)
        self.torles_gomb = tk.Button(gombok, text="Törlés", width=12, command=self.torol)
        self.torles_gomb.pack(side="left", padx=5)

        self.eredmeny = tk.Label(ablak, font=("Arial", 13), wraplength=meret + 140)
        self.eredmeny.pack(padx=10)

        # visszajelző sáv (csak tipp után látszik)
        self.visszajelzo = tk.Frame(ablak)
        tk.Label(self.visszajelzo, text="Jól tippeltem?", font=("Arial", 12)).pack(side="left", padx=5)
        tk.Button(self.visszajelzo, text="Igen, jó", width=10, bg="#c8f0c8",
                  command=lambda: self.visszajelzes(True)).pack(side="left", padx=5)
        tk.Button(self.visszajelzo, text="Nem, rossz", width=10, bg="#f4c4c4",
                  command=lambda: self.visszajelzes(False)).pack(side="left", padx=5)

        # új kör gomb (a 3 teszt végén látszik)
        self.uj_kor_gomb = tk.Button(ablak, text="Új kör (még 3 teszt)", command=self.uj_kor)

        self.also_hely = tk.Frame(ablak, height=10)
        self.also_hely.pack()

        ablak.bind("<Return>", lambda e: self.kesz())
        self.frissit_utasitas()
        self.frissit_statisztika()

    # ---- rajzolás -----------------------------------------------------------

    def cella_xy(self, esemeny):
        o = esemeny.x // CELLA
        s = esemeny.y // CELLA
        if 0 <= s < RACS and 0 <= o < RACS:
            return s, o
        return None

    def beallit(self, s, o, ertek):
        self.racs[s][o] = ertek
        self.vaszon.itemconfig(self.cellak[s][o], fill="black" if ertek else "white")

    def rajzol(self, esemeny):
        if self.fuggo is not None:   # visszajelzésig nem módosítható a rajz
            return
        hely = self.cella_xy(esemeny)
        if hely is None:
            return
        # gyors egérmozgásnál kitöltjük a két cella közötti hézagot
        if self.elozo is not None:
            s0, o0 = self.elozo
            s1, o1 = hely
            lepes = max(abs(s1 - s0), abs(o1 - o0))
            for i in range(1, lepes):
                self.beallit(round(s0 + (s1 - s0) * i / lepes),
                             round(o0 + (o1 - o0) * i / lepes), 1)
        self.beallit(*hely, 1)
        self.elozo = hely

    def radiroz(self, esemeny):
        if self.fuggo is not None:
            return
        hely = self.cella_xy(esemeny)
        if hely is not None:
            self.beallit(*hely, 0)

    def torol(self):
        for s in range(RACS):
            for o in range(RACS):
                self.beallit(s, o, 0)

    # ---- megjelenítés -------------------------------------------------------

    def frissit_utasitas(self):
        if len(self.pozitiv) < TANITO_DB and self.kuszob is None:
            self.utasitas.config(
                text=f"Rajzolj egy 5-öst! ({len(self.pozitiv) + 1}/{TANITO_DB}. tanító minta)",
                fg="navy")
        elif self.fuggo is not None:
            self.utasitas.config(text="Jelezd vissza, jól tippeltem-e!", fg="darkorange")
        elif self.teszt_szam < TESZT_DB:
            self.utasitas.config(
                text=f"Rajzolj egy tetszőleges számjegyet! ({self.teszt_szam + 1}/{TESZT_DB}. teszt)",
                fg="darkgreen")
        else:
            self.utasitas.config(text="Vége a körnek! Köszönöm a játékot.", fg="black")

    def frissit_statisztika(self):
        kuszob = f"{self.kuszob:.2f}" if self.kuszob is not None else "–"
        self.statisztika.config(
            text=f"5-ös minták: {len(self.pozitiv)}\n"
                 f"Ellenpéldák: {len(self.negativ)}\n"
                 f"Küszöb: {kuszob}")

    def rajzol_elonezet(self):
        self.elonezet.delete("all")
        if not self.pozitiv:
            return
        minta = atlag(self.pozitiv)
        legnagyobb = max(minta) or 1.0
        k = 12
        for s in range(RACS):
            for o in range(RACS):
                ertek = minta[s * RACS + o] / legnagyobb
                szurke = int(255 * (1 - ertek))
                szin = f"#{szurke:02x}{szurke:02x}{szurke:02x}"
                self.elonezet.create_rectangle(o * k, s * k, (o + 1) * k, (s + 1) * k,
                                               fill=szin, outline="")

    # ---- logika -------------------------------------------------------------

    def kesz(self):
        if self.fuggo is not None:
            self.eredmeny.config(text="Előbb jelezd vissza, hogy jó volt-e a tipp!", fg="red")
            return
        if self.kuszob is not None and self.teszt_szam >= TESZT_DB:
            return
        if not any(any(sor) for sor in self.racs):
            self.eredmeny.config(text="Előbb rajzolj valamit a rácsra!", fg="red")
            return

        vektor = jellemzok(self.racs)

        if self.kuszob is None:                       # tanító szakasz
            self.pozitiv.append(vektor)
            self.eredmeny.config(text=f"{len(self.pozitiv)}. minta elmentve.", fg="black")
            if len(self.pozitiv) == TANITO_DB:
                self.ujraszamol()
                self.eredmeny.config(
                    text=f"Megtanultam az 5-ös formáját! (küszöb: {self.kuszob:.2f})",
                    fg="navy")
            self.torol()
        else:                                         # teszt szakasz
            self.felismer(vektor)

        self.frissit_utasitas()
        self.frissit_statisztika()

    def ujraszamol(self):
        """Újraszámolja a döntési küszöböt az összes eddigi minta alapján."""
        # leave-one-out: mennyire hasonlít egy 5-ös a legközelebbi másik 5-ösre
        sajat = [legjobb(v, self.pozitiv[:i] + self.pozitiv[i + 1:])
                 for i, v in enumerate(self.pozitiv)]
        also = min(sajat)
        kuszob = also - TURES

        # az ellenpéldák közül azok, amelyek a pozitívok "sávja" alatt vannak,
        # felfelé tolhatják a küszöböt (ami fölöttük van, azt a szomszéd-szabály kezeli)
        alatta = [legjobb(n, self.pozitiv) for n in self.negativ]
        alatta = [h for h in alatta if h < also]
        if alatta:
            kuszob = max(kuszob, min(also, max(alatta) + 0.01))

        self.kuszob = kuszob
        self.rajzol_elonezet()

    def osztalyoz(self, vektor):
        poz = legjobb(vektor, self.pozitiv)
        neg = legjobb(vektor, self.negativ)
        otos = poz >= self.kuszob and poz > neg
        return otos, poz, neg

    def felismer(self, vektor):
        otos, poz, neg = self.osztalyoz(vektor)
        self.fuggo = (vektor, otos)
        if otos:
            szoveg, szin = "Szerintem ez egy 5-ös!", "darkgreen"
        else:
            szoveg, szin = "Szerintem ez NEM 5-ös.", "red"
        reszlet = f"hasonlóság az 5-ösökhöz: {poz:.2f}, küszöb: {self.kuszob:.2f}"
        if self.negativ:
            reszlet += f", az ellenpéldákhoz: {neg:.2f}"
        self.eredmeny.config(text=f"{self.teszt_szam + 1}. teszt: {szoveg}\n({reszlet})", fg=szin)

        self.kesz_gomb.config(state="disabled")
        self.torles_gomb.config(state="disabled")
        self.visszajelzo.pack(before=self.also_hely, pady=(6, 0))

    def visszajelzes(self, jo):
        vektor, tipp = self.fuggo
        valoban_otos = tipp if jo else not tipp
        (self.pozitiv if valoban_otos else self.negativ).append(vektor)
        self.ujraszamol()

        if jo:
            uzenet = "Köszönöm! Megjegyeztem ezt a rajzot is."
        elif valoban_otos:
            uzenet = "Értem, ez 5-ös volt – felvettem az 5-ös minták közé."
        else:
            uzenet = "Értem, ez nem 5-ös – felvettem ellenpéldának."
        self.eredmeny.config(text=f"{uzenet} (új küszöb: {self.kuszob:.2f})", fg="black")

        self.fuggo = None
        self.teszt_szam += 1
        self.visszajelzo.pack_forget()
        self.torles_gomb.config(state="normal")
        self.torol()
        if self.teszt_szam < TESZT_DB:
            self.kesz_gomb.config(state="normal")
        else:
            self.uj_kor_gomb.pack(before=self.also_hely, pady=(6, 0))
        self.frissit_utasitas()
        self.frissit_statisztika()

    def uj_kor(self):
        """Újabb 3 teszt – a tanult tudás megmarad."""
        self.teszt_szam = 0
        self.uj_kor_gomb.pack_forget()
        self.kesz_gomb.config(state="normal")
        self.eredmeny.config(text="Új kör – minden eddig tanultat megtartottam.", fg="navy")
        self.frissit_utasitas()


if __name__ == "__main__":
    gyoker = tk.Tk()
    OtosFelismero(gyoker)
    gyoker.mainloop()
