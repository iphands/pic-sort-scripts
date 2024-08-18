import sys
import os
import shutil
import hashlib
import exifread
from exif import Image

class NoExif(Exception): pass
class NoDateTime(Exception): pass

DRY=False

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

def _get_data_norm(image_file):
    my_image = Image(image_file)

    if not my_image.has_exif: raise NoExif()

    data = try_gps_date(my_image)
    if not data: data = try_datetime(my_image, 'datetime_original')
    if not data: data = try_datetime(my_image, 'datetime')
    if not data: raise NoDateTime()
    return data

def _get_data_crtwo(fil):
    tags = exifread.process_file(fil)

    if 'EXIF DateTimeOriginal' not in tags:
        print("SKIP (no EXIF DateTimeOriginal): " + f)
        print(tags.keys())
        asfd()
        return

    datetime = tags['EXIF DateTimeOriginal']
    data = try_datetime({'test': str(datetime)}, 'test')
    return data


def dofile(f, crtwo=False):
    with open(f, 'rb') as image_file:
        data = {}
        suff = 'jpg'
        if crtwo:
            suff = 'CR2'

        if not crtwo:
            data = _get_data_norm(image_file)
        else:
            data = _get_data_crtwo(image_file)

        directory = f'../sorted/{data["year"]}/{data["month"]}/{data["day"]}'
        if not os.path.exists(directory):
            os.makedirs(directory)

        has_xmp = False
        xmp_f = f + '.xmp'
        if os.path.exists(xmp_f):
            has_xmp = True

        md5sum  = md5(f)
        newpath = f'{directory}/{data["hour"]}{data["min"]}{data["sec"]}-{md5sum}.{suff}'
        xmp_newpath = newpath + '.xmp'

        prefix = ''
        if DRY:
            prefix = '[dry] '

        # Dupe found
        if os.path.exists(newpath):
            print(f'{prefix}Skipped: {f} -> {newpath}')
            return

        # Do move if not dry
        if not DRY:
            shutil.copy(f, newpath)
            if has_xmp:
                shutil.copy(xmp_f, xmp_newpath)
        print(f'{prefix}Moved:   {f} -> {newpath}')


def main():
    global DRY
    if len(sys.argv) == 2 and sys.argv[1] == "--dry":
        DRY = True

    with open('/tmp/tmp.list', 'r') as lst:
        line = lst.readline().strip()
        while line:
            # print('DEBUG: ' + line, flush=True)
            if len(line) > 4:
                try:
                    dofile(line, crtwo=line.endswith('CR2'))
                except Exception as e:
                    print("FAIL(" + type(e).__name__ + "): " + line)
                    raise e
            line = lst.readline().strip()

if __name__ == '__main__':
    main()
