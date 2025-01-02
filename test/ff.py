

a = ['ssf','dd']
acs = []
acs.extend(a)
print(acs)


bb = [['s','d'],['c']]


bb_flat = [item for bi in bb for item in bi]

acs.extend(bb_flat)
print(acs)




















