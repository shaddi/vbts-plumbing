import sqlite3
import random
import re
import time

from libvbts import FreeSwitchMessenger
from freeswitch import *
import vbts_credit

conf = vbts_credit.conf
pending_db = conf['pending_transfer_db']
app_number = conf['app_number']
fsm = FreeSwitchMessenger.FreeSwitchMessenger()

"""
The logic for the credit transfer SMS app.
"""

code_length = int(conf['code_length'])

# regex to match transfer requests
transfer_command = re.compile('^(?P<to_number>[0-9]*)\*(?P<amount>[0-9]*)$')
# regex to match confirmation codes
confirm_command = re.compile('^(?P<confirm_code>[0-9]{%d})$' % code_length)

def _init_db():
    db_create_str = "CREATE TABLE pending_transfers (code VARCHAR(5) PRIMARY KEY, time FLOAT, from_acct INTEGER, to_acct INTEGER, amount INTEGER);"
    try:
        with open(pending_db) as f:
            pass
    except IOError as e:
        import os
        db = sqlite3.connect(pending_db)
        db.execute(db_create_str)
        db.commit()
        db.close()
        os.chmod(pending_db, 0777) # make it world writable...

def _send_to_freeswitch(to, body):
    to = vbts_credit._number_from_name(to)
    if to:
        fsm.send_smqueue_sms("", str(to), str(app_number), str(body), False)
        return True # TODO return something more sensible
    return False

def process_transfer(from_, to, amount):
    from_balance = vbts_credit.get(from_)
    consoleLog('info', "KURTIS|" + str(from_) + ":" +  str(from_balance) + "\n")
    if not from_balance or from_balance < amount:
        return False, conf['no_credit']
    if not to or vbts_credit.get(to) == None: # could be 0! Need to check if doesn't exist.
        return False, conf["wrong_number"]

    # add the pending transfer
    code = ''
    for r in range(code_length):
        code += str(random.randint(0,9))
    db = sqlite3.connect(pending_db)
    db.execute("INSERT INTO pending_transfers VALUES (?, ?, ?, ?, ?)", (code, time.time(), from_, to, amount))
    db.commit()
    db.close()

    to_num = vbts_credit._number_from_name(to)
    response = conf["reply_with_code"] % (str(code), str(amount), str(to_num))
    return True, response

def process_confirm(from_, code):
    # step one: delete all the old confirm codes
    db = sqlite3.connect(pending_db)
    db.execute("DELETE FROM pending_transfers WHERE time - ? > 600", (time.time(),))
    db.commit()

    # step two: check if this (from, code) combo is valid.
    r = db.execute("SELECT from_acct, to_acct, amount FROM pending_transfers WHERE code=? AND from_acct=?", (code, from_))
    res = r.fetchone()
    if res and len(res) == 3:
        from_acct, to_acct, amount = res
        from_num = vbts_credit._number_from_name(from_acct)
        to_num = vbts_credit._number_from_name(to_acct)
        reason = "SMS transfer from %s to %s" % (from_num, to_num)
        consoleLog('info', "KURTIS|" + str(reason) + "\n")
        vbts_credit.transfer(int(amount), from_acct, to_acct, reason)
        new_from_balance = vbts_credit.get(from_acct)
        new_to_balance = vbts_credit.get(to_acct)

        # let the recipient know they got credit
        resp = conf["received"] % (amount, from_num, new_to_balance)
        db.execute("DELETE FROM pending_transfers WHERE code=? AND from_acct=?", (code, from_))
        db.commit()
        _send_to_freeswitch(to=to_num, body=resp)

        return True, conf['confirm'] % (amount, to_num, new_from_balance)
    return False, conf["code_fail"]

def handle_incoming(from_, request):
    """
    Called externally. Should pass a from number and a request.
    """
    request = request.strip()
    transfer = transfer_command.match(request)
    confirm = confirm_command.match(request)
    consoleLog('info', "KURTIS|" + from_ + "|" + request + "|" + str(transfer) + "|" + str(confirm) + "\n")
    _init_db() # check if the db exists and create it if it doesn't
    if transfer:
        to, amount = transfer.groups()
        amount = int(amount)
        # translate everything into names
        to = vbts_credit._name_from_number(to)
        from_ = vbts_credit._name_from_number(from_)
        res, resp = process_transfer(from_, to, amount)
    elif confirm:
        # code is the whole thing, so no need for groups
        code = request.strip()
        from_ = vbts_credit._name_from_number(from_)
        res, resp = process_confirm(from_, code)
    else:
        res, resp = False, conf['bad_format']
    consoleLog('info', "Sending to " + str(from_) + ":" + str(resp) + "\n")
    _send_to_freeswitch(to=from_, body=resp)
