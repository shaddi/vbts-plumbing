from freeswitch import *

from vbts_interconnects import vbts_util, vbts_twilio

def usage():
    return "Usage: to|from|body\n"

def parse(args):
    args = args.split('|')
    if (len(args) < 3):
        consoleLog('err', "Missing args! %s" % usage())
        exit(1)
    to = args[0]
    from_ = args[1]
    body = args[2]
    if ((not to or to == '') or
        (not from_ or from_ == '')):
        consoleLog('err', "Malformed Args! %s" % usage())
        exit(1)
    return to, from_, body

def do_send(to, from_, body):
    # do the actual send
    conf = vbts_util.get_conf_dict()
    twilio_ic = vbts_twilio.twilio_ic(conf) 
    try:
        if twilio_ic.send(to, from_, body):
            return True
        else:
            return False
    except:
        return False

# DANGER ZONE: HACK HACK HACK
# Calling out to Twilio takes a long time, and it appears that doing calling
# this script as part of a condition hangs execution of the dialplan.  So, we
# moved the call to this script call to an action in the chatplan, but that
# doesn't allow us to decide whether or not to bill the user based on the
# result of the call. The solution is to have VBTS_Send_Twilio_SMS return the
# empty string on success, or '-h' on failure.  We pass this value as the first
# parameter to the billing cURL request (the second action). If it's first
# parameter is -h, it prints usage and exists; otherwise, it executes the
# billing request.
def chat(message, args):
    t, f, b = parse(args)
    res = "" if  do_send(t, f, b) else "-h"
    consoleLog('info', "Returned Chat: " + res + "\n")
    message.chat_execute('set', '_openbts_ret=%s' % res)

def fsapi(session, stream, env, args):
    t, f, b = parse(args)
    res = "" if  do_send(t, f, b) else "-h"
    consoleLog('info', "Returned FSAPI: " + res + "\n")
    stream.write(res)
