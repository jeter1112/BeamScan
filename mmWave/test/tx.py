import sys, os, time

frx = "rx"
fread="read"
try:
    
    os.mkfifo(frx)
    os.mkfifo(fread)

except:
    pass

prx=open(frx,'w')
pread=open(fread,'w')

for i in range(0,5):
    prx.write('b')
    prx.flush()
    pread.write('b')
    pread.flush()
    print ("Sending:", str(i))
    time.sleep(0.1)

time.sleep(1)  
print ("Closing")
prx.write('c')
prx.close()

pread.write('c')
pread.close()
b=time.time()

try:
    os.unlink(prx)
    os.unlink(pread)
except:
    pass



