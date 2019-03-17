class hl:
    def __init__(self, leftp, rightp, cofp):
        self.leftp = leftp
        self.rightp = rightp
        self.cofp = cofp

tststr = 'Pogcs fwwf FFWFWGW POGGERS poGfwwf grpagger phchomp'

x = 0

if 'pogqqq' in tststr.lower() or 'pagqqq' in tststr.lower():
    x = x + 1

if 'pag' in tststr.lower():
    x = x + 1

if 'chomp' in tststr.lower():
    x = x + 1

if 'pog' in tststr.lower():
    x = x + 1

print(x)
print('----')

timestamps = [2, 2, 14]
print(timestamps[len(timestamps) - 1])
print(timestamps[len(timestamps) - 1] / 5)
print(int(timestamps[len(timestamps) - 1] / 5) + 1)

testar = []
for i in range(int(timestamps[len(timestamps) - 1] / 5) + 1):
    testar.append(0)

testar[1] += 1

print(testar)
print('-------')

peakresultar = []

highlightel = hl(2, 4, 7)
peakresultar.append(highlightel)

highlightel = hl(11, 15, 6)
peakresultar.append(highlightel)

highlightel = hl(6, 9, 10)
peakresultar.append(highlightel)


peakresultar.sort(key=lambda x: x.leftp)

print(peakresultar[2].leftp)


print('--------')

print(0 % 2)