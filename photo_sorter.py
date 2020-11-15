#!/usr/bin/python
# Sort photo folder out

import os
import time
import string
import shutil
import pyexiv2
import datetime

base_path = '/mnt/Files/Google Drive/Photos/test'


def find_photos(dir):
    result = []
    #print "Files in ", os.path.abspath(dir), ": "
    for item in os.listdir(dir):
        if os.path.isfile(os.path.join(dir, item)):
            result.append(os.path.join(dir, item))
        else:
            result.extend(find_photos(os.path.join(dir, item)))
    return result


def kill_dead_folders(dir):
    if not os.listdir(dir):
        os.rmdir(dir)
        print 'Deleted %s' % dir
    else:
        for item in os.listdir(dir):
            if os.path.isdir(os.path.join(dir, item)):
                kill_dead_folders(os.path.join(dir, item))


def main():
    photos = find_photos(base_path)
    for item in photos:
        root, file_ext = os.path.splitext(item)
        if file_ext in ('.ini', '.py', '.db'):
            continue
        #print item
        if 'Misc' in item:
            item_bits = item.replace(base_path, '').split('/')
            newitem_bits = item_bits[0], '/', '-'.join(item_bits[1:])
        else:
            item_bits = item.replace(base_path, '').split('/')
            newitem_bits = item_bits[0], '/', item_bits[1], '/', '-'.join(item_bits[2:])
        newitem = ''.join(newitem_bits)
        newitem = base_path + newitem

        found_time = False
        if file_ext is '.jpg':
            img = pyexiv2.Image(item)
            img.readMetadata()
            #print img.exifKeys()
            if 'Exif.Photo.DateTimeOriginal' in img.exifKeys():
                #print img['Exif.Photo.DateTimeOriginal']
                new_date_time = img['Exif.Photo.DateTimeOriginal']
                found_time = True
            elif 'Exif.Image.DateTime' in img.exifKeys():
                #print img['Exif.Image.DateTime']
                new_date_time = img['Exif.Photo.DateTime']
                found_time = True
            else:
                print 'DateTime tag not found ------------------------------------------------------------'
                new_date_time = ''
            if new_date_time != '':
                date_time_name = string.replace(str(new_date_time), ':', '-')
                date_time_name = date_time_name.replace(' ', '-')
                newitem = base_path + '/' + date_time_name
        if not found_time:
            '''Get time from file ctime'''
            date_time = datetime.datetime.fromtimestamp(os.path.getctime(item))
            date_time = str(date_time).split('.', 1)[0]
            date_time = string.replace(str(date_time), ':', '-')
            date_time = string.replace(str(date_time), ' ', '-')
            newitem = base_path + '/' + date_time

        suffix_num = 1
        while os.path.exists(newitem + file_ext):
            suffix_num += 1
            newitem = base_path + '/' + date_time + '_' + str(suffix_num)

        print item, '->', newitem
        if 'Thumbs.db' in item:
            os.remove(item)
        else:
            if os.path.exists(newitem + file_ext):
                print 'err'
            else:
                # shutil.copy2(item, newitem + file_ext)
                os.rename(item, newitem + file_ext)

    kill_dead_folders(base_path)


if __name__ == "__main__":
    main()
