from ESL import *
import vbts_util
import syslog

#this should probably be something different
class freeswitch_ic(vbts_util.interconnect):
    
    def __init__(self, conf):
         vbts_util.interconnect.__init__(self, conf)

    def _send_raw_to_freeswitch(self, to, from_, body):
        con = ESLconnection(self.conf['fs_esl_ip'], self.conf['fs_esl_port'], self.conf['fs_esl_pass'])
        if con.connected():
            syslog.syslog("Kurtis: " + "python VBTS_Send_SMS %s|%s|%s" % (to, from_, body))
            e = con.api("python VBTS_Send_SMS %s|%s|%s" % (to, from_, body))
            e = con.api("python VBTS_Wake_BTS %s|%s" % (to, "Incoming SMS"))
            return True # TODO return something more sensible
        return False

    def send(self, to, from_, body, to_country=None, from_country=None):
        """
        Send properly-formatted numbers to FreeSwitch
        """
	# Internally, our canonical format is E.164 without the leading plus
	# (due to OpenBTS's inability to handle the + symbol).
        if (to_country):
            to = vbts_util.convert_to_e164(to, to_country)
        if (from_country):
            from_ = vbts_util.convert_to_e164(from_, from_country)
        to = vbts_util.strip_number(to)
        from_ = vbts_util.strip_number(from_)
        return self._send_raw_to_freeswitch(to, from_, body)
