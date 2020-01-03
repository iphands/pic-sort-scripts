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
czoom    = re.compile('.*CameraZOOM-([0-9]{14}).*jpg')
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


# /1463171219540.jpg
unixlike = re.compile('.*/(1[3-4][0-9]{8})[0-9]*.*jpg', re.IGNORECASE)
def try_unixlike(f):
    res = unixlike.match(f)
    if res:
        write_file(datetime.fromtimestamp(int(res.group(1))), f)
        return True
    return False

# /FB_IMG_1442980032538.jpg
fbre = re.compile('.*/FB_IMG_(1[3-4][0-9]{8})[0-9]*.*jpg', re.IGNORECASE)
def try_fb(f):
    res = fbre.match(f)
    if res:
        write_file(datetime.fromtimestamp(int(res.group(1))), f)
        return True
    return False

# /2010-01-28-174545.jpg
webcamre = re.compile('.*/(2[0-9]{3}-[0-9]{2}-[0-9]{2}-[0-9]{6}).*jpg', re.IGNORECASE)
def try_webcam_date(f):
    res = webcamre.match(f)
    if res:
        dt = datetime.strptime(res.group(1), '%Y-%m-%d-%H%M%S')
        write_file(dt, f)
        return True
    return False

# /IMG_20130405_195524.jpg
imgre = re.compile('.*([0-9]{8}_[0-9]{6}).*jpg', re.IGNORECASE)
def try_img_date(f):
    res = imgre.match(f)
    if res:
        dt = datetime.strptime(res.group(1), '%Y%m%d_%H%M%S')
        write_file(dt, f)
        return True
    return False

# /mnt/nas/pics/old/sorted/2015/12/BABY ADRIAN_45.JPG
sortedre = re.compile('.*/([0-9]{4}/[0-9]{2}).*jpg', re.IGNORECASE)
def try_folder(f):
    res = sortedre.match(f)
    if res:
        dt = datetime.strptime(res.group(1), '%Y/%m')
        write_file(dt, f)
        return True
    return False

def write_file(dt, f):
        command = 'exiv2 -M "set Exif.Image.DateTime ' + dt.strftime("%Y:%m:%d %H:%M:%S") + '" "' + f + '"'
        print(f)
        # print(command)
        # os.system(command)

def tryfile(f):
    if try_unixlike(f): return
    if try_fb(f): return
    if try_webcam_date(f): return
    if try_img_date(f): return
    if try_folder(f): return

with open('tmp/all', 'r') as lst:
    line = lst.readline().strip()
    while line:
        if len(line) > 4:
            # print('DEBUG: ' + line, flush=True)
            try:
                tryfile(line)
            except Exception as e:
                print("FAIL(" + type(e).__name__ + "): " + line + " " + str(e))
                raise e
        line = lst.readline().strip()
