"""


1. a) if NETWORKCHANGE event in android ('you are now on a new network'):

   b) if SMTP HELO/EHLO handshakes succeeds:

    - send out all pending messages in the order of their backoff-times

    - for each message that fails, increase its retry counter and compute
      next time to be sent


if smtp thread fails to establish smtp then
it waits until the minimum next backoff time and  GOTO 1b)
"""

import math
import random

def next_time(start_time, retries, constant):
    N = random.randint(0, math.pow(2, retries) - 1)
    return start_time + (N * constant)




for constant in [5, 15, 60]:
    print("")
    print("constant = {}".format(constant))
    start_time = 0.0
    for i in range(10):
        t = next_time(start_time, i, constant)
        print(int(t))




