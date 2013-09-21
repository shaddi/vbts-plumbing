#!/usr/bin/python
import threading
import traceback

import web
import requests

import syslog

import vbts_interconnects
from vbts_interconnects import vbts_twilio, vbts_voipms, vbts_util, vbts_fs, vbts_nexmo

from libvbts import Messenger

import vbts_credit

urls = ("/twilio_sms", "twilio_sms",
        "/nexmo_sms", "nexmo_sms",
        "/nexmo_delivery", "nexmo_delivery",
        "/out_twilio_sms", "out_twilio_sms",
        "/out_nexmo_sms", "out_nexmo_sms",
        "/twilio_registration", "twilio_registration",
        "/voipms_registration", "voipms_registration",
        "/nexmo_registration", "nexmo_registration")

class registration:
    """
    Class for doing registration. POST request fires off a registration worker,
    which does allocates a new number, registers the phone, then sends the
    phone an SMS with the number.
    """
    def __init__(self):
        self.ic = None
        self.conf = vbts_util.get_conf_dict()
        self.worker = self.registration_worker
        self.fs_ic = vbts_fs.freeswitch_ic(self.conf)

    def registration_worker(self, from_name, ip, port, ret_num):
        try:
            number = self.ic.get_next_avail_number()
            if number:
                # register the user
                vbts_util.messenger.SR_provision(from_name, number, ip, port)
                self.fs_ic._send_raw_to_freeswitch(number, ret_num, "Your number is %s" % number)
                vbts_credit.log_credit(from_name, 0, 0, "Provisioned user %s number %s" % (from_name, number))
            else:
                # send failed message
                # TODO: how to send an SMS with no number provisioned??
                syslog.syslog("VBTS Failed to provision user %s" % from_name)
        except Exception as e:
            syslog.syslog("VBTS " + traceback.format_exc(e))

    def POST(self):
        data = web.input()
        needed_fields = ["from_name", "ip", "port", "ret_num"]
        if all(i in data for i in needed_fields):
            from_name = str(data.from_name)
            ip =  str(data.ip)
            port = str(data.port)
            ret_num = str(data.ret_num)
            t = threading.Thread(target=self.worker, kwargs={"from_name": from_name, "ip": ip, "port": port, "ret_num": ret_num})
            t.start()
            raise web.Accepted()
        else:
            raise web.NotFound()

class twilio_registration(registration):

    def __init__(self):
        registration.__init__(self)
        self.ic = vbts_twilio.twilio_ic(self.conf)

class voipms_registration(registration):

    def __init__(self):
        registration.__init__(self)
        self.ic = vbts_voipms.voipms_ic(self.conf)

class nexmo_registration(registration):

    def __init__(self):
        registration.__init__(self)
        self.ic = vbts_nexmo.nexmo_ic(self.conf)

class incoming_sms:

    def __init__(self):
        self.conf = vbts_util.get_conf_dict()
        self.fs_ic = vbts_fs.freeswitch_ic(self.conf)
        self.tariff_type = "incoming_sms"

    def bill(self, to, from_):
        syslog.syslog("VBTS " + to + " " + from_)
        try:
            tariff = vbts_credit.sms_cost(self.tariff_type)
            username = vbts_util.messenger.SR_dialdata_get("dial", ("exten", to))
            if (username and username != ""):
                vbts_credit.deduct(tariff, username, "Incoming SMS from %s to %s at %s" % (from_, to, self.tariff_type))
        except Exception as e:
            syslog.syslog("VBTS " + traceback.format_exc(e))


class twilio_sms(incoming_sms):
    """
    Class for handling incoming messages from Twilio.
    """
    def __init__(self):
        incoming_sms.__init__(self)

    def POST(self):
        data = web.input()
        needed_fields = ["Body", "To", "From", "ToCountry", "FromCountry"]
        if all(i in data for i in needed_fields):
            to = str(data.To)
            toCountry =  str(data.ToCountry)
            from_ = str(data.From)
            fromCountry = str(data.FromCountry)
            body = str(data.Body)
            self.fs_ic.send(to, from_, body, to_country=toCountry, from_country=fromCountry)
            self.bill(to, from_)
            web.header('Content-Type', 'text/xml')
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
        else:
            raise web.NotFound()

class nexmo_sms(incoming_sms):
    """
    Class for handling incoming messages from Nexmo.
    """
    def __init__(self):
        incoming_sms.__init__(self)

    def GET(self):
        data = web.input()
        needed_fields = ["text", "to", "msisdn"]
        if all(i in data for i in needed_fields):
            to = str(data.to)
            from_ = str(data.msisdn)
            body = str(data.text)
            self.fs_ic.send(to, from_, body)
            self.bill(to, from_)
            return web.ok
        else:
            return web.badrequest

class nexmo_delivery(incoming_sms):
    """
    Class for handling delivery receipts from Nexmo.
    """
    def __init__(self):
        incoming_sms.__init__(self)
        self.m = Messenger.Messenger()

    def GET(self):
        try:
            self.GET_fake()
        except Exception as e:
            syslog.syslog("VBTS " + traceback.format_exc(e))

    def GET_fake(self):
        data = web.input()
        needed_fields = ["status", "to", "msisdn"]
        if all(i in data for i in needed_fields):
            to = str(data.to)
            from_ = str(data.msisdn)
            status = str(data.status)
            if (self.m.SR_get("delivery_receipt", ("callerid", to)) != "yes"):
                pass
            elif (status == "delivered"):
                self.fs_ic.send(to, "101", "Message has been received by %s" % from_)
            elif (status == "accepted"):
                self.fs_ic.send(to, "101", "Message has been received by the service provider for %s" % from_)
            return web.ok
        else:
            return web.badrequest


class out_sms:

    """
    Class for handling outgoing messages, needed due to poor chatplan
    performance. We accept a request, return 202 Accepted immediately, then
    fire off a thread that does the actual request and issues the
    billing request if appropriate.
    """

    def __init__(self):
        self.conf = vbts_util.get_conf_dict()
        self.worker = self.sms_worker

    def POST(self):
        data = web.input()
        needed_fields = ["to", "from_number", "from_name", "body", "service_type"]
        if all(i in data for i in needed_fields):
            to = str(data.to)
            from_number = str(data.from_number)
            from_name = str(data.from_name)
            body = str(data.body)
            service_type = str(data.service_type)
            t = threading.Thread(target=self.worker, kwargs={"to": to, "from_num": from_number, "from_name": from_name, "body": body, "service_type": service_type})
            t.start()
            raise web.Accepted()
        else:
            raise web.NotFound()

    #default SMS worker thread
    def sms_worker(self, to, from_num, from_name, body, service_type):
        try:
            if self.ic.send(to, from_num, body):
                billing_url = self.conf['billing_url']
                requests.post(billing_url, data={"from_name": from_name, "destination": to, "service_type": service_type})
        except Exception as e:
            syslog.syslog("VBTS " + traceback.format_exc(e))


class out_twilio_sms(out_sms):

    def __init__(self):
        out_sms.__init__(self)
        self.ic = vbts_twilio.twilio_ic(self.conf)

class out_nexmo_sms(out_sms):

    def __init__(self):
        out_sms.__init__(self)
        self.ic = vbts_nexmo.nexmo_ic(self.conf)

app = web.application(urls, locals())

if __name__ == "__main__":
    app.run()
