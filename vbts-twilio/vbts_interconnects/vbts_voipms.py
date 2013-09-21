import random

import vbts_util

class voipms_ic(vbts_util.interconnect):
    
    def __init__(self, conf):
        vbts_util.interconnect.__init__(self, conf)
        
    def get_next_avail_number(self):
        nums = []
        file_loc = self.conf['voipms_fileloc']
        f = open(file_loc, 'r')
        for l in f:
            nums.append(l.strip())
        nums = vbts_util.get_next_avail_number(nums)
        if (len(nums) == 0):
            raise ValueError("Not enough voip.ms numbers")
        return random.choice(nums)

    def send(self, to, from_, body,  to_country="US", from_country="US"):
        raise NotImplemented("VoipMS can't send sms")

