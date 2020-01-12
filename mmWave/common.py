from math import ceil, log
import datetime

### int -> list ###
def int2intlist(x, intmax=256, num_ints=0):
    """Convert x (integer) into list of integers.
       The size of each integer in the list can optionally be controlled
       by intmax so that the integer range is 0 to intmax-1 (default: 0-255).
       Number integers in the list can optionally be controlled by parameter num_ints,
       where num_ints=0 (default) means minimum number of integers required.
    """
    vals = []
    temp = x
    if (num_ints == 0):
        if (x != 0):
            num_ints=int(ceil(log(x,intmax)))
        else:
            num_ints = 1
    for i in xrange(num_ints-1,-1,-1):
        vals.append(int(temp//intmax**i))
        temp=temp%intmax**i
    return vals



### list -> int ###
def intlist2int(intlist, intmax=256):
    """Convert list of integers (range: 0 - intmax-1) to integer."""
    return reduce(lambda x, y: x * intmax + y, intlist)



### list -> list ###
def intlist2intlist(intlist,intmax_out,num_ints=0,intmax_in=256):
    return int2intlist(intlist2int(intlist,intmax_in),intmax_out,num_ints)



def fhex(data, size):
    """Return a sized hex-string of value"""
    return '0x{:0{}X}'.format(data,size)

def reverse_bits(x, start_pos, stop_pos):
    answer = x
    for i in range(start_pos, stop_pos + 1):
        if (x & (1 << i)):
            answer |= (1 << (stop_pos + start_pos - i))
        else:
            answer &= ~(1 << (stop_pos + start_pos - i))

    return answer

def testBit(int_type, offset):
    mask = 1 << offset
    return(int_type & mask)

def clearBit(int_type, offset):
    mask = ~(1 << offset)
    return(int_type & mask)

def get_time_stamp(fmt='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.now().strftime(fmt)

