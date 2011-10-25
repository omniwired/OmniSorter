#!/usr/bin/python
# -*- coding: utf-8 *-*

import os
import shutil
import re
import sys
import time

# no detecta .AVI el missing finder

__DIRECTORY_TO_WORK_WITH__ = "/home/omniwired/Downloads"
__EXTENSIONS_TO_LOOK_FOR__ = [".avi", ".mkv"]  # sin uso
__SERIES_TO_LOOK_FOR__ = ['The big bang theory', 'Fringe']  # sin uso
target = __DIRECTORY_TO_WORK_WITH__ + "/Videos"
config_file = os.path.join(sys.path[0], "series.conf")  # os.getcwd()

mode = len(sys.argv)


def md5_file(fileName,block_size=2**20):
    import hashlib
    f = open(fileName,'rb')
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()


def get_series_list():

    f = open(config_file, 'r')
    col_series = []

    for line in f:
        conf_serie = line.split(":")
        conf_serie[1] = conf_serie[1].replace("\n", "")  # removes the \n
        col_series.append(conf_serie)
    return col_series

special_series_list = get_series_list()


def normalize(str):

    str = str.replace(".", " ")
    str = str.replace(" - ", "")
    str = str.title()
    if str.endswith(" "):
        str = str[:-1]
    return str


def automatic_behaviour():

    a = process_series(__DIRECTORY_TO_WORK_WITH__, 0)
    move_to_target(a, target, 0)


def process_series(__DIRECTORY_TO_WORK_WITH__, verbose):

    col_findings = []
    total_size = 0
    for root, dirs, files in os.walk(__DIRECTORY_TO_WORK_WITH__):
#        if 'Videos' in dirs:
#            dirs.remove('Videos')  # don't visit Videos directories
        for item in files:
            if item.endswith(".avi") or item.endswith(".mkv"):
                match = re.search('(?=[S-s][0-9][0-9][E-e][0-9][0-9])\w+', item)
                fullpath = os.path.join(root, item)
                if match is not None:
                    if verbose is 1:
                        size = os.path.getsize(fullpath) / 1024 / 1024
                        print "Processsing " + item, size, "MB"
                        total_size += size

                    donde_cortar = match.span()
                    info_episodio = item[donde_cortar[0]:donde_cortar[1]]
                    serie = normalize(item[:donde_cortar[0]])
                    season = info_episodio[1:3]
                    col_findings.append([serie, info_episodio, fullpath, root, season, item])
    if verbose is 1:
        print "Processed", total_size / 1024, "Gb"
    return col_findings


def freespace(p):
    """
    Returns the number of free bytes on the drive that ``p`` is on
    """
    s = os.statvfs(p)
    return s.f_bsize * s.f_bavail


def move_to_target(col_findings, target, verbose):

    MB_moved = 0
    start_time = time.time()
    if not os.path.isdir(target):
        if verbose is 1:
            print "Creating " + target
        os.mkdir(target)
    for x in col_findings:
        # ex ['The IT Crowd', 'S04E03', fullpath, root, season_number, filename]
        serie = os.path.join(target, x[0])
        fullpath = x[2]
        root = x[3]
        temporada = x[4]
        filename = x[5]

        # Special Cases
        for serie_from_conf in special_series_list:
            if x[0].lower() == serie_from_conf[0].lower():
                if not os.path.isdir(serie_from_conf[1]):  # special check for external drives
                    serie = os.path.join(target, x[0])
                else:
                    serie = os.path.join(serie_from_conf[1], x[0])

        if temporada[0] is "0":
            season_dir = "Season " + temporada.replace("0", "", 1)
        else:
            season_dir = "Season " + temporada

        season_to_create = serie + "/" + season_dir
        if not os.path.isdir(serie):
            os.mkdir(serie)
        if not os.path.isdir(season_to_create):
            os.mkdir(season_to_create)
        if root != season_to_create:
            file_to_create = os.path.join(season_to_create, filename)
            if os.path.getsize(fullpath) < freespace(season_to_create):
                MB_moved += os.path.getsize(fullpath) / 1024 / 1024
                if os.path.exists(file_to_create) and md5_file(fullpath) == md5_file(file_to_create):
                    print "dio igual MD5", fullpath, file_to_create
                    os.remove(fullpath)
                else:
                    shutil.move(fullpath, file_to_create)
            else:
                print "no freespace", season_to_create, "to move", fullpath
    finish_time = time.time()
    total_time = finish_time - start_time
    if verbose is 1:
        print MB_moved, "Mb moved in", int(total_time), "seconds.", MB_moved / total_time, "Mb/s"


def group(col_findings, by_what, record_what):

    sortkeyfn = key = lambda s: s[by_what]
    input = col_findings
    input.sort(key=sortkeyfn)
    from itertools import groupby
    result = []
    for key, valuesiter in groupby(input, key=sortkeyfn):
        result.append(dict(type=key, items=list(v[record_what] for v in valuesiter)))
    result = {}
    for key, valuesiter in groupby(input, key=sortkeyfn):
        result[key] = list(v[record_what] for v in valuesiter)
    return result


def search_missing(col_findings):

    dictionary = group(col_findings, 3, 1)
    list_episodes = []
    for item in dictionary:
        print "Processing", item
        cosa = dictionary[item]
        for info_episodio in cosa:
            episode = int(float(info_episodio[4:6]))
            list_episodes.append(episode)
            if not list_episodes:  # la lista esta empty
                continue
            mini = min(list_episodes)
            maxi = max(list_episodes)
        for x in range(mini, maxi):
            from sets import Set
            set_hack = Set(list_episodes)
            if x not in set_hack:
                print "falta episodio", x, "de la temporada", info_episodio[1:3]

        list_episodes = []
        set_hack = []


def interactive(__DIRECTORY_TO_WORK_WITH__, target):

    if sys.argv[2] == "/" or sys.argv[3] == "/":
        print "NO SE PUEDE /"
        quit()
    a = process_series(sys.argv[2], 1)
    move_to_target(a, target, 1)


def clean(__DIRECTORY_TO_WORK_WITH__, mode):

    import errno
    unwanted = [".DS_Store", "Thumbs.db" ] # "sample" is dangerous is current implementation
    for root, dirs, files in os.walk(__DIRECTORY_TO_WORK_WITH__):
        if len(dirs) == 0 and len(files) == 0:
            print root + " is empty delete?"
            if mode in "-yes" or raw_input() in ('yes', 'y'):
                try:
                    os.rmdir(root)
                except OSError as ex:
                    if ex.errno == errno.ENOTEMPTY:
                        print "directory not empty"
        for item in files:
            for x in unwanted:
                if item.find(x) is not -1:
                    print os.path.join(root, item) + " delete?"
                    if raw_input() in ('yes', 'y'):
                        os.remove(os.path.join(root, item))


if mode == 1:
    automatic_behaviour()
elif mode >= 2:
    if sys.argv[1] in ('--interactive', '-i'):
        if mode == 4:
            interactive(sys.argv[2], sys.argv[3])
        else:
            print "For interactive mode you need [source] and [destination] parameters"
    elif sys.argv[1] in ('--clean', '-c'):
        clean(sys.argv[2], sys.argv[3])
    elif sys.argv[1] in ('--missing', '-m'):
        if mode == 3:
            a = process_series(sys.argv[2], 0)
            search_missing(a)
        else:
            print "For finding missing you need a sorted [source]"
    else:
        print "help ahora"
        quit()
else:
    automatic_behaviour()
