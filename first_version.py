#!/usr/bin/python
# -*- coding: utf-8 *-*

import os
import shutil
import re
import sys


__DIRECTORY_TO_WORK_WITH__ = "/home/omniwired/Downloads/"
__EXTENSIONS_TO_LOOK_FOR__ = [".avi", ".mkv"]  # sin uso
__SERIES_TO_LOOK_FOR__ = ['The big bang theory', 'Fringe']  # sin uso
target = __DIRECTORY_TO_WORK_WITH__ + "/Videos"

mode = len(sys.argv)


def normalize(str):
#    str[0] = str[0].upper()
    str = str.replace(".", " ")
    if str.endswith(" "):
        str = str[:-1]
    return str


def automatic_behaviour():

    process_series(__DIRECTORY_TO_WORK_WITH__, target, 0)


def process_series(__DIRECTORY_TO_WORK_WITH__, target, verbose):

    if not os.path.isdir(target):
        if verbose is 1:
            print "Creating " + target
        os.mkdir(target)
    for root, dirs, files in os.walk(__DIRECTORY_TO_WORK_WITH__):
        if 'Videos' in dirs:
            dirs.remove('Videos')  # don't visit Videos directories
        for item in files:
            if item.endswith(".avi") or item.endswith(".mkv"):
                match = re.search('(?=[S-s][0-9][0-9][E-e][0-9][0-9])\w+', item)
                if match is not None:
                    if verbose is 1:
                        print "Processsing " + item
                    donde_cortar = match.span()
                    info_episodio = item[donde_cortar[0]:donde_cortar[1]]
                    serie = target + "/" + normalize(item[:donde_cortar[0]])
                    temporada = info_episodio[1:3]
                    if temporada[0] is "0":
                        season_dir = serie + "/" + "Season " + temporada.replace("0", "", 1)
                    else:
                        season_dir = serie + "/" + "Season " + temporada
                    if not os.path.isdir(serie):
                        os.mkdir(serie)
                    if not os.path.isdir(season_dir):
                        os.mkdir(season_dir)
                        # que pasa si no se pudo crear (ahora hay errno)
                    if root != season_dir:
                        shutil.move(os.path.join(root, item), season_dir)



def interactive(__DIRECTORY_TO_WORK_WITH__, target):

    if sys.argv[2] == "/" or sys.argv[3] == "/":
        print "NO SE PUEDE /"
        quit()
    process_series(sys.argv[2], target, 1)


def clean(__DIRECTORY_TO_WORK_WITH__):

    for root, dirs, files in os.walk(__DIRECTORY_TO_WORK_WITH__):
        if len(dirs) == 0 and len(files) == 0:
            print root + " is empty delete?"
            if raw_input() in ('yes', 'y'):
                try:
                    os.rmdir(root)
                except OSError as ex:
                    if ex.errno == errno.ENOTEMPTY:
                        print "directory not empty"
        for item in files:
            if item.endswith(".avi") or item.endswith(".mkv"):
                if item.find("sample") is not -1:
                    print os.path.join(root, item) + " delete?"
                    if raw_input() in ('yes', 'y'):
                        os.remove(os.path.join(root, item))


# logica de modos
if mode == 1:
    automatic_behaviour()
elif mode >= 2:
    if sys.argv[1] in ('--interactive', '-i'):
        if mode == 4:
            interactive(sys.argv[2], sys.argv[3])
        else:
            print "For interactive mode you need [source] and [destination] parameters"
    elif sys.argv[1] in ('--clean', '-c'):
        clean(sys.argv[2])
    else:
        print "help ahora"
        quit()
else:
    automatic_behaviour()
