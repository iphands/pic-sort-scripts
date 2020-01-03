import os
import shutil
import hashlib
from exif import Image

class NoExif(Exception): pass
class NoDateTime(Exception): pass

def md5(fname):
    with open(fname, 'rb') as f:
        hash_md5 = hashlib.md5()
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
        return hash_md5.hexdigest()

def dofile(f):
    with open(f, 'rb') as image_file:
        my_image = Image(image_file)

        if not my_image.has_exif: raise NoExif()
        if 'datetime' not in dir(my_image): raise NoDateTime()

        dt    = my_image['datetime'].split(':')
        year  = dt[0]
        month = dt[1]
        day   = dt[2].split(' ')[0]
        hour  = dt[2].split(' ')[1]
        mint  = dt[3]
        sec   = dt[4]

        directory = '../sorted/' + year + '/' + month + '/' + day
        if not os.path.exists(directory):
            os.makedirs(directory)


        if (DRY):
            newpath = directory + '/' + hour + mint + sec + '-md5sum.jpg'
            print('would move: {} -> {}'.format(f, newpath))
            print('PASS: ' + f)
            return

        md5sum  = md5(f)
        newpath = directory + '/' + hour + mint + sec + '-' + md5sum + '.jpg'

        if not os.path.exists(newpath):
            shutil.move(f, newpath)
            print('PASS: ' + f)
        else:
            print('DUP:  ' + f)

DRY=False
with open('./tmp/test', 'r') as lst:
    line = lst.readline().strip()
    while line:
        print('DEBUG: ' + line, flush=True)
        if len(line) > 4:
            try:
                dofile(line)
            except Exception as e:
                print("FAIL(" + type(e).__name__ + "): " + line)
        line = lst.readline().strip()
