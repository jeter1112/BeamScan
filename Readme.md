# Beam Scan





## Table of Contents

- [Environments](#environments)  
- [Principle](#principle) 
- [Run](#run)
## Environments
> GNUradio

> matplotlib,numpy,etc

~~~
    $pip install numpy matplotlib
~~~


## Principle

TX process open two namedpipe to synchronize the beamforming system.
When TX changes its beam and issues a signal "begin", Rx consumes "begin" signal and iteratively changes its beam, and at the same time issue a signal "received" to the usrp RSSI process. RSSI process will accept the "received" signal and record RSSI. 


## Run

> TX or RX
~~~
    $python beamforming.py -u SNFP19038 -x RX
~~~

> USRP RSSI
~~~
    $python rssi_usrp.py
~~~

> Heatmap
~~~
    $python heatmap.py
~~~

#### order
TX enabled-->RX enabled-->RSSI.
