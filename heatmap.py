"""

    heatmap matplotlib

"""


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pandas import read_csv

import matplotlib

filename='rssi'


#df = read_csv(filename+'.txt')
df = np.genfromtxt(filename+'.txt',delimiter=',').transpose()[::-1]

print(len(df))
print(len(df[0]))
print(df.max())
#row=int(df.argmax()/64)+2
#col=int(df.argmax()%64)-2
#print(col,row)

ax=sns.heatmap(df,cmap='jet',vmax=-25,vmin=-75,xticklabels=10,yticklabels=10)
plt.title(filename.capitalize())

plt.ylabel('RX Beam Index')
#plt.yticks([0,10,20,30,40,50,60][::-1])
#plt.xticks([i+0.5 for i in range(0,64,10)])
plt.yticks([i+3.5 for i in range(0,64,10)][::-1])
plt.xlabel('TX Beam Index')


#ax.annotate(str(round(df.max(),2)), xy=(col, row),fontsize=13,fontweight='bold')


#for item in ([ax.xaxis.label, ax.yaxis.label]):
#    item.set_fontsize(10.5)


plt.show()




