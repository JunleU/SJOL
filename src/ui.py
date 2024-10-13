import pygame
import os
import sys
import configparser
import ctypes


# (D,C,H,S) + (A,2,3,4,5,6,7,8,9,0,J,Q,K)   用"jk"、"JK"分别表示小王、大王
# 黑桃-spade 红桃-heart 方快-diamond 草花-club
class Setting(object):
    """docstring for Setting"""
    def __init__(self, display_width, display_height):
        super(Setting, self).__init__()

        self.SCREEN_WIDTH = int(display_width*7/8)
        self.SCREEN_HEIGHT = int(display_height*7/8)

        config = configparser.ConfigParser()
        config.read("../conf/config.ini", encoding='utf-8')
        # print(config.sections())
        self.ascend_order = config['Pref'].getboolean('AscendingOrder')

        self.poker_backface_image = '../resources/images/poker/back.png'

        #self.scale_poker = 0.2
        self.scale_bpoker = 0.6
        self.poker_height = int(display_height/6)
        self.text_size = int(display_height/30)
        self.button_size = int(display_height/24)
        

        self.cards_gap = 720 / 12
        self.real_role = 'South'

        colors = ('H', 'S', 'D', 'C')
        nums = ('A', 'K', 'Q', 'J', '0', '9', '8', '7', '5', '6', '4', '3', '2')
        self.card_dir = [i+j for i in colors for j in nums]
        self.card_dir.append('jk')
        self.card_dir.append('JK')

    def load_poker_backface_image(self):
        image = pygame.image.load(self.poker_backface_image)
        rect = image.get_rect()
        height = self.poker_height
        width = int(rect.width * height / rect.height)
        self.poker_width = width
        #width, height = rect.width * self.scale_poker_back, rect.height * self.scale_poker_back
        image = pygame.transform.scale(image, (width, height))
        image = pygame.transform.rotate(image, 90)
        return image

    def load_face_image(self, face, role):
        if face == 'JK':
            face_image = 'jk1'
        elif face == 'jk':
            face_image = 'jk2'
        else:
            face_image = face

        face_image = '../resources/images/poker/' + face_image + '.png'
        image = pygame.image.load(face_image)
        rect = image.get_rect()
        height = self.poker_height
        #width = int(rect.width * height / rect.height)
        width = self.poker_width
        #width, height = rect.width * self.scale_poker, rect.height * self.scale_poker
        image = pygame.transform.scale(image, (width, height))
        # counterclockwise rotation
        if role == 'East':
            angle = 90
        elif role == 'West':
            angle = 270
        else:
            angle = 0
        image = pygame.transform.rotate(image, angle)
        return image

class Background(object):
    """docstring for Background"""
    def __init__(self, screen, setting):
        super(Background, self).__init__()
        self.screen = screen
        self.setting = setting
        self.width = setting.SCREEN_WIDTH
        self.height = setting.SCREEN_HEIGHT

        self.image_backface = setting.load_poker_backface_image()
        self.rect_backface = self.image_backface.get_rect()
        self.back_num = 4

        self.roles = ['East', 'North', 'West', 'South']
        self.players = {}
        for role in self.roles:
            player = Player(screen, setting, role)
            self.players[role] = player

        self.point = 0
        self.level1 = 0
        self.level2 = 0
        self.real_role = setting.real_role
        self.master = 'E'

        self.buttons = {}
        self.buttons['出'] = Button(self, '出牌', 45, 55, self.push_cards)
        self.buttons['喊'] = Button(self, '喊牌', 45, 55, self.show_cards)
        self.buttons['贴'] = Button(self, '贴牌', 45, 55, self.put_cards)

        self.textRects = {}

        self.bottom_card = []
        self.db = False

        self.clock = pygame.time.Clock()

    def initial(self):
        for role in self.roles:
            self.players[role].initial()

        self.point = 0
        self.db = False
        self.bottom_card.clear()
        self.back_num = 4

    # add a card in a player
    def add_card(self, card, turn):
        pygame.time.wait(4)
        role = self.roles[turn]
        if not self.setting.ascend_order:
            self.players[role].cards.reverse()

        self.players[role].add_card(card)

        if not self.setting.ascend_order:
            self.players[role].cards.reverse()

        self.blitme()

    def click(self, pos):
        pygame.time.wait(10)
        for button in self.buttons.values():
            if button.click(pos):
                return 1
        if self.players['South'].click_card(pos):
            self.blitme()
            return 2
        return 0

    def push_cards(self, card='No', turn=3):
        pygame.time.wait(50)
        role = self.roles[turn]
        #print(role, card)
        self.players[role].push_cards(card)

        self.blitme()
        # pygame.display.flip()

    def show_cards(self, card='No', turn=3):
        pygame.time.wait(50)
        role = self.roles[turn]
        # print(role, card)
        self.players[role].show_cards(card)
        self.blitme()

    def put_cards(self):
        for card in self.players['South'].cards.copy():
            if card.selected:
                self.bottom_card.append(card.face)
                self.players['South'].cards.remove(card)

        self.back_num = 4

    def draw_bottom(self):
        n = len(self.bottom_card)
        centerx = self.width / 2
        centery = self.height / 2
        gap = 60
        x1 = (2 * centerx - (n - 1) * gap) / 2
        for face in self.bottom_card:
            image = self.setting.load_face_image(face, 'South')
            rect = image.get_rect()
            rect.centerx = int(x1)
            rect.centery = int(centery)
            self.screen.blit(image, rect)
            x1 += gap

    def make_master(self, role):
        self.master = role
        self.blitme()

    def turn_over(self):
        pygame.time.wait(100)
        for player in self.players.values():
            player.del_out_cards()
        self.blitme()

    def update_point(self, point, level1, level2):
        self.point += point
        self.level1 += level1
        self.level2 += level2
        self.blitme()
        # pygame.display.update()

    def draw_level(self):
        size = self.setting.text_size
        text = '东西: ' + str(self.level1)
        textSurface = self.text_image(text, (255, 0, 0), size)
        textRect = textSurface.get_rect()
        textRect.top = 5
        textRect.left = 5
        self.textRects['l1'] = textRect.copy()
        self.screen.blit(textSurface, textRect)

        text = '南北: ' + str(self.level2)
        textSurface = self.text_image(text, (255, 0, 0), size)
        textRect = textSurface.get_rect()
        textRect.top = self.textRects['l1'].bottom + 5
        textRect.left = 5
        self.textRects['l2'] = textRect.copy()
        self.screen.blit(textSurface, textRect)

    def text_image(self, text, color, size):
        font = pygame.font.Font('../resources/fonts/xs.otf', size)
        textSurface = font.render(text, True, color)
        return textSurface

    def draw_point(self):
        size = self.setting.text_size
        text = '逮'
        textSurface = self.text_image(text, (255, 0, 0), size)
        textRect = textSurface.get_rect()
        textRect.top = 10
        textRect.right = self.width - 10
        self.screen.blit(textSurface, textRect)

        text = '分'
        temp_top = textRect.bottom
        textSurface = self.text_image(text, (255, 0, 0), size)
        textRect = textSurface.get_rect()
        textRect.top = temp_top
        textRect.right = self.width - 10
        self.screen.blit(textSurface, textRect)

        text = str(self.point)
        temp_top = textRect.bottom
        textSurface = self.text_image(text, (255, 0, 0), size)
        textRect = textSurface.get_rect()
        textRect.top = temp_top
        textRect.right = self.width - 10
        self.screen.blit(textSurface, textRect)
        self.textRects['p'] = textRect.copy()

    def draw_buttons(self):
        for button in self.buttons.values():
            button.draw()

    def draw_fps(self):
        fps = self.clock.get_fps()
        text = 'FPS: ' + str(int(fps))
        textSurface = self.text_image(text, (255, 255, 255), 20)
        textRect = textSurface.get_rect()
        textRect.top = 0
        textRect.left = 0

        self.screen.blit(textSurface, textRect)

    def draw_my_role(self):
        size = self.setting.text_size * 2
        role_dir = {'E': '东', 'S': '南', 'W': '西', 'N': '北'}
        text = role_dir[self.real_role[0]]
        textSurface = self.text_image(text, (255, 0, 0), size)
        textRect = textSurface.get_rect()
        textRect.bottom = self.height - 10
        textRect.left = 30

        self.screen.blit(textSurface, textRect)

    def draw_master(self):
        size = self.setting.text_size
        role_dir = {'E': '东', 'S': '南', 'W': '西', 'N': '北'}
        text = '庄:' + role_dir[self.master[0]]
        textSurface = self.text_image(text, (255, 0, 0), size)
        textRect = textSurface.get_rect()
        textRect.top = self.textRects['l2'].bottom + 5
        textRect.left = 5
        self.textRects['m'] = textRect.copy()
        self.screen.blit(textSurface, textRect)

    def resize(self, size):
        self.width = size[0]
        self.height = size[1]
        for player in self.players.values():
            player.resize(size)
        self.blitme()

    def blitme(self):
        self.clock.tick(30)
        #self.screen.blit(self.image, self.rect)
        self.screen.fill((0, 128, 0))

        # draw center poker card
        self.rect_backface.centerx = self.width/2
        self.rect_backface.centery = self.height/2
        rect_temp = pygame.Rect(self.rect_backface)
        for a in range(self.back_num):
            rect_temp.centerx = int(rect_temp.centerx - a * 0.5)
            rect_temp.centery = int(rect_temp.centery - a * 0.5)
            self.screen.blit(self.image_backface, rect_temp)

        if self.db:
            self.draw_bottom()

        # draw each player
        for player in self.players.values():
            player.blitme()

        # draw level
        self.draw_level()
        # draw master
        self.draw_master()
        # draw my role
        self.draw_my_role()
        # draw point
        self.draw_point()
        # draw buttons
        self.draw_buttons()

class Button(object):
    def __init__(self, background, text, x, y, func):
        self.background = background
        self.text = text
        self.size = background.setting.button_size
        self.x = x
        self.y = y
        self.func = func
        self.able = False

        textSurface = self.background.text_image(self.text, (255, 0, 0), self.size)
        textRect = textSurface.get_rect()
        textRect.bottom = self.background.height - x
        textRect.right = self.background.width - y
        self.rect = textRect

    def enable(self):
        self.able = True
        # self.draw()

    def disable(self):
        self.able = False

    def draw(self):
        if not self.able:
            return
        textSurface = self.background.text_image(self.text, (255, 0, 0), self.size)
        textRect = textSurface.get_rect()
        textRect.bottom = self.background.height - self.x
        textRect.right = self.background.width - self.y
        self.rect = textRect
        self.background.screen.blit(textSurface, textRect)

    def click(self, pos):
        if not self.able:
            return 0
        if self.rect.collidepoint(pos):
            self.func()
            return 1

class Poker(object):
    """dscreen, settingtring for Poker"""

    def __init__(self, screen, setting, face, role):
        super(Poker, self).__init__()
        self.screen = screen
        self.face = face
        self.image = setting.load_face_image(face, role)
        self.rect = self.image.get_rect()
        self.selected = False

    def click(self):
        if self.selected:
            self.selected = False
        else:
            self.selected = True

    def blitme(self, centerx, centery):
        self.rect.centerx = int(centerx)
        self.rect.centery = int(centery)
        if self.selected:
            self.rect.centery -= 25
        self.screen.blit(self.image, self.rect)
        line_color = (149, 129, 113)  # 红色
        line_start = (self.rect.left-1, self.rect.top + int(self.rect.height/10))  # 起始点坐标
        line_end = (self.rect.left-1, self.rect.bottom - int(self.rect.height/10))  # 结束点坐标
        line_width = 1
        pygame.draw.line(self.screen, line_color, line_start, line_end, line_width)

class Bpoker(object):
    def __init__(self, screen, setting, role):
        super(Bpoker, self).__init__()
        self.screen = screen
        self.scale = setting.scale_bpoker
        self.image = pygame.image.load(setting.poker_backface_image)
        rect = self.image.get_rect()
        height = setting.poker_height
        width = int(rect.width * height / rect.height)
        width, height = width * self.scale, height * self.scale
        self.image = pygame.transform.scale(self.image, (int(width), int(height)))
        if role == 'East':
            self.image = pygame.transform.rotate(self.image, 90)
        elif role == 'West':
            self.image = pygame.transform.rotate(self.image, 270)
        self.rect = self.image.get_rect()

    def blitme(self, centerx, centery):
        self.rect.centerx = int(centerx)
        self.rect.centery = int(centery)
        self.screen.blit(self.image, self.rect)

class Player(object):
    """dscreen, settingtring for Player"""

    def __init__(self, screen, setting, role):
        self.screen = screen
        self.setting = setting
        self.gap = setting.cards_gap
        width, height = setting.SCREEN_WIDTH, setting.SCREEN_HEIGHT
        if role == 'East':
            self.centerx = width - width / 10
            self.centery = height / 2
            self.out_centerx = 7 * width / 10
        elif role == 'South':
            self.centerx = width / 2
            self.centery = height - height / 10
            self.out_centery = 7 * height / 10
        elif role == 'West':
            self.centerx = width / 10
            self.centery = height / 2
            self.out_centerx = 3 * width / 10
        else:
            self.centerx = width / 2
            self.centery = height / 10
            self.out_centery = 3 * height / 10

        self.role = role
        self.cards = []
        self.out_cards = []
        self.bcard = Bpoker(self.screen, self.setting, self.role)

        if role != 'South':
            self.gap *= setting.scale_bpoker

    def initial(self):
        for card in self.cards:
            del card
        for card in self.out_cards:
            del card
        self.cards = []
        self.out_cards = []
        self.master = False

    def add_card(self, face):
        new_card = Poker(self.screen, self.setting, face, self.role)

        colors = ('H', 'S', 'D', 'C')
        nums = ('A', 'K', 'Q', 'J', '0', '9', '8', '7', '6', '4')
        main_cards = [j + i for i in '532' for j in colors]
        main_cards.insert(4, 'JK')
        main_cards.insert(5, 'jk')

        power = {nums[index]: index for index in range(10)}
        if face in main_cards:
            for i in range(len(self.cards)):
                while self.cards[i].face in main_cards:
                    if main_cards.index(self.cards[i].face) <= main_cards.index(face):
                        self.cards.insert(i, new_card)
                        return
                    while self.cards[i].face[1] == face[1]:
                        if self.cards[i].face[0] == face[0]:
                            self.cards.insert(i, new_card)
                            return
                        i += 1
                        if i == len(self.cards):
                            self.cards.append(new_card)
                            return
                        if self.cards[i].face[1] != face[1]:
                            self.cards.insert(i, new_card)
                            return
                    i += 1
                    if i == len(self.cards):
                        self.cards.append(new_card)
                        return
            self.cards.append(new_card)
            return

        for i in range(len(self.cards)):
            if self.cards[i].face in main_cards:
                self.cards.insert(i, new_card)
                return
            while self.cards[i].face[0] == face[0]:
                #print(self.cards[i].face)
                #print(face)
                if nums.index(self.cards[i].face[1]) <= nums.index(face[1]):
                    self.cards.insert(i, new_card)
                    return
                i += 1
                if i == len(self.cards):
                    self.cards.append(new_card)
                    return
                if self.cards[i].face[0] != face[0]:
                    self.cards.insert(i, new_card)
                    return
                if self.cards[i].face in main_cards:
                    self.cards.insert(i, new_card)
                    return
        self.cards.append(new_card)

    def click_card(self, pos):
        n = len(self.cards)
        for i in range(n):
            if self.cards[n-i-1].rect.collidepoint(pos):
                self.cards[n - i - 1].click()
                return 1
        return 0

    def push_cards(self, face='NO'):
        if self.role == 'South':
            for card in self.cards.copy():
                if card.selected:
                    self.out_cards.append(card)
                    self.cards.remove(card)
                    self.out_cards[-1].selected = False
        else:
            for card in self.cards.copy():
                if card.face == face:
                    self.out_cards.append(card)
                    self.cards.remove(card)
                    return
            print('Wrong cards!!!')

    def show_cards(self, face='NO'):
        if self.role == 'South':
            for card in self.cards.copy():
                if card.selected and card not in self.out_cards:
                    self.out_cards.append(card)
                    self.out_cards[-1].selected = False
                    self.cards[self.cards.index(card)].selected = False
        else:
            for card in self.cards.copy():
                if card.face == face:
                    self.out_cards.append(card)
                    return
            print('Wrong cards!!!')

    def del_out_cards(self):
        for card in self.out_cards:
            del card
        self.out_cards = []

    def resize(self, size):
        width, height = size[0], size[1]
        if self.role == 'East':
            self.centerx = width - width / 10
            self.centery = height / 2
            self.out_centerx = 7 * width / 10
        elif self.role == 'South':
            self.centerx = width / 2
            self.centery = height - height / 10
            self.out_centery = 7 * height / 10
        elif self.role == 'West':
            self.centerx = width / 10
            self.centery = height / 2
            self.out_centerx = 3 * width / 10
        else:
            self.centerx = width / 2
            self.centery = height / 10
            self.out_centery = 3 * height / 10

    def blitme(self):
        # draw master
        """
        if self.master:
            self.screen.blit(self.master_image, self.master_rect)
        """
        # draw cards in hand of each player
        n = len(self.cards)
        if self.role == 'South':
            x1 = (2 * self.centerx - (n - 1) * self.gap) / 2
            for a in range(n):
                self.cards[a].blitme(x1, self.centery)
                x1 += self.gap
        elif self.role == 'West':
            y1 = (2 * self.centery - (n - 1) * self.gap) / 2
            for a in range(n):
                self.bcard.blitme(self.centerx, y1)
                y1 += self.gap
        elif self.role == 'East':
            yn = (2 * self.centery + (n - 1) * self.gap) / 2
            for a in range(n):
                self.bcard.blitme(self.centerx, yn)
                yn -= self.gap
        else:
            xn = (2 * self.centerx + (n - 1) * self.gap) / 2
            for a in range(n):
                self.bcard.blitme(xn, self.centery)
                xn -= self.gap

        # draw the cards pushing out
        m = len(self.out_cards)
        if m == 0:
            return
        if self.role == 'West':
            y = (2 * self.centery - (m - 1) * self.gap * 2) / 2
            for a in range(m):
                self.out_cards[a].blitme(self.out_centerx, y)
                y += self.gap * 2
        elif self.role == 'East':
            y = (2 * self.centery + (m - 1) * self.gap*2) / 2
            for a in range(m):
                self.out_cards[a].blitme(self.out_centerx, y)
                y -= self.gap*2
        elif self.role == 'South':
            x = (2 * self.centerx - (m - 1) * self.gap) / 2
            for a in range(m):
                self.out_cards[a].blitme(x, self.out_centery)
                x += self.gap
        else:
            x = (2 * self.centerx + (m - 1) * self.gap*2) / 2
            for a in range(m):
                self.out_cards[a].blitme(x, self.out_centery)
                x -= self.gap*2

def check_events(background):
    """Respond to keypresses and mouse events."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
    # check_play_button(mouse_x, mouse_y)
        elif event.type == pygame.VIDEORESIZE:
            size = event.size
            background.resize(size)

def play_game():
    # Initialize pygame
    pygame.init()
    info = pygame.display.Info()
    display_width = info.current_w
    display_height = info.current_h
    setting = Setting(display_width, display_height)

    SCREEN_WIDTH, SCREEN_HEIGHT = setting.SCREEN_WIDTH, setting.SCREEN_HEIGHT
    x, y = 150, 60
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x, y)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("升级")
    icon = pygame.image.load("../resources/icons/poker.png")
    pygame.display.set_icon(icon)

    user32 = ctypes.WinDLL('user32')
    SW_MAXIMISE = 3
    hWnd = pygame.display.get_wm_info()["window"]
    user32.ShowWindow(hWnd, SW_MAXIMISE)

    background = Background(screen, setting)
    # (main loop)
    background.turn_over()
    while True:
        check_events(background)
        background.blitme()
        pygame.display.update()


if __name__ == "__main__":
    try:  # >= win 8.1
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:  # win 8.0 or less
        ctypes.windll.user32.SetProcessDPIAware()
    play_game()
