strr = ['bw 5 2', 'bw 3 1', 'bw 3 0', 'bw 2 1', 'bw 4 2', 'bw 4 3', 'bw 1 3', 'bw 1 2', 'm u_21 s', 'm u_28 n', 'm u_41 w', 'm u_43 s', 'm u_45 w', 'm u_49 s', 'm u_67 e', 'm u_68 e', 'm u_71 e', 'm u_73 s', 'dst \'["bw 5 2", "bw 3 1", "bw 3 0", "bw 2 1", "bw 4 2", "bw 4 3", "bw 1 3", "bw 1 2", "m u_21 s", "m u_28 n", "m u_41 w", "m u_43 s", "m u_45 w", "m u_49 s", "m u_67 e", "m u_68 e", "m u_71 e", "m u_73 s"]\'']

strrr = str(strr)


aaa = [i+ ' ' * (8 - len(i)) if i.startswith('bw') and len(i)!=8 else i for i in strr]
print(aaa)

# c = ''.join('bbb')
# c = ''.join(['bb','cc'])
# print(c)
#
#
#
# b = ''.append(range(7))
# print(b)

import random
a = random.random()>0.7
print(a)









