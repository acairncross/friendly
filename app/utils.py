import re
import datetime
import string
import random

def parseDatetime(dt):
    expr = re.compile(r'(?P<year>\d{4})/'
                      r'(?P<month>\d{2})/'
                      r'(?P<day>\d{2}) '
                      r'(?P<hour>\d{2}):'
                      r'(?P<minute>\d{2})')
    m = expr.match(dt)
    return datetime.datetime(int(m.group('year')),
                             int(m.group('month')),
                             int(m.group('day')),
                             int(m.group('hour')),
                             int(m.group('minute')))

def generate_uvc():
    return ''.join([random.choice(string.ascii_uppercase) for i in range(10)])
