#!/usr/bin/env python3.9

"""
Conway's Game of life in Python
"""

__author__ = "TFC343"
__version__ = "1.5.2"

import collections
import copy
import dataclasses
import os
import sys
import logging
import time
import tkinter
import traceback
from tkinter.filedialog import asksaveasfilename, askopenfile
from tkinter.messagebox import showerror, askyesno

import pygame
from pygame.locals import (
    KEYDOWN,
    K_SPACE,
    MOUSEBUTTONDOWN,
    MOUSEBUTTONUP,
    QUIT,
    K_ESCAPE,
    K_p,
    FULLSCREEN,
    KMOD_CTRL,
    K_c,
    K_F11,
)

pygame.init()
pygame.font.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900

BLACK = pygame.color.Color((0, 0, 0))
GREY0 = pygame.color.Color((20, 20, 20))
GREY1 = pygame.color.Color((50, 50, 50))
GREY2 = pygame.color.Color((100, 100, 100))
GREY2_5 = pygame.color.Color((125, 125, 125))
GREY3 = pygame.color.Color((150, 150, 150))
WHITE = pygame.color.Color((255, 255, 255))
BLUE = pygame.color.Color((0, 0, 255))

FONT = pygame.font.SysFont('arial', 30)
SETTINGS_FONT = pygame.font.SysFont('arial', 24)


class DimensionError(Exception):
    pass


class AbyssList(list):
    def __getitem__(self, item):
        if 0 <= item < len(self):
            return list.__getitem__(self, item)
        else:
            return VoidEntity()

    def __setitem__(self, key, value):
        if 0 <= key < len(self):
            list.__setitem__(self, key, value)
        else:
            pass


class TorusList(list):
    def __getitem__(self, item):
        item = item % len(self)
        return list.__getitem__(self, item)

    def __setitem__(self, key, value):
        key = key % len(self)
        list.__setitem__(self, key, value)


ListType = TorusList  # the type of list being used for the board


class VoidEntity:
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        return VoidEntity()

    def __getattribute__(self, item):
        return VoidEntity()

    def __setattr__(self, key, value):
        pass

    def __getitem__(self, item):
        return VoidEntity()

    def __setitem__(self, key, value):
        pass

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return False

    def __lt__(self, other):
        return False


class Multiplier:
    def __init__(self, factor):
        self.factor = factor

    def __mul__(self, other):
        return round(self.factor * other)

    def __rmul__(self, other):
        return round(self.factor * other)


class Gol:
    def __init__(self, x=80, y=40, board=None):
        self.screen_width, self.screen_height = 1600, 900
        self.board_width, self.board_height = x, y
        self.pixel_width, self.pixel_height = self.screen_width / self.board_width, self.screen_height / self.board_height
        if board is None:
            self.board = ListType([ListType([0 for _ in range(self.board_height)]) for _ in range(self.board_width)])
        else:
            self.board = board
        self.surf = pygame.Surface((self.screen_width,  self.screen_height))
        self.surf.fill(GREY1)
        self.draw()

    def draw(self):
        self.surf.fill(GREY1)
        for x, row in enumerate(self.board):
            for y, point in enumerate(row):
                if point == 1:
                    pygame.draw.rect(self.surf, WHITE, (x * self.pixel_width, y * self.pixel_height, self.pixel_width, self.pixel_height))

        # for column in range(1, self.board_width):
        #     pygame.draw.line(self.surf, GREY2, (column * self.pixel_width, 0), (column * self.pixel_width, self.screen_height), 1)
#
        # for row in range(1, self.board_height):
        #     pygame.draw.line(self.surf, GREY2, (0, row * self.pixel_height), (self.screen_width, row * self.pixel_height), 1)

    def draw_data(self):
        for x, row in enumerate(self.board):
            for y, _ in enumerate(row):
                surrounding = 0
                points = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                for d0, d1 in points:
                    if self.board[x+d0][y+d1] == 1:
                        surrounding += 1
                self.surf.blit(FONT.render(str(surrounding), False, BLUE), (x*self.pixel_width+self.pixel_width//2, y*self.pixel_height+self.pixel_height//2))

    def update(self):
        new_board = ListType([ListType([0 for _ in range(self.board_height)]) for _ in range(self.board_width)])
        for x, row in enumerate(self.board):
            for y, _ in enumerate(row):
                surrounding = 0
                points = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                for d0, d1 in points:
                    if self.board[x + d0][y + d1] == 1:
                        surrounding += 1
                if self.board[x][y] == 1 and (surrounding == 2 or surrounding == 3):
                    new_board[x][y] = 1
                elif self.board[x][y] == 0 and (surrounding == 3):
                    new_board[x][y] = 1
                else:
                    new_board[x][y] = 0

        self.board = new_board

    def swap_cell(self, x, y):
        self.board[x][y] = int(not self.board[x][y])

    def play_step(self, ):
        # update
        self.update()

        # draw
        self.draw()

    def reset(self):
        self.board = ListType([ListType([0 for _ in range(self.board_height)]) for _ in range(self.board_width)])


@dataclasses.dataclass
class sGol:
    """a holder class for all important information of the game"""
    board_width: int
    board_height: int
    board: ListType

    @staticmethod
    def convert(game_inst: Gol):
        """convert the Gol instant into the holder type"""
        return sGol(game_inst.board_width, game_inst.board_height, game_inst.board)


class Memory:
    def __init__(self):
        self.past = collections.deque()  # all the past action the user makes
        self.future = collections.deque()  # the the future action the user makes (when the user clicks back)

    def is_empty(self) -> tuple[bool, bool]:
        """checks if past or future are empty"""
        return not bool(len(self.past)), not bool(len(self.future))

    def store(self, game_inst):
        self.future = collections.deque()
        g = sGol.convert(game_inst)
        self.past.append(copy.deepcopy(g))

    def get_past(self, game_inst):
        """called when user pressed back"""
        g = sGol.convert(game_inst)
        self.future.append(copy.deepcopy(g))
        j: sGol = self.past.pop()
        return Gol(j.board_width, j.board_height, j.board)

    def get_forward(self, game_inst):
        """called when user clicks forward"""
        g = sGol.convert(game_inst)
        self.past.append(copy.deepcopy(g))
        j: sGol = self.future.pop()
        return Gol(j.board_width, j.board_height, j.board)


def load(game_inst, file_name):
    old_game = copy.copy(game_inst)
    if file_name.split(".")[-1] == 'brd':
        try:
            with open(str(file_name), 'r') as file:
                str_ = file.read()
                str_ = str_.split(' ')
                if not(int(str_[0]) * int(str_[1]) == len(str_[2])):
                    raise DimensionError("dimensions do not fit data")
                new_board = ListType(
                    [ListType([0 for _ in range(int(str_[1]))]) for _ in range(int(str_[0]))])
                new_game = Gol(int(str_[0]), int(str_[1]))
                for x, rows in enumerate(new_board):
                    for y, dat in enumerate(rows):
                        new_game.board[x][y] = int(str_[2][x*len(rows) + y])
                return new_game
        except FileNotFoundError:
            logging.warning("file not found")
            return old_game
        except DimensionError:
            logging.warning("the dimensions provided do not fit the data")
            return old_game
    else:
        logging.warning("wrong file type")
        return old_game    


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def main():
    global SCREEN_WIDTH, SCREEN_HEIGHT
    game = Gol()
    if 'fullscreen' in sys.argv:
        surf = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), FULLSCREEN)
    else:
        surf = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("game of life in python")
    # creating window icon
    icon = pygame.Surface((32, 32))
    icon.fill(BLACK)
    img = pygame.transform.scale(pygame.image.load(resource_path('icon.png')), (30, 30))
    icon.blit(img, (1, 1))
    pygame.display.set_icon(icon)

    game_rect, step_rect, play_rect, clear_rect, quit_rect, save_as_rect, load_rect, back_rect, for_rect, slow_rect, speed_rect =\
        [VoidEntity()]*11  # init for some vars to avoid errors
    playing = False  # if the program is currently running
    playing_ = False  # if the game should be playing but can't bc the user is drawing
    drawing = 0  # {0: not drawing, 1: adding, 2: removing}
    timer = time.perf_counter()  # timing when an generation should happen
    frame_times = [1/2, 1/5, 1/15, 1/25, 1/50, 1/100]
    frame_index = 2
    frame_time = frame_times[frame_index]  # how long between each gen. at a minimum
    memory = Memory()  # where the back and forward button data is stored
    memory.store(game)  # adding original state to memory

    try:
        if sys.argv[1][-4:] == '.brd':
            game = load(game, sys.argv[1])
    except IndexError:
        pass

    running = True
    while running:
        pos = pygame.mouse.get_pos()
        # get event
        x = pygame.event.get()
        pressed_keys = pygame.key.get_pressed()
        pressed_mods = pygame.key.get_mods()
        for event in x:
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    memory.store(game)
                    playing = False
                    game.reset()
                if event.key == K_SPACE:
                    memory.store(game)
                    playing = False
                    game.play_step()
                if event.key == K_p:
                    if not playing:
                        memory.store(game)
                        playing_ = True
                    playing = not playing
                    logging.info("playing/paused")
                if event.key == K_c:
                    if pressed_mods & KMOD_CTRL:
                        top = tkinter.Tk()
                        top.withdraw()
                        user = askyesno("do you want to quit?", message="are you sure you want to quit?")
                        top.destroy()
                        if user:
                            running = False
                if event.key == K_F11:
                    pygame.display.toggle_fullscreen()
            if event.type == MOUSEBUTTONDOWN:
                if game_rect.collidepoint(pos):
                    x, y = pos
                    x, y = x - game_rect.left, y - game_rect.top
                    x, y = int(game.board_width * x / game_rect.width), int(game.board_height * y / game_rect.height)
                    if game.board[x][y] == 1:
                        playing_ = playing
                        playing = False
                        drawing = 2
                        memory.store(game)
                    elif game.board[x][y] == 0:
                        playing_ = playing
                        playing = False
                        drawing = 1
                        memory.store(game)
                elif step_rect.collidepoint(pos):
                    memory.store(game)
                    playing = False
                    game.play_step()
                elif play_rect.collidepoint(pos):
                    if not playing:
                        memory.store(game)
                        playing_ = True
                    playing = not playing
                    logging.info("playing/paused")
                elif clear_rect.collidepoint(pos):
                    memory.store(game)
                    game.reset()
                    playing = False
                elif quit_rect.collidepoint(pos):
                    top = tkinter.Tk()
                    top.withdraw()
                    user = askyesno("do you want to quit?", message="are you sure you want to quit?")
                    top.destroy()
                    if user:
                        running = False
                elif save_as_rect.collidepoint(pos):
                    top = tkinter.Tk()
                    top.withdraw()
                    file_name = asksaveasfilename(parent=top)
                    top.destroy()
                    str_ = str(game.board_width) + " " + str(game.board_height) + " "
                    for x, rows in enumerate(game.board):
                        for y, _ in enumerate(rows):
                            str_ += str(game.board[x][y])
                    try:
                        file = open(file_name+'.brd', 'x')
                        file.close()
                    except FileExistsError:
                        pass
                    with open(file_name+'.brd', 'w') as file:
                        file.write(str_)

                elif load_rect.collidepoint(pos):
                    playing = False
                    playing_ = False
                    top = tkinter.Tk()
                    top.withdraw()
                    file_name = askopenfile(parent=top)
                    if file_name is None:
                        file_name = VoidEntity()
                    top.destroy()

                    memory.store(game)
                    game = load(game, file_name.name)

                elif back_rect.collidepoint(pos):
                    playing = False
                    if memory.is_empty()[0]:
                        logging.info("no more on stack")
                    else:
                        game = memory.get_past(game)

                elif for_rect.collidepoint(pos):
                    playing = False
                    if memory.is_empty()[1]:
                        logging.info("no more on stack")
                    else:
                        game = memory.get_forward(game)

                elif slow_rect.collidepoint(pos):
                    if frame_index > 0:
                        frame_index -= 1
                        frame_time = frame_times[frame_index]

                elif speed_rect.collidepoint(pos):
                    if frame_index < len(frame_times) - 1:
                        frame_index += 1
                        frame_time = frame_times[frame_index]

                elif size_rect.collidepoint(pos):
                    new_size = [game.board_width, game.board_height]
                    def pressed(*_):
                        new_size[0], new_size[1] = ent1.get(), ent2.get()
                        top.destroy()
                    top = tkinter.Tk()
                    top.resizable(False, False)
                    top.geometry("300x240")
                    top.title("enter dimesions")
                    tkinter.Label(top, text="enter dimensions\n(this will clear the board)\n\n warning: entering too large number will cause a crash\nstick to 2 digit numbers to be safe").place(relx=0.5, rely=0.2, anchor='center')
                    tkinter.Label(top, text="width").place(relx=0.40, rely=0.45, anchor='center')
                    tkinter.Label(top, text="height").place(relx=0.60, rely=0.45, anchor='center')
                    ent1 = tkinter.Entry(top, width=3, justify='center')
                    ent1.place(relx=0.4, rely=0.6, anchor='center')
                    ent1.focus_set()
                    ent2 = tkinter.Entry(top, width=3, justify='center')
                    ent2.place(relx=0.6, rely=0.6, anchor='center')
                    btn = tkinter.Button(top, text="submit", command=pressed)
                    btn.place(relx=0.5, rely=0.82, anchor='center')
                    top.bind("<Return>", pressed)
                    tkinter.mainloop()
                    del ent1, ent2, top
                    if len(new_size) == 2:
                        try:
                            new_size = int(new_size[0]), int(new_size[1])
                        except ValueError:
                            logging.error("numbers not entered")
                        else:
                            memory.store(game)
                            playing, playing_ = False, False
                            game = Gol(*new_size)

            if event.type == MOUSEBUTTONUP:
                if drawing != 0:
                    drawing = 0
                if playing_:
                    playing = playing_
                    playing_ = False

            # if event.type == WINDOWSIZECHANGED:
            #     if WINDOWMAXIMIZED in map(lambda z: z.type, x):
            #         print("big")
            #     else:
            #         surf = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), RESIZABLE)
            # TODO add window resizing

        if pygame.mouse.get_pressed(3)[0]:
            x, y = pygame.mouse.get_pos()
            x, y = x - game_rect.left, y - game_rect.top
            x, y = int(game.board_width * x / game_rect.width), int(game.board_height * y / game_rect.height)
            if drawing == 1:
                game.board[x][y] = 1
            elif drawing == 2:
                game.board[x][y] = 0

        if playing and (time.perf_counter() - timer) > frame_time:
            timer = time.perf_counter()
            game.play_step()

        surf.fill(GREY3)

        game.draw()
        if SCREEN_HEIGHT*Multiplier(0.8*game.board_width/game.board_height) < SCREEN_WIDTH:
            img = pygame.transform.scale(game.surf, (SCREEN_HEIGHT*Multiplier(0.8*game.board_width/game.board_height), SCREEN_HEIGHT*Multiplier(0.8)))
        else:
            img = pygame.transform.scale(game.surf, (SCREEN_WIDTH*Multiplier(0.95), SCREEN_WIDTH*Multiplier(0.95*game.board_height/game.board_width)))
        game_rect = img.get_rect()
        game_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT*Multiplier(0.57))
        surf.blit(img, game_rect)

        for i in range(1, game.board_width):
            pygame.draw.line(surf, GREY2, (game_rect.left + i * game_rect.width/game.board_width, game_rect.top),
                             (game_rect.x + i * game_rect.width/game.board_width, game_rect.bottom))

        for i in range(1, game.board_height):
            pygame.draw.line(surf, GREY2, (game_rect.left, game_rect.top + i * game_rect.height/game.board_height),
                             (game_rect.right, game_rect.top + i * game_rect.height/game.board_height))

        pygame.draw.line(surf, GREY1, (0, SCREEN_HEIGHT*0.148), (SCREEN_WIDTH, SCREEN_HEIGHT*0.148))

        play_rect = pygame.Rect((40, 20, 100, 50))
        pygame.draw.rect(surf, GREY0, play_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if play_rect.collidepoint(pos) else GREY2, play_rect)
        text = SETTINGS_FONT.render("pause" if playing else "play", False, BLACK)
        r = text.get_rect()
        r.center = (0, 45)
        r.left = 48
        surf.blit(text, r)

        step_rect = pygame.Rect((40, 80, 100, 30))
        pygame.draw.rect(surf, GREY0, step_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if step_rect.collidepoint(pos) else GREY2, step_rect)
        text = SETTINGS_FONT.render("play step", False, BLACK)
        r = text.get_rect()
        r.center = (0, 95)
        r.left = 48
        surf.blit(text, r)

        clear_rect = pygame.Rect((165, 20, 75, 90))
        pygame.draw.rect(surf, GREY0, clear_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if clear_rect.collidepoint(pos) else GREY2, clear_rect)
        text = SETTINGS_FONT.render("clear", False, BLACK)
        r = text.get_rect()
        r.center = (200, 65)
        surf.blit(text, r)

        pygame.draw.line(surf, GREY1, (278, 0), (278, SCREEN_HEIGHT*0.148))

        back_rect = pygame.Rect((315, 20, 100, 40))
        pygame.draw.rect(surf, GREY0, back_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if back_rect.collidepoint(pos) else GREY2, back_rect)
        text = SETTINGS_FONT.render("back", False, BLACK)
        r = text.get_rect()
        r.center = back_rect.center
        r.left = 325
        surf.blit(text, r)

        for_rect = pygame.Rect((315, 70, 100, 40))
        pygame.draw.rect(surf, GREY0, for_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if for_rect.collidepoint(*pos) else GREY2, for_rect)
        text = SETTINGS_FONT.render("forward", False, BLACK)
        r = text.get_rect()
        r.center = for_rect.center
        r.left = 325
        surf.blit(text, r)

        pygame.draw.line(surf, GREY1, (453, 0), (453, SCREEN_HEIGHT*0.148))

        slow_rect = pygame.Rect((491, 20, 100, 40))
        pygame.draw.rect(surf, GREY0, slow_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if slow_rect.collidepoint(pos) else GREY2, slow_rect)
        text = SETTINGS_FONT.render("- speed", False, BLACK)
        r = text.get_rect()
        r.center = slow_rect.center
        surf.blit(text, r)

        speed_rect = pygame.Rect((491, 70, 100, 40))
        pygame.draw.rect(surf, GREY0, speed_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if speed_rect.collidepoint(pos) else GREY2, speed_rect)
        text = SETTINGS_FONT.render("+ speed", False, BLACK)
        r = text.get_rect()
        r.center = speed_rect.center
        surf.blit(text, r)

        pygame.draw.line(surf, GREY1, (629, 0), (629, SCREEN_HEIGHT*0.148))

        size_rect = pygame.Rect((667, 20, 100, 90))
        pygame.draw.rect(surf, GREY0, size_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if size_rect.collidepoint(pos) else GREY2, size_rect)
        text = SETTINGS_FONT.render("change", False, BLACK)
        r = text.get_rect()
        r.center = (717, 55)
        surf.blit(text, r)
        text = SETTINGS_FONT.render("board size", False, BLACK)
        r = text.get_rect()
        r.center = (717, 75)
        surf.blit(text, r)

        pygame.draw.line(surf, GREY1, (805, 0), (805, SCREEN_HEIGHT*0.148))

        pygame.draw.line(surf, GREY1, (1187, 0), (1225-38, SCREEN_HEIGHT*0.148))

        save_as_rect = pygame.Rect((1225, 20, 75, 90))
        pygame.draw.rect(surf, GREY0, save_as_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if save_as_rect.collidepoint(*pos) else GREY2, save_as_rect)
        text = SETTINGS_FONT.render("save as", False, BLACK)
        r = text.get_rect()
        r.center = (1225+38, 65)
        surf.blit(text, r)

        load_rect = pygame.Rect((1325, 20, 75, 90))
        pygame.draw.rect(surf, GREY0, load_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if load_rect.collidepoint(*pos) else GREY2, load_rect)
        text = SETTINGS_FONT.render("load", False, BLACK)
        r = text.get_rect()
        r.center = (1325+38, 65)
        surf.blit(text, r)

        pygame.draw.line(surf, GREY1, (1438, 0), (1438, SCREEN_HEIGHT * 0.148))

        quit_rect = pygame.Rect((1475, 20, 75, 90))
        pygame.draw.rect(surf, GREY0, quit_rect, 5)
        pygame.draw.rect(surf, GREY2_5 if quit_rect.collidepoint(*pos) else GREY2, quit_rect)
        text = SETTINGS_FONT.render("quit", False, BLACK)
        r = text.get_rect()
        r.center = (1512, 65)
        surf.blit(text, r)

        pygame.display.update()


if __name__ == '__main__':
    logging.basicConfig(level=logging.NOTSET, format="[%(levelname)s] -> %(message)s")
    logging.info("running version " + __version__)
    try:
        main()
    except Exception:
        logging.info("an error has occurred")
        __tb = traceback.format_exc()
        logging.info(__tb)
        __top = tkinter.Tk()
        __top.withdraw()
        showerror("Error", f"an error has occurred\ncrash report sent to {os.getcwd()}")
        __top.destroy()
        with open('crash report.txt', 'w') as __file:
            __file.write("an error has occurred\nplease send the contents of this file to https://github.com/TFC-343/GameOfLife/issues\n\n")
            __file.write(__tb)
    except KeyboardInterrupt:
        logging.info("closing from user interrupt")
    else:
        logging.info("closing")
    finally:
        pygame.quit()
        sys.exit()
