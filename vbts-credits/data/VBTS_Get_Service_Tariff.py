from freeswitch import *

import vbts_credit

def chat(message, args):
    res = str(vbts_credit.get_service_tariff(str(args).strip()))
    consoleLog('info', "Returned Chat: " + res + "\n")
    message.chat_execute('set', 'service_type=%s' % res)

def fsapi(session, stream, env, args):
    res = str(vbts_credit.get_service_tariff(str(args).strip()))
    consoleLog('info', "Returned FSAPI: " + res + "\n")
    stream.write(res)
