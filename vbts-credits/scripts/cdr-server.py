#!/usr/bin/python

import base64
import re
import sqlite3
import xml.dom.minidom as xml

import web

import vbts_credit

"""
HTTP server for processing CDRs sent from Freeswitch using mod_xml_cdr.

Receives CDRs from Freeswitch and updates subscriber registry accordingly.
"""

urls = ("/cdr", "cdr",
        "/smscdr", "smscdr")

def getText(nodelist):
    """ Get the text value of an XML tag (from the minidom doc)
    """
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

class smscdr(object):
    def GET(self):
        raise web.NotFound()

    def POST(self):
        data = web.input()
        if "from_name" in data and "service_type" in data and "destination" in data:
            self.process_smscdr(data.from_name, data.service_type, data.destination)
            raise web.OK

    def process_smscdr(self, from_, service_type, dest):
        cost_in_credits = vbts_credit.sms_cost(service_type)
        vbts_credit.deduct(int(cost_in_credits), from_, "SMS sent to %s at %s" % (dest, service_type))

class cdr(object):
    def GET(self):
        raise web.NotFound()

    def POST(self):
        data = web.input()
        if "cdr" in data:
            self.process_cdr(data.cdr)
            raise web.OK

    def process_cdr(self, cdr_xml):
        cdr_dom = xml.parseString(cdr_xml)
        #handle only b-legs for billing
        origin = cdr_dom.getElementsByTagName("origination")
        if (origin):
            return

        billsec = getText(cdr_dom.getElementsByTagName("billsec")[0].childNodes)
        caller = getText(cdr_dom.getElementsByTagName("username")[0].childNodes)
        if (caller[0] == '+'):
            caller = caller[1:]

        #in b-leg cdrs, there are multiple destinations
        #the sip one (IMSI) and the dialed one (MSISDN)
        #we want the latter
        callees = cdr_dom.getElementsByTagName("destination_number")
        callee = ''
        for c in callees:
            c = getText(c.childNodes)
            #NOT THE IMSI
            if (c[0:4] != "IMSI"):
                callee = c
                break

        if (callee[0] == "+"):
            callee = callee[1:]

        if len(cdr_dom.getElementsByTagName("service_type")) > 0:
            service_type = getText(cdr_dom.getElementsByTagName("service_type")[0].childNodes)
            rate = vbts_credit.get_service_tariff(service_type)
            cost = vbts_credit.call_cost(billsec, service_type)
            print "%s: %s sec @ %s R/min, %d" % (caller, billsec, rate, cost)
            vbts_credit.deduct(cost, caller, "%d sec call to %s at %s" % (int(billsec), callee, service_type))
        else:
            print "No rate info for this call. (from: %s, billsec: %s)" % (caller, billsec)

app = web.application(urls, locals())

if __name__ == "__main__":
    app.run()
