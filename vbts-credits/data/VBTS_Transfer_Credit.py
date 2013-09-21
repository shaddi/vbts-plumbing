from freeswitch import *

import vbts_credit_transfer

def chat(message, args):
    consoleLog('info', "Credit transfer: %s\n" % args)
    from_, request = args.split("|", 1)
    vbts_credit_transfer.handle_incoming(from_, request)

def fsapi(session, stream, env, args):
    chat(args)
