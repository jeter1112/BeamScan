

import os, sys,time

frx = "rx"

fread="rxread"


prx=open(frx,'r')
pread=open(fread,'w')

while True:
   
    
    r= prx.read(1)

    if r=='b':

        for i in range(0,5):
            pread.write('b')
            pread.flush()
            print (str(i))
            time.sleep(0.01)
    elif r=='c':
        break
    else:
        print('rx error')
        sys.exit(1)

prx.close()

pread.write('c')
pread.close()


try:
    os.unlink(pread)
    os.unlink(prx)
except:
    pass

