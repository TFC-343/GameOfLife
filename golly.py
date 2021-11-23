#!/usr/bin/env python3.9

"""
Conway's Game of life in Python
"""

__author__ = "TFC343"
__version__ = "1.0.0"

import copy
import itertools
import pprint
import sys
import tkinter
from tkinter import Tk
from tkinter.filedialog import asksaveasfilename, askopenfile

import pygame
from pygame.locals import (
    KEYDOWN,
    K_SPACE,
    MOUSEBUTTONDOWN,
    MOUSEBUTTONUP,
    QUIT,
    K_ESCAPE,
    K_p,
    USEREVENT,
)

pygame.init()
pygame.font.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
BOARD_WIDTH, BOARD_HEIGHT = 50, 25
PIXEL_WIDTH, PIXEL_HEIGHT = SCREEN_WIDTH // BOARD_WIDTH, SCREEN_HEIGHT // BOARD_HEIGHT

BLACK = pygame.color.Color((0, 0, 0))
GREY0 = pygame.color.Color((20, 20, 20))
GREY1 = pygame.color.Color((50, 50, 50))
GREY2 = pygame.color.Color((100, 100, 100))
GREY3 = pygame.color.Color((150, 150, 150))
WHITE = pygame.color.Color((255, 255, 255))
BLUE = pygame.color.Color((0, 0, 255))

FONT = pygame.font.SysFont('arial', 30)
SETTINGS_FONT = pygame.font.SysFont('arial', 24)

PLAY_STEP = USEREVENT + 1
pygame.time.set_timer(PLAY_STEP, 1000//15)


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
        if isinstance(item, int):
            item = item % len(self)
            return list.__getitem__(self, item)
        if isinstance(item, slice):
            item = slice(0 if item.start is None else item.start,
                         len(self)-1 if item.stop is None else item.stop,
                         1 if item.step is None else item.step)
            assert item.start is not None
            assert item.stop is not None
            assert item.step is not None
            item = slice(item.start % len(self), item.stop + (item.start % len(self) - item.start), item.step)
            o = []
            for i, v in enumerate(itertools.cycle(self)):
                if i > item.stop:
                    break
                if i < item.start or i % item.step != 0:
                    continue
                o.append(v)
            return o

    def __setitem__(self, key, value):

        key = key % len(self)
        list.__setitem__(self, key, value)


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


class Gol:
    def __init__(self):
        self.screen_width, self.screen_height = 1520, 720
        self.board_width, self.board_height = 80, 40
        self.pixel_width, self.pixel_height = self.screen_width // self.board_width, self.screen_height // self.board_height
        self.board = TorusList([TorusList([0 for _ in range(self.board_height)]) for _ in range(self.board_width)])
        self.surf = pygame.Surface((self.screen_width,  self.screen_height))
        self.surf.fill(GREY1)
        self.draw()

    def draw(self):
        self.surf.fill(GREY1)
        for x, row in enumerate(self.board):
            for y, point in enumerate(row):
                if point == 1:
                    pygame.draw.rect(self.surf, WHITE, (x * self.pixel_width, y * self.pixel_height, self.pixel_width, self.pixel_height))

        for column in range(1, self.board_width):
            pygame.draw.line(self.surf, GREY2, (column * self.pixel_width, 0), (column * self.pixel_width, self.screen_height))

        for row in range(1, self.board_height):
            pygame.draw.line(self.surf, GREY2, (0, row * self.pixel_height), (self.screen_width, row * self.pixel_height))

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
        new_board = TorusList([TorusList([0 for _ in range(self.board_height)]) for _ in range(self.board_width)])
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

        # pygame.display.update()

    def reset(self):
        self.board = TorusList([TorusList([0 for _ in range(self.board_height)]) for _ in range(self.board_width)])

    def save(self):
        print(asksaveasfilename())


def pos_in_rectangle(pos: tuple[int, int], rect: pygame.Rect):
    if rect.left < pos[0] < rect.right and rect.top < pos[1] < rect.bottom:
        return True
    return False


def main():
    game = Gol()
    game_rect = game.surf.get_rect()
    game_rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
    game_rect.bottom = SCREEN_HEIGHT-25
    surf = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("game of life in python")
    playing = False
    drawing = 0  # {0: not drawing, 1: adding, 2: removing}

    while True:
        # get event
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    game.reset()
                if event.key == K_SPACE:
                    game.play_step()
                if event.key == K_p:
                    playing = not playing
            if event.type == PLAY_STEP and playing:
                game.play_step()
            if event.type == MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                pos = pygame.mouse.get_pos()
                if pos_in_rectangle(pos, game_rect):
                    x, y = x - game_rect.left, y - game_rect.top
                    x, y = int(x * (1 / game.pixel_width)), int(y * 1 / game.pixel_height)
                    if game.board[x][y] == 1:
                        drawing = 2
                    elif game.board[x][y] == 0:
                        drawing = 1
                elif pos_in_rectangle(pos, step_rect) and not playing:
                    game.play_step()
                elif pos_in_rectangle(pos, play_rect):
                    playing = not playing
                elif pos_in_rectangle(pos, clear_rect):
                    game.reset()
                    playing = False
                elif pos_in_rectangle(pos, quit_rect):
                    pygame.quit()
                    sys.exit()
                elif pos_in_rectangle(pos, save_as_rect):
                    top = tkinter.Tk()
                    top.withdraw()
                    file_name = asksaveasfilename(parent=top)
                    top.destroy()
                    str_ = ''
                    for x, rows in enumerate(game.board):
                        for y, _ in enumerate(rows):
                            str_ += str(game.board[x][y])
                    try:
                        file = open(file_name+'.brd', 'w')
                        file.write(str_)
                    except FileNotFoundError:
                        file = open(file_name+'.brd', 'x')
                        file.close()
                        file = open(file_name+'.brd', 'w')
                        file.write(str_)
                    finally:
                        file.close()
                elif pos_in_rectangle(pos, load_rect):
                    playing = False
                    top = tkinter.Tk()
                    top.withdraw()
                    file_name = askopenfile(parent=top)
                    top.destroy()
                    old_board = copy.copy(game.board)
                    try:
                        game.reset()
                        file = open(str(file_name.name), 'r')
                        str_ = file.read()
                        for x, rows in enumerate(game.board):
                            for y, dat in enumerate(rows):
                                game.board[x][y] = int(str_[x*len(rows) + y])

                    except FileNotFoundError:
                        print("file not found")
                        game.board = old_board
                    finally:
                        file.close()
                    print(game.board)
            if event.type == MOUSEBUTTONUP:
                drawing = 0

        if pygame.mouse.get_pressed(3)[0]:
            x, y = pygame.mouse.get_pos()
            x, y = x - game_rect.left, y - game_rect.top
            x, y = int(x * (1 / game.pixel_width)), int(y * 1 / game.pixel_height)
            if drawing == 1:
                game.board[x][y] = 1
            elif drawing == 2:
                game.board[x][y] = 0

        surf.fill(GREY3)

        game.draw()

        surf.blit(game.surf, game_rect)

        pygame.draw.line(surf, GREY1, (0, 133), (SCREEN_WIDTH, 133))

        play_rect = pygame.Rect((40, 20, 100, 50))
        pygame.draw.rect(surf, GREY0, play_rect, 5)
        pygame.draw.rect(surf, GREY2, play_rect)
        text = SETTINGS_FONT.render("pause" if playing else "play", False, BLACK)
        r = text.get_rect()
        r.center = (0, 45)
        r.left = 48
        surf.blit(text, r)

        step_rect = pygame.Rect((40, 80, 100, 30))
        pygame.draw.rect(surf, GREY0, step_rect, 5)
        pygame.draw.rect(surf, GREY2, step_rect)
        text = SETTINGS_FONT.render("play step", False, BLACK)
        r = text.get_rect()
        r.center = (0, 95)
        r.left = 48
        surf.blit(text, r)

        clear_rect = pygame.Rect((165, 20, 75, 90))
        pygame.draw.rect(surf, GREY0, clear_rect, 5)
        pygame.draw.rect(surf, GREY2, clear_rect)
        text = SETTINGS_FONT.render("clear", False, BLACK)
        r = text.get_rect()
        r.center = (200, 65)
        surf.blit(text, r)

        # save_rect = pygame.Rect((1200, 20, 100, 50))
        # pygame.draw.rect(surf, GREY0, save_rect, 5)
        # pygame.draw.rect(surf, GREY2, save_rect)
        # text = SETTINGS_FONT.render("save", False, BLACK)
        # r = text.get_rect()
        # r.center = (0, 45)
        # r.left = 48+1160
        # surf.blit(text, r)

        save_as_rect = pygame.Rect((1225, 20, 75, 90))
        pygame.draw.rect(surf, GREY0, save_as_rect, 5)
        pygame.draw.rect(surf, GREY2, save_as_rect)
        text = SETTINGS_FONT.render("save as", False, BLACK)
        r = text.get_rect()
        r.center = (1225+38, 65)
        surf.blit(text, r)

        load_rect = pygame.Rect((1325, 20, 75, 90))
        pygame.draw.rect(surf, GREY0, load_rect, 5)
        pygame.draw.rect(surf, GREY2, load_rect)
        text = SETTINGS_FONT.render("load", False, BLACK)
        r = text.get_rect()
        r.center = (1325+38, 65)
        surf.blit(text, r)

        quit_rect = pygame.Rect((1475, 20, 75, 90))
        pygame.draw.rect(surf, GREY0, quit_rect, 5)
        pygame.draw.rect(surf, GREY2, quit_rect)
        text = SETTINGS_FONT.render("quit", False, BLACK)
        r = text.get_rect()
        r.center = (1512, 65)
        surf.blit(text, r)

        pygame.display.update()


if __name__ == '__main__':
    main()
