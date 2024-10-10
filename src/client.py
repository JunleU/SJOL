import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = 'yes'

import pygame
from pygame.locals import *
import time
import sys
import ui

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

    s = socket.socket()
    with open('../res/host', 'r') as hostfile:
        host = dft_host = hostfile.readline().replace('\r','').replace('\n','')
        port = hostfile.readline()
        port = dft_port = int(port)

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
    setting = ui.Setting()
    for i in ['East', 'West', 'South', 'North']:
        if role == i[0]:
            setting.real_role = i
            break

    SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = setting.SCREEN_WIDTH, setting.SCREEN_HEIGHT
    x, y = 150, 60
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x, y)
    screen = pygame.display.set_mode(SIZE, RESIZABLE)
    pygame.display.set_caption("升级")
    
    icon = pygame.image.load("../res/ico/poker.png")
    pygame.display.set_icon(icon) 

    background = ui.Background(screen, setting)
    me = background.players['South']

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
    while True:
        slp = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                sys.exit()
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
                            background.turn_over()
                            cleaned = True
                f = background.click(event.pos)
                if f == 1: # 1-Buttons
                    if flag == GOING:
                        for card in me.out_cards:
                            msg = role
                            msg += chr(setting.card_dir.index(card.face))
                            s.send(msg.encode("UTF-8"))
                        msg = role+chr(54)
                        s.send(msg.encode("UTF-8"))

                        turn += 1
                        out_num = len(background.players['South'].out_cards)
                        if out_num > 0:
                            cleaned = False
                            for r in ['East', 'North', 'West']:
                                if len(background.players[r].out_cards) != out_num:
                                    cleaned = True
                                    break

                    elif flag == ADDCARD:
                        for card in me.out_cards:
                            msg = role
                            msg += chr(setting.card_dir.index(card.face))
                            s.send(msg.encode("UTF-8"))
                        # background.buttons['喊'].disable()

                    elif flag == PUTTING:
                        for face in background.bottom_card:
                            msg = 'b'
                            msg += chr(setting.card_dir.index(face))
                            s.send(msg.encode("UTF-8"))
                        s.send('go'.encode("UTF-8"))
                        flag = GOING
                        background.back_num = 4
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
                background.initial()
                background.blitme()
                for b in background.buttons.values():
                    b.disable()
                background.buttons['喊'].enable()
                background.blitme()

            elif flag == ADDCARD and data == 'ae':
                flag = PUTTING
                background.turn_over()
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
                background.blitme()
                flag = WAITING
            elif flag == GOING and data[0] in roles:
                if ord(data[1]) == 54:
                    turn += 1
                    out_num = len(background.players['South'].out_cards)
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
                        background.turn_over()
                        cleaned = True
                    card = setting.card_dir[ord(data[1])]
                    background.push_cards(card, roles.index(data[0]))

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
