import os
import shutil
import hashlib
import exifread
from exif import Image

class NoExif(Exception): pass
class NoDateTime(Exception): pass

def md5(fname):
    with open(fname, 'rb') as f:
        hash_md5 = hashlib.md5()
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
        return hash_md5.hexdigest()

def try_gps_date(img):
    if 'gps_datestamp' in dir(img):
        dt = img['gps_datestamp'].split(':')
        data = {
            "year":  dt[0],
            "month": dt[1],
            "day":   dt[2],
            "hour":  "00",
            "min":   "00",
            "sec":   "00"
        }
        return data
    return False

def try_datetime(img, key):
    # if key in dir(img):
    dt   = img[key].split(':')
    data = {
        "year":  dt[0],
        "month": dt[1],
        "day":   dt[2].split(' ')[0],
        "hour":  dt[2].split(' ')[1],
        "min":   dt[3],
        "sec":   dt[4]
    }
    return data
    # return False

def dofile(f):
    with open(f, 'rb') as image_file:
        my_image = Image(image_file)

        if not my_image.has_exif: raise NoExif()

        data = try_gps_date(my_image)
        if not data: data = try_datetime(my_image, 'datetime_original')
        if not data: data = try_datetime(my_image, 'datetime')
        if not data: raise NoDateTime()

        directory = '../sorted/' + data['year'] + '/' + data['month'] + '/' + data['day']
        if not os.path.exists(directory):
            os.makedirs(directory)

        if (DRY):
            newpath = directory + '/' + data['hour'] + data['min'] + data['sec'] + '-md5sum.jpg'
            print('would move: {} -> {}'.format(f, newpath))
            print('PASS: ' + f)
            return

        md5sum  = md5(f)
        newpath = directory + '/' + data['hour'] + data['min'] + data['sec'] + '-' + md5sum + '.jpg'

        if not os.path.exists(newpath):
            # shutil.move(f, newpath)
            print('PASS: ' + f)
        else:
            print('DUP:  ' + f)

def docrtwo(f):
    with open(f, 'rb') as fil:
        tags = exifread.process_file(fil)

        if 'EXIF DateTimeOriginal' not in tags:
            print("SKIP (no EXIF DateTimeOriginal): " + f)
            print(tags.keys())
            asfd()
            return

        datetime = tags['EXIF DateTimeOriginal']
        data = try_datetime({'test': str(datetime)}, 'test')

        directory = '../sorted/' + data['year'] + '/' + data['month'] + '/' + data['day']
        if not os.path.exists(directory):
            os.makedirs(directory)

        has_xmp = False
        xmp_f = f + '.xmp'
        if os.path.exists(xmp_f):
            has_xmp = True

        md5sum  = md5(f)
        newpath = directory + '/' + data['hour'] + data['min'] + data['sec'] + '-' + md5sum + '.CR2'
        xmp_newpath = newpath + '.xmp'

        if (DRY):
            print('would move: {} -> {}'.format(f, newpath))
            if has_xmp:
                print('would move: {} -> {}'.format(xmp_f, xmp_newpath))
            print('PASS: ' + f)
            return

        if not os.path.exists(newpath):
            shutil.move(f, newpath)
            if has_xmp:
                shutil.move(xmp_f, xmp_newpath)
            print('Moved {} -> {}:'.format(f, newpath))
        else:
            print('Skipped:  ' + f)


DRY=False
with open('/tmp/tmp.list', 'r') as lst:
    line = lst.readline().strip()
    while line:
        # print('DEBUG: ' + line, flush=True)
        if len(line) > 4:
            try:
                if line.endswith('CR2'):
                    docrtwo(line)
                else:
                    dofile(line)
            except Exception as e:
                print("FAIL(" + type(e).__name__ + "): " + line)
                raise e
        line = lst.readline().strip()
