from urandom import choice, randrange, seed
from ventilastation.director import director, stripes
from ventilastation.scene import Scene
from ventilastation.sprites import Sprite
from .rotaciones import ROTACIONES

COLS = 16
ROWS = 18

class Pieza(Sprite):
    def reset(self, col, row, shape_id, rotation_id=None):
        self.col = col
        self.row = row
        self.shape_id = shape_id
        self.rotation = randrange(4) if rotation_id is None else rotation_id
        self.show()

    def show(self):
        self.set_x(self.col * 8 + 64)
        self.set_y(self.row * 8)
        self.set_strip(stripes["vortris.png"])
        self.set_frame(self.shape_id * 4 + self.rotation)

    def rotate(self):
        self.rotation = (self.rotation + 1) % 4
        self.show()

    def grilla_actual(self):
        return ROTACIONES[self.shape_id][self.rotation]

    def moved(self, dx, dy):
        p = ProtoPieza()
        p.reset(self.col+dx, self.row+dy, self.shape_id, self.rotation)
        return p


class ProtoPieza:
    def reset(self, col, row, shape_id, rotation_id=None):
        self.col = col
        self.row = row
        self.shape_id = shape_id
        self.rotation = randrange(4) if rotation_id is None else rotation_id
        self.show()
    def show(self):
        pass
    def rotate(self):
        self.rotation = (self.rotation + 1) % 4
        self.show()
    def grilla_actual(self):
        return ROTACIONES[self.shape_id][self.rotation]
    def moved(self, dx, dy):
        p = ProtoPieza()
        p.reset(self.col+dx, self.row+dy, self.shape_id, self.rotation)
        return p


BORDER = 2
OCCUPIED = 1
EMPTY = 0
VOID = 3
W = {EMPTY: '_', OCCUPIED: 'X', BORDER: '|', VOID: ' '}

class Consola:
    CCOLS = (COLS+5)*3
    CROWS = ROWS+1
    def __init__(self):
        self.board = bytearray(self.CCOLS * self.CROWS)
        for x in range(self.CCOLS * self.CROWS):
            self.board[x] = VOID

    def show(self):
        # print('  123456789 123456789 123456789 123456789 123456789 123456789 123456789 ')
        print('  123456[ fijo ]56789 1234567 [c/pieza] 9 123456789 [aftermove]23456789 ')
        for row in range(self.CROWS):
            print('%02d ' % row, end='')
            for col in range(self.CCOLS):
                c = self.board[row * self.CCOLS + col]
                print(W[c], end='')
            print()
        print()

    def set(self, x, y):
        self.reset(x,y,OCCUPIED)

    def reset(self, x, y, kind=EMPTY):
        self.board[y * self.CCOLS + x] = kind



class BasicBoard:
    def __init__(self):
        self.board = bytearray(COLS * ROWS)

    def copyAt(self, other: Consola, sx, sy):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board[row * COLS + col]:
                    other.set(col+sx, row+sy)
                else:
                    other.reset(col+sx, row+sy)
        for row in range(ROWS):
            other.reset(-1 + sx, row + sy, BORDER)
            other.reset(COLS + sx, row + sy, BORDER)
        for col in range(COLS):
            other.reset(col + sx, ROWS+sy, BORDER)

    @classmethod
    def Copy(cls, _from):
        instance = cls()
        instance.board = bytearray.fromhex(_from.board.hex())
        return instance

    def collision(self, grilla, new_col, new_row):
        for y in range(4):
            for x in range(4):
                if grilla[y*4+x] == "X":
                    if x + new_col < 0 or x + new_col >= COLS or y + new_row >= ROWS:
                        return True
                    if y + new_row >= 0 and self.board[(new_row + y) * COLS + (new_col + x)]:
                        return True
        return False

    def freeze(self, current, grilla):
        for y in range(4):
            for x in range(4):
                if grilla[y*4+x] == "X":
                    if y + current.row >= 0:
                        self.board[(current.row + y) * COLS + (current.col + x)] = 1

    def show_board(self, msg=None):
        print('  ', end='')
        for i in range(COLS):
            print('%0d'%(i%10), end='')
        print(' ', msg)
        for row in range(ROWS):
            print('%02d' % row, end='')
            for col in range(COLS):
                print("X" if self.board[row * COLS + col] else "_", end='')
            print()
        print()

    def clear_lines(self):
        new_board = [row for row in self.board if any(cell is None for cell in row)]
        lines_cleared = ROWS - len(new_board)
        # self.score += lines_cleared
        for _ in range(lines_cleared):
            new_board.insert(0, [None for _ in range(COLS)])
        self.board = new_board
        return lines_cleared


class Tablero:
    def __init__(self):
        self.unused_pieces = [Pieza() for _ in range(80)]
        self.board = BasicBoard()
        self.score = 0
        self.gameover = False
        self.spawn()

    @property
    def grilla(self):
        return ROTACIONES[self.current.shape_id][self.current.rotation]
    @property
    def next_grilla(self):
        return ROTACIONES[self.current.shape_id][(self.current.rotation + 1) % 4]

    def spawn(self):
        self.current = self.unused_pieces.pop()
        self.current.reset(COLS // 2 - 2, 2, randrange(7))
        if self.board.collision(self.grilla, self.current.col, self.current.row):
            self.gameover = True

    def freeze(self):
        self.board.freeze(self.current, self.grilla)
        self.board.show_board()
        # self.show_board()
        self.spawn()

    def clear_lines(self):
        self.score += self.board.clear_lines()

    def move(self, dx, dy):
        new_col = self.current.col + dx
        new_row = self.current.row + dy

        b1 = BasicBoard.Copy(self.board)
        b1.freeze(self.current, self.grilla)
        # b.show_board("pre")

        moved_piece = self.current.moved(dx,dy)
        b2 = BasicBoard.Copy(self.board)
        b2.freeze(moved_piece, self.grilla)
        # b.show_board("post")

        c = Consola()
        self.board.copyAt(c, 2, 0)
        b1.copyAt(c, 2+5+COLS, 0)
        b2.copyAt(c, 2+2*(5+COLS), 0)
        c.show()

        # self.board.show_board('actual')
        if not self.board.collision(self.grilla, new_col, new_row):
            self.current.col = new_col
            self.current.row = new_row
            self.current.show()
            return True
        else:
            print("collision detected")
        return False

    def rotate(self):
        new_rotation = (self.current.rotation + 1) % 4
        if not self.board.collision(self.next_grilla, self.current.col, self.current.row):
            self.current.rotation = new_rotation
            self.current.show()

    def drop(self):
        if not self.move(0, 1):
            self.board.freeze(self.current, self.grilla)


class Vortris(Scene):
    stripes_rom = "vortris"

    def on_enter(self):
        super().on_enter()
        self.game = Tablero()

    def step(self):
        if self.game.gameover:
            print("Game Over! Score:", self.game.score)
            self.finished()

        if director.was_pressed(director.JOY_LEFT):
            self.game.move(-1, 0)
        if director.was_pressed(director.JOY_RIGHT):
            self.game.move(1, 0)
        if director.was_pressed(director.JOY_DOWN):
            self.game.drop()
        if director.was_pressed(director.JOY_UP):
            self.game.rotate()
        if director.was_pressed(director.BUTTON_A):
            while self.game.move(0, 1):
                pass
            self.game.freeze()

        # caída automática
        # fall_time += clock.get_rawtime()
        # if fall_time > 1000 // FPS:
        #     self.game.drop()
        #     fall_time = 0

        if director.was_pressed(director.BUTTON_D):
            self.finished()

    def finished(self):
        director.pop()
        raise StopIteration()


def main():
    return Vortris()