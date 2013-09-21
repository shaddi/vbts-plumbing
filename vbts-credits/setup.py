from distutils.core import setup, Extension

data_files = [('/etc/lighttpd/conf-enabled/', ['data/10-cdr-server-fastcgi.conf']),
              ('/usr/local/freeswitch/scripts/', ['data/VBTS_Get_Service_Tariff.py']),
              ('/usr/local/freeswitch/scripts/', ['data/VBTS_Transfer_Credit.py'])]

try:
    f = open("/etc/vbts_credit.conf")
except:
    data_files.append(('/etc/', ['data/vbts_credit.conf']))

setup(name="vbts_credits",
      version="0.0.2",
      description="Credits system for VBTS",
      author="Shaddi Hasan",
      author_email="shaddi@cs.berkeley.edu",
      url="http://cs.berkeley.edu/~shaddi",
      license='bsd',
      py_modules=['vbts_credit', 'vbts_credit_transfer'],
      scripts=['scripts/cdr-server.py',
               'scripts/vbts_credit_cli',
               'scripts/credits_log_restore.py',
               'scripts/credits_report.py'],
      data_files=data_files
)
