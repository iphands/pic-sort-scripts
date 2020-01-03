import os
import shutil
import hashlib
import re
from exif import Image
from datetime import datetime
from datetime import timedelta

class BadCzoomMatch(Exception): pass

# dt = datetime.fromtimestamp(int(unix_stamp))

# CameraZOOM-20160114233054379.jpg
czoom = re.compile('.*CameraZOOM-([0-9]{14}).*jpg')
czoom_24 = re.compile('([0-9]{8}([0-9]{2}))')

def try_czoom_fix(s):
    m = czoom_24.match(s)
    if m.group(2) == "24":
        new = m.group(1)[:-2] + "23"
        s   = s.replace(m.group(1), new)
        return (s, True)
    return (s, False)

def handle_czoom(f, stamp):
    stamp, fix = try_czoom_fix(stamp)
    dt = datetime.strptime(stamp, '%Y%m%d%H%M%S')
    if fix: dt = dt + timedelta(hours=1)

    with open(f, 'rb') as image_file:
        my_image = Image(image_file)
        print(dir(my_image))
        print(my_image['datetime'])
    print(dt)

def tryfile(f):
    res = czoom.match(f)
    if not res: raise BadCzoomMatch
    if len(res.groups()) < 1: raise BadCzoomMatch
    handle_czoom(f, res.group(1))

with open('noexif.list.txt', 'r') as lst:
    line = lst.readline().strip()
    while line:
        if len(line) > 4:
            # print('DEBUG: ' + line, flush=True)
            try:
                tryfile(line)
            except Exception as e:
                print("FAIL(" + type(e).__name__ + "): " + line + " " + str(e))
        line = lst.readline().strip()
