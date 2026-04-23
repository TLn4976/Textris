from random import randint

from textual.app import App, ComposeResult, RenderResult
from textual.color import Color
from textual.containers import Grid, Horizontal, Vertical, Container
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Header, Footer, Digits, Label, Static


class Kremlin(Label):
    PIC = """    ⠀⠀⠀⠀  ⠀⠀[$warning]⢰[/] ⠀⠀⠀⠀⠀
  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢐⡒⠀⠀⠀⠀⠀
⠀⠀   ⠀⠀⠀⠀⠀ ⠀[$error]⡜⣻[/]⠀⠀⠀⠀⠀
  ⠀⠀⠀⠀[$warning]⢰[/]⠀⠀⠀⠀[$warning]⢠[/][$error]⣣[$warning]⣇[/]⣆[/]⠀⠀[$warning]⢰[/]⠀
  ⠀⠀ [$success]⡠⠏⢢[/]⠀⠀[$secondary]⢀⡏⠿[/][$warning]⢹[/][$error]⠻[/]⠀[$primary]⣠⡿⣄[/]
   ⢀⠀[$success]⠼⠺⠗⢁[$primary]⣆[/][$error]⠲⠒⢢⢨⡖⣨[/][$primary]⢈⣤⡅[/][/]
   [$primary]⣴[/]⠀⠼⠿⠿[$warning]⢹⣽[/]⡜⡛⡓⢶⣾[$warning]⣒[/]⠨⠶⠷
  [$error][$primary]⢠⣟⣧[/]⣲⡆⣶⠰⠴⡏⣽⣹⠶⣴⡿⣽⠽⠇[/]
 ⣴⣒⣘⢐⣛⣛⣛⣛⣛⣒⣒⣒⣛⣛⣛⣩⣿⠭⣧
"""

    def render(self) -> RenderResult:
        return self.PIC


class SqrTiles(Grid):
    def __init__(
        self,
        *children: Widget,
        width: int = 0,
        height: int = 0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ) -> None:
        self.width = width
        self.height = height
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )

    def compose(self):
        self.tiles = [
            Static("", classes="c0") for _ in range(self.width * self.height)
        ]
        yield from self.tiles

    def on_mount(self):
        self.styles.grid_size_columns = self.width
        self.styles.grid_size_rows = self.height
        self.styles.width = self.width * 2
        self.styles.height = self.height
        self.cache = [0 for _ in range(self.width * self.height)]

    def rendBoard(self, board):
        fboard = [u for r in board for u in r]
        for i, tile in enumerate(self.tiles, 0):
            if fboard[i] != self.cache[i]:
                tile.classes = f"c{fboard[i]}"
        self.cache = fboard


class ScoreDisp(Digits):
    BORDER_TITLE = "SCORE"
    score = 0

    def addsc(self, sc):
        self.score += sc
        self.update(f"{self.score:6.0f}")

    def reset(self):
        self.score = 0
        self.update(f"{self.score:6.0f}")


class MainApp(App):
    TITLE = "TEXTRIS"

    CSS_PATH = "style"
    BINDINGS = [
        ("left", "movL", "​"),
        ("down", "movD", "​"),
        ("right", "movR", "Move"),
        ("up", "rot", "Rotate"),
        ("space", "hdDrp", "Drop"),
        ("r", "reset", "New Game"),
        ("p", "pause", "Pause"),
        ("ctrl+d", "tDark", " /"),
    ]
    ENABLE_COMMAND_PALETTE = False
    PAUSETEXT = """╭─╮╭─╮╷ ╷╭─╮╭─╴┬─╮
├─╯├─┤│ │╰─╮├╴ │ │
╵  ╵ ╵╰─╯╰─╯╰─╴┴─╯"""
    opacity = reactive(0)
    tlocked = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, icon="")
        yield Container(
            Static(self.PAUSETEXT, id="p"), Horizontal(Tetris(), id="q"), id="scr"
        )
        yield Footer()

    def action_reset(self):
        self.g.newGame()

    def action_movR(self):
        self.g.movDir = 3

    def action_movD(self):
        self.g.movDir = 4

    def action_movL(self):
        self.g.movDir = 0

    def action_hdDrp(self):
        self.g.hardDrop()

    def action_rot(self):
        self.g.rot = True

    def action_tDark(self) -> None:
        if not self.tlocked:
            self.theme = (
                "rose-pine-moon" if self.theme == "rose-pine-dawn" else "rose-pine-dawn"
            )
            self.query_one("#q").styles.background = (
                 "#faf4ed" if self.theme == "rose-pine-dawn" else "#232136"
            )

    def action_pause(self):
        t = 0 if self.opacity == 100 else 100
        self.animate("opacity", t, duration=0.75, easing="out_quint")
        if t == 100:
            try:
                self.g.drptimer.pause()
                self.g.locked = True
            except AttributeError:
                pass
        else:
            try:
                self.g.drptimer.reset()
                if not self.g.gameover:
                    self.g.locked = False
            except AttributeError:
                pass

    def on_mount(self):
        self.theme = "rose-pine-moon"
        self.g = self.query_one(Tetris)
        self.p = self.query_one("#p")

    def watch_opacity(self):
        self.p.styles.width = str(int(self.opacity)) + "%"

    def on_tetris_blink(self, message: Tetris.Blink):
        self.tlocked = True
        body = self.query_one("#q")
        col = [250, 244, 237] if self.theme == "rose-pine-dawn" else [35, 33, 54]
        col = [int(message.color[i]/2 + col[i]/2) for i in range(len(message.color))]
        body.styles.background = Color.parse(f"rgb({col[0]},{col[1]},{col[2]})")  
        self.set_timer(message.duration, lambda: self.__setattr__("tlocked", False))
        body.styles.animate(
            "background",
            "#faf4ed" if self.theme == "rose-pine-dawn" else "#232136",
            duration=message.duration,
        )


class Tetris(Horizontal):
    # COORDINATES: [ROW, COLUMN]
    ROWS = 20
    COLS = 10
    PIECES = [
        [0x4E00, 0x4640, 0x0E40, 0x4C40, 0x0270],  # T
        [0x2E00, 0x4460, 0x0E80, 0xC440, 0x0170],  # L
        [0x8E00, 0x6440, 0x0E20, 0x44C0, 0x0470],  # J
        [0x0F00, 0x2222, 0x00F0, 0x4444, 0x2222],  # I
        [0x6600, 0x6600, 0x6600, 0x6600, 0x0660],  # O
        [0xC600, 0x2640, 0x0C60, 0x4C80, 0x0630],  # Z
        [0x6C00, 0x4620, 0x06C0, 0x8C40, 0x0360],  # S
        [0, 0, 0, 0, 0],  # Blank
    ]

    pType = 7
    nType = 7
    pVar = 0
    pos = reactive([0, 3])
    movDir = reactive(-1)
    dLayer = [[int(j > 20) * -1 for _ in range(10)] for j in range(22)]
    rot = reactive(False)
    locked = False
    gameover = True
    level, rCleared = reactive(1), 0

    class Blink(Message):
        def __init__(self, color: list, duration: float, easing: str) -> None:
            self.color = color
            self.duration = duration
            self.easing = easing
            super().__init__()

    def parseP(self, p, c=1):
        p, mat = [((p >> i) & 1) * c for i in range(15, -1, -1)], []
        while p != []:
            mat.append(p[:4])
            p = p[4:]
        return mat

    def getCoords(self, lpType, lpVar, lPos) -> list:
        cPiece = self.parseP(self.PIECES[lpType][lpVar])
        return [
            [lPos[0] + r, lPos[1] + c]
            for r in range(4)
            for c in range(4)
            if cPiece[r][c] != 0
        ]

    def collide(self, coords):
        for i in coords:
            if self.dLayer[i[0]][i[1]]:
                return True
        return False

    def showNextPiece(self):
        nPiece = self.parseP(self.PIECES[self.nType][4], self.nType + 1)
        for i in nPiece:
            i.append(0)
        self.NextPiece.rendBoard(nPiece)

    def hardDrop(self):
        if not self.locked and not self.gameover:
            tPos = self.pos.copy()
            addscore = 0
            tCoords = self.getCoords(self.pType, self.pVar, tPos)
            while not self.collide(tCoords):
                tPos[0] += 1
                addscore += 2
                for i in tCoords:
                    i[0] += 1
            tPos[0] -= 1
            addscore -= 2
            self.scoreDisp.addsc(addscore)
            self.pos = tPos
            self.movDir = 1

    def tryMove(self, dire, var, doMov=1):
        oob = False
        pos = self.pos
        b = 0
        match dire:
            case 0:
                tPos = [pos[0], pos[1] - 1]
            case 1:
                tPos = [pos[0] + 1, pos[1]]
            case 4:
                tPos = [pos[0] + 1, pos[1]]
                self.scoreDisp.addsc(1)
            case 2:
                tPos = [pos[0] - 1, pos[1]]
            case 3:
                tPos = [pos[0], pos[1] + 1]
            case _:
                tPos = pos
        tCoords = self.getCoords(self.pType, var, tPos)
        for i in tCoords:
            if i[0] < 0 or i[0] > 21 or i[1] < 0 or i[1] > 9:
                oob = True
        if not oob:
            if self.collide(tCoords):
                b = -1
            else:
                if doMov:
                    self.pos = tPos
                b = 1
        return b

    def regOnDL(self):
        for r, u in self.getCoords(self.pType, self.pVar, self.pos):
            self.dLayer[r][u] = self.pType + 1
        self.Board.rendBoard(self.dLayer[1:])
        self.set_interval(0.15, self.clearRows, repeat=1)

    def clearRows(self):
        a = 0
        for r in self.dLayer:
            space = 0
            for i in r:
                if i < 1:
                    space += 1
            if not space:
                self.dLayer.pop(self.dLayer.index(r))
                self.dLayer.insert(0, [0 for _ in range(10)])
                a += 1
        if a:
            self.updateDisp()
            self.scoreDisp.addsc(2**a * 50)
            self.rCleared += a
            if a == 4:
                self.Board.border_subtitle = str(self.Board.border_subtitle) + "Tetris!"

                def t1():
                    self.Board.border_subtitle = ""

                self.set_timer(2, t1)
            if self.rCleared > 6:
                self.post_message(self.Blink([255, 204, 0], 0.5, "out_quint"))
                self.rCleared -= 7
                self.level += 1
            else:
                self.post_message(self.Blink([170, 255, 0], 0.5, "out_quint"))

    def updateDisp(self):
        temp = [r[:] for r in self.dLayer]
        for r, u in self.getCoords(self.pType, self.pVar, self.pos):
            temp[r][u] = self.pType + 1
        self.Board.rendBoard(temp[1:])

    def newPiece(self):
        self.regOnDL()
        self.locked = True
        self.drptimer.pause()
        self.pType = self.nType
        self.nType = randint(0, 6)
        self.pVar = 0
        self.pos = [0, 3]
        i = 1
        if self.pType == 3:
            i = -1
        if self.tryMove(i, 0) != 1:
            self.drptimer.stop()
            self.post_message(self.Blink([255, 85, 68], 5, "linear"))
            self.notify("Press R to play again.", title="~Game Over~")
            self.gameover = True
        else:
            self.showNextPiece()
            self.locked = False
            self.drptimer.reset()

    def newGame(self):
        if self.gameover:
            self.pType = randint(0, 6)
            self.nType = randint(0, 6)
            self.pVar = 0
            self.pos = [0, 3]
            self.movDir = -1
            self.uLayer = [[0 for _ in range(10)] for _ in range(22)]
            self.dLayer = [[int(j > 20) * -1 for _ in range(10)] for j in range(22)]
            self.rot = False
            self.locked = False
            self.gameover = False
            self.level = 1
            self.rCleared = 0
            self.drptimer = self.set_interval(0.85, self.drp1)
            self.scoreDisp.reset()
            self.showNextPiece()
            self.updateDisp()

    def watch_rot(self):
        if self.rot and not self.locked and not self.gameover:
            tVar = (self.pVar + 1) % 4
            tPos = self.pos.copy()
            mov = -1
            coords = self.getCoords(self.pType, tVar, tPos)
            failed, oob = False, False
            for i in coords:
                if i[0] < 0 or i[0] > 21 or i[1] < 0 or i[1] > 9:
                    oob = True
            if oob or self.collide(coords):
                if self.tryMove(3, tVar, 0) > 0:
                    mov = 3
                else:
                    if self.tryMove(0, tVar, 0) > 0:
                        mov = 0
                    else:
                        if self.tryMove(1, tVar, 0) > 0:
                            mov = 1
                        else:
                            if self.tryMove(2, tVar, 0) > 0:
                                mov = 2
                            else:
                                failed = True
            if not failed:
                self.pVar = tVar
                if mov > -1:
                    self.movDir = mov
                    self.drptimer.reset()
                self.updateDisp()
            self.rot = False

    def watch_level(self):
        def t1():
            self.Board.border_subtitle = ""

        self.Board.border_title = f"LEVEL {self.level}"
        if self.level > 1:
            self.Board.border_subtitle = str(self.Board.border_subtitle) + "Level Up!"
            self.drptimer.stop()
            self.drptimer = self.set_interval(0.85 / 1.1 ** (self.level - 1), self.drp1)
            self.set_timer(2, t1)

    def watch_pos(self):
        self.updateDisp()

    def watch_movDir(self):
        if not self.locked and not self.gameover:
            b = self.tryMove(self.movDir, self.pVar)
            if self.movDir % 3 == 1:
                if b == -1:
                    self.newPiece()
            self.movDir = -1

    def compose(self) -> ComposeResult:
        yield SqrTiles(id="Board", width=10, height=20)
        yield Vertical(
            ScoreDisp("114514"),
            SqrTiles(id="NextPiece", width=5, height=4),
            Kremlin(),
            id="info",
        )

    def drp1(self):
        self.movDir = 1

    def on_mount(self):
        self.scoreDisp = self.query_one(ScoreDisp)
        self.Board = self.query_one("#Board")
        self.NextPiece = self.query_one("#NextPiece")
        self.Board.border_title = "LEVEL 0"
        self.Board.border_subtitle = ""
        self.NextPiece.border_title = "NEXT:"
        self.notify(
            "TEXTRIS v0.2\nA tetris game made with Textual by Maharu\nHave Fun!   Press R to start...",
            title="WELCOME",
        )


MyApp = MainApp()
MyApp.run()
