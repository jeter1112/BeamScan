

import os, sys,time

fread = "read"

frxread="rxread"


pread=open(fread,'r')
prxread=open(frxread,'r')

while True:
   
    
    r= pread.read(1)

    if r=='b':

        for i in range(0,5):
            da=prxread.read(1)
            if da =='b':
                print(str(i))
                time.sleep(0.01)
            elif da=='':
                print('?')
            elif da=='c':
                print(da)
                prxread.close()
                pread.close()
                sys.exit()
                    
    elif r=='c':
        break
    else:
        print('rx error')
        sys.exit(1)
pread.close()
prxread.close()


try:
    os.unlink(pread)
    os.unlink(prxread)
except:
    pass


