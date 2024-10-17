import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = 'yes'

import ctypes
try:  # >= win 8.1
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:  # win 8.0 or less
    ctypes.windll.user32.SetProcessDPIAware()

import pygame
from pygame.locals import *
import time
import sys
import ui
import configparser

import socket

# flags
WAITING = 0
ADDCARD = 1
PUTTING = 2
GOING = 3

if __name__ == '__main__':
    role = input("请选择您的座位(E/W/S/N):")
    while role not in ['E','W','S','N','e','w','s','n']:
        role = input("请正确输入您的座位(E/W/S/N):")
    role = role.upper()

    config = configparser.ConfigParser()
    config.read("../conf/config.ini", encoding='utf-8')

    s = socket.socket()
    host = dft_host = 'shengji.bilibil.eu.org'
    port = dft_port = 11451

    if config.has_option('Socket', 'Host'):
        host = dft_host = config['Socket']['Host']
    if config.has_option('Socket', 'Port'):
        port = dft_port = config['Socket'].getint('Port')

    while True:
        print("连接中")
        try:
            s.connect((host, port))
            break
        except Exception as e:
            print(e)
            host = input("请输入服务器地址(回车选择默认地址):")
            if host == '':
                host = dft_host
            port = input("请输入服务器端口(回车选择默认端口):")
            if port == '':
                port = dft_port
            else:
                port = int(port)

    msg = 'i' + role
    s.send(msg.encode("UTF-8"))
    print("连接成功")
    print("游戏开始后请勿关闭本窗口,可以最小化")

    pygame.init()
    info = pygame.display.Info()
    display_width = info.current_w
    display_height = info.current_h
    setting = ui.Setting(display_width, display_height)
    for i in ['East', 'West', 'South', 'North']:
        if role == i[0]:
            setting.real_role = i
            break

    SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = setting.SCREEN_WIDTH, setting.SCREEN_HEIGHT
    x, y = 150, 60
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x, y)
    screen = pygame.display.set_mode(SIZE, RESIZABLE)
    pygame.display.set_caption("升级")
    
    icon = pygame.image.load("../resources/icons/poker.png")
    pygame.display.set_icon(icon)

    background = ui.Background(screen, setting)
    me = background.players['South']

    user32 = ctypes.WinDLL('user32')
    SW_MAXIMISE = 3
    hWnd = pygame.display.get_wm_info()["window"]
    user32.ShowWindow(hWnd, SW_MAXIMISE)

    # (main loop)
    background.turn_over()
    cleaned = True
    game_num = 0
    flag = WAITING
    if role == 'S':
        roles = 'ENWS'
    elif role == 'E':
        roles = 'NWSE'
    elif role == 'N':
        roles = 'WSEN'
    else:
        roles = 'SENW'

    turn = roles.index(background.master[0])
    s.setblocking(False)
    showed_cards = []
    outed_cards = []
    temp_down_cards = []
    while True:
        slp = True
        # key_state = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == K_LEFT:
                tmp_fm = tmp_f = 0
                for i in range(len(me.cards)):
                    if i == 0:
                        if me.cards[i].selected:
                            tmp_f = 1
                        continue
                    if me.cards[i].selected:
                        if tmp_f == 1:
                            continue
                        tmp_fm = 1
                        temp_card = me.cards.pop(i)
                        me.cards.insert(i - 1, temp_card)
                    else:
                        if tmp_f == 1:
                            tmp_f = 0
                if tmp_fm == 1:
                    background.blitme()
            elif event.type == pygame.KEYDOWN and event.key == K_RIGHT:
                tmp_card_n = len(me.cards)
                tmp_fm = tmp_f = 0 # 是否发生移动，边缘是否选中
                for i in range(tmp_card_n):
                    if i == 0:
                        if me.cards[tmp_card_n - i - 1].selected:
                            tmp_f = 1
                            continue
                        continue
                    if me.cards[tmp_card_n - i - 1].selected:
                        if tmp_f == 1:
                            continue
                        tmp_fm = 1
                        temp_card = me.cards.pop(tmp_card_n - i - 1)
                        me.cards.insert(tmp_card_n - i, temp_card)
                    else:
                        if tmp_f == 1:
                            tmp_f = 0
                if tmp_fm == 1:
                    background.blitme()
            elif event.type == pygame.KEYDOWN and event.key == K_DOWN:
                temp_down_cards = []
                for card in me.cards:
                    if card.selected:
                        tmp_f = 1
                        temp_down_cards.append(card)
                        card.selected = False
                if len(temp_down_cards) > 0:
                    background.blitme()
            elif event.type == pygame.KEYDOWN and event.key == K_UP:
                if len(temp_down_cards) > 0:
                    for card in temp_down_cards:
                        card.selected = True
                    temp_down_cards = []
                    background.blitme()
            elif event.type == pygame.KEYDOWN and event.key == K_z and (event.mod & pygame.KMOD_CTRL):
                if flag == GOING:
                    tmp_rm_cards = []
                    for card in me.out_cards:
                        if card.selected:
                            tmp_rm_cards.append(card)
                            try:
                                outed_cards.remove(card)
                            except ValueError:
                                pass
                    for card in tmp_rm_cards:
                        me.out_cards.remove(card)
                        msg = role.lower()
                        msg += chr(setting.card_dir.index(card.face))
                        s.send(msg.encode("UTF-8"))
                        background.add_card(card.face)

                    """
                    for tmp_c in me.cards:
                        if tmp_c == card.face:
                            tmp_c.selected = True
                    background.blitme()
                    """

            elif event.type == VIDEORESIZE:
                size = event.size
                background.resize(size)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if slp:
                    slp = False
                # print('MOUSEBUTTONDOWN')
                if flag == GOING and not cleaned:
                    if background.buttons['出'].able:
                        if background.buttons['出'].rect.collidepoint(event.pos):
                            out_num = len(me.out_cards)
                            if out_num > 0:
                                cleaned = False
                                for r in ['East', 'North', 'West']:
                                    if len(background.players[r].out_cards) != out_num:
                                        cleaned = True
                                        break
                            else:
                                cleaned = True
                            if not cleaned:
                                for card in me.cards:
                                    if card.selected:
                                        background.turn_over()
                                        cleaned = True
                                        break
                f = background.click(event.pos)
                if f == 1: # 1-Buttons
                    if flag == GOING:
                        out_num = len(me.out_cards)
                        if out_num > 0:
                            send_num = 0
                            for card in me.out_cards:
                                if card in outed_cards:
                                    continue
                                outed_cards.append(card)
                                msg = role
                                msg += chr(setting.card_dir.index(card.face))
                                s.send(msg.encode("UTF-8"))
                                send_num += 1

                            if send_num > 0:
                                msg = role+chr(54)
                                s.send(msg.encode("UTF-8"))

                                turn += 1
                                if out_num > 0:
                                    cleaned = False
                                    for r in ['East', 'North', 'West']:
                                        if len(background.players[r].out_cards) != out_num:
                                            cleaned = True
                                            break

                    elif flag == ADDCARD:
                        for card in me.out_cards:
                            if card in showed_cards:
                                continue
                            showed_cards.append(card)
                            msg = role
                            msg += chr(setting.card_dir.index(card.face))
                            s.send(msg.encode("UTF-8"))
                        # background.buttons['喊'].disable()

                    elif flag == PUTTING:
                        for face in background.bottom_card:
                            msg = 'b'
                            msg += chr(setting.card_dir.index(face))
                            s.send(msg.encode("UTF-8"))

                        if len(background.bottom_card) == 4:
                            s.send('go'.encode("UTF-8"))
                            flag = GOING
                            #background.back_num = 4
                            for b in background.buttons.values():
                                b.disable()
                            background.buttons['出'].enable()
                            background.blitme()
                            turn = 0
                elif f == 0 and pygame.key.get_pressed()[pygame.K_LCTRL]: # 2-text
                    if background.textRects['l1'].collidepoint(event.pos):
                        if event.button == 1:
                            s.send('l1'.encode("UTF-8"))
                            background.update_point(0, 1, 0)
                        elif event.button == 3:
                            s.send('l3'.encode("UTF-8"))
                            background.update_point(0, -1, 0)
                    elif background.textRects['l2'].collidepoint(event.pos):
                        if event.button == 1:
                            s.send('l2'.encode("UTF-8"))
                            background.update_point(0, 0, 1)
                        elif event.button == 3:
                            s.send('l4'.encode("UTF-8"))
                            background.update_point(0, 0, -1)
                    elif background.textRects['p'].collidepoint(event.pos):
                        if event.button == 1:
                            s.send('p+'.encode("UTF-8"))
                            background.update_point(5, 0, 0)
                        elif event.button == 3:
                            s.send('p-'.encode("UTF-8"))
                            background.update_point(-5, 0, 0)
                    elif background.textRects['m'].collidepoint(event.pos):
                        msg = 'm' + role[0]
                        s.send(msg.encode("UTF-8"))
                        background.make_master(role)
                elif f == 0 and pygame.key.get_pressed()[pygame.K_LALT]:
                    if background.textRects['l1'].collidepoint(event.pos):
                        if event.button == 1:
                            background.update_point(0, 1, 0)
                        elif event.button == 3:
                            background.update_point(0, -1, 0)
                    elif background.textRects['l2'].collidepoint(event.pos):
                        if event.button == 1:
                            background.update_point(0, 0, 1)
                        elif event.button == 3:
                            background.update_point(0, 0, -1)
                    elif background.textRects['p'].collidepoint(event.pos):
                        if event.button == 1:
                            background.update_point(5, 0, 0)
                        elif event.button == 3:
                            background.update_point(-5, 0, 0)
                    elif background.textRects['m'].collidepoint(event.pos):
                        background.make_master(role)
                elif f == 0:
                    n = len(me.out_cards)
                    focc_tmp = 0
                    for i in range(n):
                        if me.out_cards[n - i - 1].rect.collidepoint(event.pos):
                            me.out_cards[n - i - 1].selected = not me.out_cards[n - i - 1].selected
                            focc_tmp = 1
                            break
                    if focc_tmp:
                        background.blitme()


        try:
            data = s.recv(2)

            if not data:
                print("已离线")
                break

            data = data.decode("UTF-8")
            #print(data)
            if data[0] == 'm':
                background.make_master(data[1])
            elif data[0] in 'lp':
                if data[1] == '1':
                    background.update_point(0, 1, 0)
                elif data[1] == '2':
                    background.update_point(0, 0, 1)
                elif data[1] == '3':
                    background.update_point(0, -1, 0)
                elif data[1] == '4':
                    background.update_point(0, 0, -1)
                elif data[1] == '+':
                    background.update_point(5, 0, 0)
                elif data[1] == '-':
                    background.update_point(-5, 0, 0)

            elif flag != ADDCARD and data == 'ac':
                flag = ADDCARD
                turn = roles.index(background.master[0])
                showed_cards = []
                outed_cards = []
                background.initial()
                background.blitme()
                for b in background.buttons.values():
                    b.disable()
                background.buttons['喊'].enable()
                background.blitme()

            elif flag == ADDCARD and data == 'ae':
                flag = PUTTING
                for card in me.out_cards:
                    background.add_card(card.face)
                for player in background.players.values():
                    player.out_cards = []
                for b in background.buttons.values():
                    b.disable()
                if role == background.master[0]:
                    background.buttons['贴'].enable()
                background.blitme()

            elif flag == PUTTING and data[0] == 'a':
                card = setting.card_dir[ord(data[1])]
                background.back_num -= 1
                background.add_card(card, roles.index(background.master[0]))

            elif flag == ADDCARD and data[0] == 'a':
                card = setting.card_dir[ord(data[1])]
                #print(card)
                background.add_card(card, turn % 4)
                turn += 1
            elif flag == ADDCARD and data[0] in roles:
                card = setting.card_dir[ord(data[1])]
                background.show_cards(card, roles.index(data[0]))

            elif flag != GOING and data == 'go':
                flag = GOING
                background.back_num = 4
                for b in background.buttons.values():
                    b.disable()
                background.buttons['出'].enable()
                background.blitme()
                turn = 0
            elif flag == GOING and data == 'ge':
                background.turn_over()
                background.db = True
                for b in background.buttons.values():
                    b.disable()
                background.blitme()
                flag = WAITING
            elif flag == GOING and data[0] in roles:
                if ord(data[1]) == 54:
                    turn += 1
                    out_num = len(me.out_cards)
                    # print(out_num)
                    if out_num > 0:
                        cleaned = False
                        for r in ['East', 'North', 'West']:
                            if len(background.players[r].out_cards) != out_num:
                                cleaned = True
                                break
                    """
                    turn += 1
                    if turn % 4 == 0:
                        cleaned = False
                    """
                else:
                    if not cleaned:
                        out_num = len(me.out_cards)
                        if out_num > 0:
                            cleaned = False
                            for r in ['East', 'North', 'West']:
                                if len(background.players[r].out_cards) != out_num:
                                    cleaned = True
                                    break
                        else:
                            cleaned = True
                        if not cleaned:
                            background.turn_over()
                            cleaned = True

                    card = setting.card_dir[ord(data[1])]
                    background.push_cards(card, roles.index(data[0]))
            elif flag == GOING and data[0] in roles.lower():
                card = setting.card_dir[ord(data[1])]
                tmp_player = background.players[background.roles[roles.index(data[0].upper())]]
                for tmp_card in tmp_player.out_cards:
                    if tmp_card.face == card:
                        tmp_player.out_cards.remove(tmp_card)
                        break
                background.blitme()
            elif flag == PUTTING and data[0] == 'b':
                # print(ord(data[1]))
                card = setting.card_dir[ord(data[1])]
                background.bottom_card.append(card)
                background.push_cards(card, roles.index(background.master[0]))
                background.turn_over()

        except socket.error as e:
            if e.errno == socket.errno.EWOULDBLOCK:
                if slp:
                    time.sleep(0.01)
            else:
                # 其他错误，进行相应的处理
                pass
        pygame.display.update()
