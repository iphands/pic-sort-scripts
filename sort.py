import exifread
import ffmpeg
import hashlib
import json
import os
import shutil
import subprocess
import sys

from datetime import datetime
from exif import Image
from plum.exceptions import UnpackError

class NoDateTime(Exception): pass
class NoExif(Exception): pass
class NoValidDate(Exception): pass
class UnsupportedSuffix(Exception): pass

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
    if key not in img and not key in dir(img): return
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

def try_from_stat(img):
    stat = os.stat(img)
    dates = [
        datetime.fromtimestamp(stat.st_ctime),
        datetime.fromtimestamp(stat.st_mtime),
        datetime.fromtimestamp(stat.st_atime),
    ]
    dates = sorted(dates)
    date = None
    min_date = datetime(2001, 1, 1)
    for i in dates:
        if i > min_date:
            date = i
            break
    if date == None: raise NoValidDate(f"Cant find valid date in {img}: {dates}")
    return _data_from_datetime(str(date))

def _get_data_norm(f, image_file):
    try:
        my_image = Image(image_file)
    except UnpackError:
        data = try_from_stat(f)
        if not data: raise e
        return data

    if not my_image.has_exif:
        data = try_from_stat(f)
        if not data: raise NoExif()
        return data

    data = try_gps_date(my_image)
    if not data: data = try_datetime(my_image, 'datetime_original')
    if not data: data = try_datetime(my_image, 'datetime')
    if not data: data = try_from_stat(f)
    if not data: raise NoDateTime()
    return data

def _data_from_datetime(dt):
    dt = dt.split(".")[0]
    format_code = "%Y-%m-%d %H:%M:%S"
    if "T" in dt:
        format_code = "%Y-%m-%dT%H:%M:%S"
    parsed = datetime.strptime(dt, format_code)
    return {
        "year": str(parsed.year).zfill(4),
        "month": str(parsed.month).zfill(2),
        "day": str(parsed.day).zfill(2),
        "hour": str(parsed.hour).zfill(2),
        "min": str(parsed.minute).zfill(2),
        "sec": str(parsed.second).zfill(2),
    }

def _get_data_ffmpeg(fil):
    js = ffmpeg.probe(fil, show_entries='format')
    if 'format' in js:
        if 'tags' in js['format']:
            if 'creation_time' in js['format']['tags']:
                dt = js['format']['tags']['creation_time']
                return _data_from_datetime(dt)
    # print(json.dumps(js))
    data = try_from_stat(fil)
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

def _get_suffix(f):
    f = f.lower()
    if f.endswith('.jpg'):
        return "jpg"
    if f.endswith('.cr2'):
        return "CR2"
    if f.endswith('.3gp'):
        return "3gp"
    if f.endswith('.mp4'):
        return "mp4"
    if f.endswith('.mpg'):
        return "mpg"
    if f.endswith('.mov'):
        return "mov"
    if f.endswith('.tif'):
        return "tif"
    if f.endswith('.png'):
        return "png"
    raise UnsupportedSuffix()

def dofile(f):
    suff = _get_suffix(f)
    with open(f, 'rb') as image_file:
        data = {}

        if suff == "jpg":
            data = _get_data_norm(f, image_file)
        if suff == "tif":
            data = _get_data_norm(f, image_file)
        if suff == "png":
            data = _get_data_norm(f, image_file)
        elif suff == "CR2":
            data = _get_data_crtwo(image_file)
        elif suff == "3gp":
            data = _get_data_ffmpeg(f)
        elif suff == "mp4":
            data = _get_data_ffmpeg(f)
        elif suff == "mpg":
            data = _get_data_ffmpeg(f)
        elif suff == "mov":
            data = _get_data_ffmpeg(f)
        else:
            raise Exception(f"BUG: Matched suffix but missing impl! {suff}")

        if not data:
            raise Exception(f"BUG: Matched suffix, ran get_data but filed data == None: {f})")

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
            shutil.move(f, newpath)
            if has_xmp:
                shutil.move(xmp_f, xmp_newpath)
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
                    dofile(line)
                except (NoExif, NoDateTime, UnsupportedSuffix) as e:
                    if e != "":
                        print(f"FAIL({type(e).__name__}): {line}")
                    else:
                        print(f"FAIL({type(e).__name__}): {e}")
                except Exception as e:
                    print("FAIL(" + type(e).__name__ + "): " + line)
                    raise e
            line = lst.readline().strip()

if __name__ == '__main__':
    main()
