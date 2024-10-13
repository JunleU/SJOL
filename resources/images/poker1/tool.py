# (D,C,H,S) + (A,2,3,4,5,6,7,8,9,0,J,Q,K)   用"jk"、"JK"分别表示小王、大王
# 黑桃-spade 红桃-heart 方快-diamond 草花-club
from os import rename
from os import listdir
from os.path import isfile, join
def rename_puke():
	pukes = []
	for f in listdir():
		if isfile(f):
			if f[0] == 'd':
				continue
			fix = f.split('.')
			if fix[1] == 'png':
				pukes.append(fix[0])

	pukes.sort()
	colors = ('D','H','S','C')
	nums = ('2','3','4','5','6','7','8','9','0','J','Q','K','A')
	words = ('Two', "Three", 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten')
	#print(str(pukes[0])+'.jpg', 'jk'+'.jpg')
	#print(str(pukes[1])+'.jpg', 'JK'+'.jpg')
	#rename(str(pukes[0])+'.jpg', 'jk1'+'.png')
	#rename(str(pukes[1])+'.jpg', 'jk2'+'.png')
	for puke in pukes:
		ws = puke.split(' ')
		if ws[0] in words:
			after = ws[2][0] + nums[words.index(ws[0])]
		else:
			after = ws[2][0] + ws[0][0]
		before = str(puke) + '.png'
		after += '.png'
		#print(before, after)
		rename(before, after)

rename_puke()
