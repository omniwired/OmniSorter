#!/usr/bin/python
# -*- coding: utf-8 *-*
# author Juan Manuel Combetto
# www.omniwired.com
import os
import shutil
import re
import sys
import time
from sets import Set
from itertools import groupby
import hashlib
import errno
import pickle
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
                        FileTransferSpeed, FormatLabel, Percentage, \
                        ProgressBar, ReverseBar, RotatingMarker, \
                        SimpleProgress, Timer
# no detecta .AVI el missing finder
processed_series_size = 0
__DIRECTORY_TO_WORK_WITH__ = "/home/omniwired/Downloads"
__EXTENSIONS_TO_LOOK_FOR__ = ".avi", ".mkv", ".rar"
target = __DIRECTORY_TO_WORK_WITH__ + "/Videos"
config_file = os.path.join(sys.path[0], "series.conf")  # os.getcwd()



mode = len(sys.argv)

def process_series(__DIRECTORY_TO_WORK_WITH__, verbose):

    regex = '(?=[S-s][0-9][0-9][E-e][0-9][0-9])\w+' #old SXXEXX
    # regex = '(?=([0-9][x][0-9][0-9])|([S-s][0-9][0-9][E-e][0-9][0-9]))\w+' #SXXEXX & xXxx
    # (?=([0-9][x][0-9][0-9]))\w+
    col_findings = []
    global processed_series_size
    for root, dirs, files in os.walk(__DIRECTORY_TO_WORK_WITH__):
#        if 'Videos' in dirs:
#            dirs.remove('Videos')  # don't visit Videos directories
        for item in files:
            if item.endswith(__EXTENSIONS_TO_LOOK_FOR__):
                match = re.search(regex, item)
                fullpath = os.path.join(root, item)
                if match is not None:
                    if verbose is 1:
                        size = os.path.getsize(fullpath) / 1024 / 1024
                        print "Processsing " + item, size, "MB"
                        processed_series_size += size
                    donde_cortar = match.span()
                    info_episodio = item[donde_cortar[0]:donde_cortar[1]]
                    serie = normalize(item[:donde_cortar[0]])
                    season = info_episodio[1:3]
#                    if info_episodio.find('S') is not -1:                    
#                        season = info_episodio[1:3]
#                    else:
#                        season = info_episodio[0]
#                        print "season", season
                    # special case rar
                    if item.endswith(".rar"):
                        print "unrar -> ", fullpath
                        unrar_module(fullpath, root)
                    else:
                        col_findings.append([serie, info_episodio, \
                                        fullpath, root, season, item])
    if verbose is 1:
        print "Processed", processed_series_size / 1024, "Gb"
    return col_findings


def unrar_module(fullpath, root):

    #alpha needs more work
    os.system("unrar x -o- -inul \'" + fullpath + "\' \'" + target + "\'")
    # VERY DANGEROUS
#    shutil.rmtree(root, True)


def md5_file(fileName, block_size=2 ** 20):

    f = open(fileName, 'rb')
    md5 = hashlib.md5()
    parts = os.path.getsize(fileName) / block_size
 #   progress bar
    widgets = ['Hashing: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
               ' ', ETA(), ' ', FileTransferSpeed()]
    pbar = ProgressBar(widgets=widgets, maxval=(parts+1)*block_size).start()
#    for i in range(parts):
        #real work
    leidos = 0
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
        leidos += block_size
        pbar.update(leidos)
        #realwork
    
    pbar.finish()
   #  progress bar
    
    return md5.hexdigest()


def get_series_list():

    f = open(config_file, 'r')
    col_series = []

    for line in f:
        conf_serie = line.split(":")
        conf_serie[1] = conf_serie[1].replace("\n", "")  # removes the \n
        col_series.append(conf_serie)
    return col_series


def normalize(str):

    str = str.replace(".", " ")
    str = str.replace(" - ", "")
    str = str.title()
    if str.endswith(" "):
        str = str[:-1]
    return str

def save(data, file):
    
    output = open(file, 'wb')
    pickle.dump(data, output)
    output.close()

def load(file):

    if not os.path.exists(file):
        save(dict(), file)
    input = open(file, 'rb')
    data = pickle.load(input)
    input.close()
    return data


def find_duplicates(series_found):
    
    # que no borre todo cuando se desconecta un externo (buscar /media, por ej)
    global processed_series_size
    total = 0
    set_hack = Set()
    duplicates_list = []
    dic = dict()
    file = os.path.join(sys.path[0], "hashes.md5")
    dic = load(file)
    pbar = ProgressBar(widgets=[Percentage(), Bar()], maxval=processed_series_size).start()    
    
#   Rainbow table for the already discovered hashes
    for item in series_found:
        size = os.path.getsize(item[2]) / 1024 / 1024
        total += size
        pbar.update(total)
        if item[2] not in dic:
            dic[item[2]] = md5_file(item[2])
#   Rainbow table for the already discovered hashes
    pbar.finish()
    
    hash_dic = dict()
    for x in dic.keys():
        if not os.path.exists(x):
            print x, "Doesn't exists anymore"
            del dic[x]
            continue
    
        list = []
        if dic[x] not in hash_dic:
            list.append(x)
            hash_dic[dic[x]] = list
        else:
            for cosa in hash_dic[dic[x]]:
                list.append(cosa)
            list.append(x)
            hash_dic[dic[x]] = list
    for item in hash_dic:
        if len(hash_dic[item]) > 1:
            duplicates_list.extend(hash_dic[item])
            
    save(dic, file)
    
    if len(duplicates_list) != 0:
        print "\n \n These are the duplicates that have been found"
        for x in duplicates_list:
            print x
        print "Do you want to delete some? [y] [n]"
        input = raw_input()
        if input in ('no', 'n'):
            quit()
        elif input in ('yes', 'y'):
            for x in duplicates_list:
                print x, "delete?"
                if raw_input() in ('yes', 'y'):
                    os.remove(x)


def automatic_behaviour():
    
    series_found = process_series(__DIRECTORY_TO_WORK_WITH__, 0)
    move_to_target(series_found, target, 0)
    

def freespace(p):
    """
    Returns the number of free bytes on the drive that ``p`` is on
    """
    s = os.statvfs(p)
    return s.f_bsize * s.f_bavail


def move_to_target(col_findings, target, verbose):

    special_series_list = get_series_list()
    MB_moved = 0
    start_time = time.time()
    if not os.path.isdir(target):
        if verbose is 1:
            print "Creating " + target
        os.mkdir(target)
    for x in col_findings:
        # ex ['series', 'SXXEXX', fullpath, root, season_number, filename]
        serie = os.path.join(target, x[0])
        fullpath = x[2]
        root = x[3]
        temporada = x[4]
        filename = x[5]
#        if info_episodio.find('S') is not -1:                    
#            filename = x[5]
#        si tiene la forma xXxx le creamos un nuevo filename
#            season = info_episodio[0]
#            print "season", season

        # Special Cases
        for serie_from_conf in special_series_list:
            if x[0].lower() == serie_from_conf[0].lower():
                # special check for external drives
                if not os.path.isdir(serie_from_conf[1]):
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
                if os.path.exists(file_to_create) \
                and md5_file(fullpath) == md5_file(file_to_create):
                    print "dio igual MD5", fullpath, file_to_create
                    os.remove(fullpath)
                else:
                    shutil.move(fullpath, file_to_create)
                    if verbose is 1:
                        print "Moving", fullpath, "to", file_to_create
            else:
                print "no freespace", season_to_create, "to move", fullpath
    finish_time = time.time()
    total_time = finish_time - start_time
    if verbose is 1:
        print MB_moved, "Mb moved in", int(total_time), \
        "seconds.", MB_moved / total_time, "Mb/s"


def group(col_findings, by_what, record_what):

    sortkeyfn = key = lambda s: s[by_what]
    input = col_findings
    input.sort(key=sortkeyfn)
    result = []
    for key, valuesiter in groupby(input, key=sortkeyfn):
        result.append(dict(type=key, items=list(v[record_what] \
        for v in valuesiter)))
    result = {}
    for key, valuesiter in groupby(input, key=sortkeyfn):
        result[key] = list(v[record_what] for v in valuesiter)
    return result


def search_missing(col_findings):

    dictionary = group(col_findings, 3, 1)
    list_episodes = []
    for item in dictionary:
        print "Processing", item
        dict_items = dictionary[item]
        for info_episodio in dict_items:
            episode = int(float(info_episodio[4:6]))
            list_episodes.append(episode)
            if not list_episodes:  # la lista esta empty
                continue
            mini = min(list_episodes)
            maxi = max(list_episodes)
        for x in range(mini, maxi):
            set_hack = Set(list_episodes)
            if x not in set_hack:
                print "Missing episode", x, "of Season", info_episodio[1:3]
#                os.system("nautilus \'" + item + "\'")
        list_episodes = []
        set_hack = []


def interactive(__DIRECTORY_TO_WORK_WITH__, target):

    if sys.argv[2] == "/" or sys.argv[3] == "/":
        print "NO SE PUEDE /"
        quit()
    a = process_series(sys.argv[2], 1)
    move_to_target(a, target, 1)


def clean(__DIRECTORY_TO_WORK_WITH__, mode):

    # "sample" is dangerous is current implementation
    unwanted = [".DS_Store", "Thumbs.db"]
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
            print "For interactive mode you need [source] " + \
                  "and [destination] parameters"
    elif sys.argv[1] in ('--clean', '-c'):
        clean(sys.argv[2], sys.argv[3])
    elif sys.argv[1] in ('--missing', '-m'):
        if mode == 3:
            a = process_series(sys.argv[2], 0)
            search_missing(a)
        else:
            print "For finding missing you need a sorted [source]"

    elif sys.argv[1] in ('--duplicates', '-d'):
        if mode == 3:
            print "This process WILL take a long time"
            found_series = process_series(sys.argv[2], 1)
            find_duplicates(found_series)
        else:
            print "For finding duplicates you need to especify a [source]"
    else:
        print "help ahora"
        quit()
else:
    automatic_behaviour()
#found_series = process_series("/home/omniwired/Downloads/Videos/The It Crowd", 1)
#find_duplicates(found_series)
#import pickle
#cosa = dict()
#cosa['file'] = "data"
#
#if "file" in cosa:
#    print cosa
#
#output = open('data.pkl', 'wb')
#
## Pickle dictionary using protocol 0.
#pickle.dump(cosa, output)
#output.close()
#input = open('data.pkl', 'rb')
#c = pickle.load(input)
#print "c es", c
