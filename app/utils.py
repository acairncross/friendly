import datetime
import hashlib
import hmac
import json
import random
import re
import string

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

def get_now():
    return datetime.datetime.utcnow()

def shuffle(l):
    random.shuffle(l)

def generate_salt():
    return ''.join([random.choice(string.ascii_uppercase) for i in range(10)])

def generate_hash(password, salt):
    return hmac.new(salt, password, hashlib.sha256).hexdigest()

def is_alnum_or_underscore(s):
    return True if re.match('^[a-zA-Z0-9_]$', s) else False
