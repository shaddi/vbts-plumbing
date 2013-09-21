from distutils.core import setup, Extension

setup(name="vbts_twilio_sms",
      version="0.0.2",
      description="SMS integration for VBTS/Freeswitch, with both Twilio and Nexmo",
      author="Shaddi Hasan",
      author_email="shaddi@cs.berkeley.edu",
      url="http://cs.berkeley.edu/~shaddi",
      license='bsd',
      packages=['vbts_interconnects'],
      scripts=['scripts/twilio-sms-server.py'],
      data_files=[('/etc/', ['conf/vbts_twilio.conf']),
                  ('/etc/lighttpd/conf-enabled/', ['conf/10-twilio-server-fastcgi.conf']),
                  ('/usr/local/freeswitch/scripts', ['VBTS_Send_Twilio_SMS.py'])],
)
