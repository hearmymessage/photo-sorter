#!/usr/bin/python
# Sort photo folder out

import argparse
import datetime
import logging
import os
import pyexiv2
import shutil
import time

VALID_YEARS = range(2003, int(time.strftime('%Y')) + 1)
VALID_MONTHS = range(1, 12 + 1)

VALID_EXTENSIONS = ['.jpg', '.heic', '.mov', '.mp4', '.png']


def get_jpg_time(jpg_file):
    exif_dict = {}
    xmp_dict = {}
    iptc_dict = {}
    new_date_time = ''
    try:
        with pyexiv2.Image(jpg_file) as img:
            exif_dict = img.read_exif()
    except RuntimeError as e:
        logging.warn('RuntimeError reading EXIF data: {}'.format(e))
    except UnicodeDecodeError as e:
        logging.warn('UnicodeDecodeError reading EXIF data: {}'.format(e))

    try:
        with pyexiv2.Image(jpg_file) as img:
            xmp_dict = img.read_xmp()
    except RuntimeError as e:
        logging.warn('RuntimeError reading XMP data: {}'.format(e))

    try:
        with pyexiv2.Image(jpg_file) as img:
            iptc_dict = img.read_iptc()
    except RuntimeError as e:
        logging.warn('RuntimeError reading IPTC data: {}'.format(e))
    except UnboundLocalError as e:
        logging.warn('UnboundLocalError reading IPTC data: {}'.format(e))

    if len(exif_dict) != 0:
        if 'Exif.Photo.DateTimeOriginal' in exif_dict.keys():
            new_date_time = exif_dict['Exif.Photo.DateTimeOriginal']
            logging.debug(
                'DateTimeOriginal tag found: {}'.format(new_date_time))
        elif 'Exif.Image.DateTimeOriginal' in exif_dict.keys():
            new_date_time = exif_dict['Exif.Image.DateTimeOriginal']
            logging.debug(
                'DateTimeOriginal tag found: {}'.format(new_date_time))
        elif 'Exif.Image.DateTime' in exif_dict.keys():
            new_date_time = exif_dict['Exif.Image.DateTime']
            logging.debug('DateTime tag found: {}'.format(new_date_time))
        elif 'Exif.Photo.DateTime' in exif_dict.keys():
            new_date_time = exif_dict['Exif.Photo.DateTime']
            logging.debug('DateTime tag found: {}'.format(new_date_time))
        else:
            logging.debug(
                'Exif present but DateTime tag not found -------------------------------------------------'
            )
            logging.debug(exif_dict)

    elif len(xmp_dict) != 0:
        logging.debug("XMP read: {}".format(xmp_dict))

    elif len(iptc_dict) != 0:
        logging.debug("IPTC read: {}".format(iptc_dict))

    if new_date_time != '':
        try:
            date_time = datetime.datetime.strptime(new_date_time,
                                                   '%Y:%m:%d %H:%M:%S')
        except ValueError:
            pass
        except TypeError as e:
            logging.warn(
                'TypeError trying to parse EXIF datetime: {} ({} from {})'.format(
                    e, new_date_time, jpg_file))
            date_time = datetime.datetime.strptime(new_date_time[1],
                                                   '%Y:%m:%d %H:%M:%S')
            logging.info('Timestamp from metadata: {} ({})'.format(
                date_time, new_date_time))
            return date_time
        else:
            logging.info('Timestamp from metadata: {} ({})'.format(
                date_time, new_date_time))
            return date_time

        try:
            date_time = datetime.datetime.strptime(new_date_time,
                                                   '%Y/%m/%d %H:%M:%S')
        except ValueError:
            pass
        else:
            logging.info('Timestamp from metadata: {} ({})'.format(
                date_time, new_date_time))
            return date_time

    # If those haven't worked, get time from file ctime
    date_time = datetime.datetime.fromtimestamp(os.path.getctime(jpg_file))
    logging.info('Timestamp from file (created): {}'.format(date_time))

    return date_time


def generate_path(lib_dir, item_path, out_dir, date_time):
    logging.debug("File: {}".format(item_path))
    root, file_ext = os.path.splitext(item_path)
    date_time_str = datetime.datetime.strftime(date_time, '%Y_%m_%d %H_%M_%S')
    year_str = datetime.datetime.strftime(date_time, '%Y')
    month_str = datetime.datetime.strftime(date_time, '%m')
    item_bits = item_path.replace(lib_dir + '\\', '').split('\\')
    logging.debug('Item bits: {}'.format(item_bits))
    if len(item_bits[1:-1]) != 0:
        if item_bits[0] == year_str:
            newitem_bits = [
                year_str, '/', month_str, '/', date_time_str, ' ',
                '-'.join(item_bits[1:-1]), file_ext
            ]
        else:
            newitem_bits = [
                year_str, '/', month_str, '/', date_time_str, ' ',
                '-'.join(item_bits[0:-1]), file_ext
            ]
    else:
        if item_bits[0].startswith(year_str):
            newitem_bits = [
                year_str, '/', month_str, '/', date_time_str, file_ext
            ]
        else:
            newitem_bits = [
                year_str, '/', month_str, '/', date_time_str, ' ',
                item_bits[0], file_ext
            ]
    logging.debug('New item bits: {}'.format(newitem_bits))
    newitem = ''.join(newitem_bits)
    newitem = out_dir + '/' + newitem
    logging.debug("new item {}".format(newitem))
    return newitem


def rename_item(item, newitem, move, cut):
    suffix_num = 0
    root, file_ext = os.path.splitext(newitem)
    file_ext = file_ext.lower()
    newitem_test = root + file_ext
    while os.path.exists(newitem_test):
        suffix_num += 1
        newitem_test = root + '_' + str(suffix_num) + file_ext

    newitem = newitem_test

    logging.info('Item to rename/move:\n\t{}\nto\t{}'.format(item, newitem))

    if move:
        dir_path = os.path.dirname(newitem)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    if move and cut:
        os.rename(item, newitem)
    elif move and not cut:
        shutil.copy2(item, newitem)


def find_photos(lib_dir, curr_dir, out_dir, move, cut):
    '''
    lib_dir     base library directory
    curr_dir    current directory (used when recursing)
    out_dir     output directory (used for relocation items)
    '''
    logging.info("Files in {}:".format(os.path.abspath(curr_dir)))
    for item in os.listdir(curr_dir):
        item_path = os.path.join(curr_dir, item)
        if os.path.isfile(item_path):
            root, file_ext = os.path.splitext(item)
            if file_ext.lower() in VALID_EXTENSIONS:
                date_time = get_jpg_time(item_path)
                new_path = generate_path(lib_dir, item_path, out_dir,
                                         date_time)
                rename_item(item_path, new_path, move, cut)
        else:
            find_photos(lib_dir, os.path.join(curr_dir, item), out_dir, move,
                        cut)


def main():
    parser = argparse.ArgumentParser(description='Photo Sorter')
    parser.add_argument('--library',
                        '-l',
                        dest='library',
                        default='C:/Users/willj/OneDrive/Documents/code/'
                        'photo-sorter/test_library',
                        help='Path to the library to sort')
    parser.add_argument('--output',
                        '-o',
                        dest='output',
                        default='C:/Users/willj/OneDrive/Documents/code/'
                        'photo-sorter/output',
                        help='Path to the output directory')
    parser.add_argument('--move',
                        '-m',
                        dest='move',
                        action='store_true',
                        default=False,
                        help='Move the files')
    parser.add_argument('--cut',
                        '-x',
                        dest='cut',
                        action='store_true',
                        default=False,
                        help='Remove the files from the source directory')
    parser.add_argument('--verbose',
                        '-v',
                        dest='verbose',
                        action='store_true',
                        default=False,
                        help='Verbose messages')

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.warn(args)

    find_photos(args.library, args.library, args.output, args.move, args.cut)


if __name__ == "__main__":
    main()
