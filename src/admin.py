import random
import time
import socket
import configparser

# H S D C
# Heart Spade Diamond Club

class Admin(object):
    def __init__(self, st):
        self.cards = None
        self.players = []

        self.level = [0, 0]

        self.master = None
        self.sleep_time = st
        self.main_color = None

    # 新游戏，初始化
    def new_game(self, conn):
        self.main_color = None
        self.point = 0
        self.player_cards = [[], [], [], []]

        cards = self.create_card()
        random.shuffle(cards)
        time.sleep(1)
        random.shuffle(cards)

        conn.settimeout(0.01)
        for i in range(104):
            try:
                data = conn.recv(2)
            except:
                pass
            msg = 'a'
            msg += chr(card_dir.index(cards[i]))
            conn.send(msg.encode("UTF-8"))
            time.sleep(self.sleep_time)

        conn.settimeout(None)

        while True:
            data = conn.recv(2)
            if data:
                data = data.decode("UTF-8")
                if data[0] == 'm':
                    break
        conn.send('ae'.encode("UTF-8"))
        for i in range(4):
            msg = 'a'
            msg += chr(card_dir.index(cards[104+i]))
            conn.send(msg.encode("UTF-8"))
            time.sleep(0.4)

    '''生成一副牌'''
    def create_card(self):
        colors = ['H', 'S', 'D', 'C']
        nums = 'A234567890JQK'
        cards = []
        for color in colors:
            for i in range(13):
                c = color + nums[i]
                cards.append(c)
        cards.append('jk')
        cards.append('JK')

        for color in colors:
            for i in range(13):
                c = color + nums[i]
                cards.append(c)
        cards.append('jk')
        cards.append('JK')

        return cards

colors = ('H', 'S', 'D', 'C')
nums = ('A', 'K', 'Q', 'J', '0', '9', '8', '7', '5', '6', '4', '3', '2')
card_dir = [i + j for i in colors for j in nums]
card_dir.append('jk')
card_dir.append('JK')

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("../conf/config.ini", encoding='utf-8')

    conn = socket.socket()
    host = dft_host = config['Socket']['Host']
    port = dft_port = config['Socket'].getint('Port')

    while True:
        print("连接中")
        try:
            conn.connect((host, port))
            break
        except Exception as e:
            print(e)
            host = input("请输入服务器地址:")
            port = input("请输入服务器端口:")
            port = int(port)
    print('连接成功')
    #s = input()

    while True:
        while True:
            data = conn.recv(2)
            if data:
                data = data.decode("UTF-8")
                print(data)
                if data[0] == 'm':
                    break
        print('New game')
        conn.send('ac'.encode("UTF-8"))

        config.read("../conf/config.ini", encoding='utf-8')
        sleep_time = config['Admin'].getfloat('Sleep')
        admin = Admin(sleep_time)
        admin.new_game(conn)
        #conn.send('go'.encode("UTF-8"))

        while True:
            data = conn.recv(2)
            if data:
                data = data.decode("UTF-8")
                if data == 'go':
                    break

        num = 0
        while True:
            data = conn.recv(2)
            if data:
                data = data.decode("UTF-8")
                if data[0] in 'ESWN' and ord(data[1]) >= 0 and ord(data[1]) <= 53:
                    if ord(data[1]) >= 0 and ord(data[1]) <= 53:
                        card = card_dir[ord(data[1])]
                        print(data[0], card)
                        num += 1
                        if num == 104:
                            break

        while True:
            data = conn.recv(2)
            if data:
                data = data.decode("UTF-8")
                if data[0] == 'm':
                    break
        conn.send('ge'.encode("UTF-8"))
        print('Game over')
