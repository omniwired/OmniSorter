#!/usr/bin/python
# -*- coding: utf-8 *-*
# author Juan Manuel Combetto
# www.omniwired.com
"""
@author: Juan Manuel Combetto
Sort series that follow the SxxExx convention and
moves them to series folder with the following Structure
Series name
  - Season (number)
    - Episode files
"""
from itertools import groupby
from progressbar import Bar, ETA, \
    FileTransferSpeed, Percentage, ProgressBar, RotatingMarker
from sets import Set
import errno
import hashlib
import os
import pickle
import re
import shutil
import sys
import time
# no detecta .AVI el missing finder
processed_series_size = 0
__DIRECTORY_TO_WORK_WITH__ = "/home/omniwired/Downloads"
__EXTENSIONS_TO_LOOK_FOR__ = ".avi", ".mkv", ".rar"
__EXTERNAL_FOLDERS__ = "/media"
TARGET = __DIRECTORY_TO_WORK_WITH__ + "/Videos"
CONFIG_FILE = os.path.join(sys.path[0], "series.conf")  # os.getcwd()


def process_series(folder_to_process, verbose):
    """
    
    Creates series list with the following elements
    [serie, info_episodio, fullpath, root, season, item]
    from series path given as series parameter
                                        
    """
    regex = '(?=[S-s][0-9][0-9][E-e][0-9][0-9])\w+' #old SXXEXX
    # regex = '(?=([0-9][x][0-9][0-9])|([S-s][0-9][0-9][E-e][0-9][0-9]))\w+' #SXXEXX & xXxx
    # (?=([0-9][x][0-9][0-9]))\w+
    col_findings = []
    global processed_series_size
    # malisimo usar una variable global
    for root, dirs, files in os.walk(folder_to_process):
        if 'Incomplete' in dirs:
            dirs.remove('Incomplete')  # don't visit Incomplete directories
        for item in files:
            if item.endswith(__EXTENSIONS_TO_LOOK_FOR__):                
                match = re.search(regex, item)
                fullpath = os.path.join(root, item)
                if match is not None:
                    if verbose is 1:
                        size = os.path.getsize(fullpath) / 1024 / 1024
                        print "Processing " + item, size, "MB"
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
                        unrar_module(fullpath)
                    else:
                        col_findings.append([serie, info_episodio, \
                                        fullpath, root, season, item])
    if verbose is 1:
        print "Processed", processed_series_size / 1024, "Gb"
    return col_findings


def unrar_module(fullpath):
    """
    Automatically unrars files that come in a compress multipart form.
    """
    #alpha needs more work
    print fullpath
    os.system("unrar x -o- -inul \'" + fullpath + "\' \'" + TARGET + "\'")
    os.remove(fullpath)
#    os.system("rm \'" + fullpath[:-2] + "*\'")    
    # VERY DANGEROUS
#    shutil.rmtree(root, True)


def md5_file(fileName, block_size=2 ** 20):
    """
    Gets the md5 of given file
    """
    file_handler = open(fileName, 'rb')
    md5 = hashlib.md5()
    parts = os.path.getsize(fileName) / block_size
    # progress bar
    widgets = ['Hashing: ', Percentage(), ' ', Bar(marker=RotatingMarker()),
               ' ', ETA(), ' ', FileTransferSpeed()]
    pbar = ProgressBar(widgets=widgets, maxval=(parts+1)*block_size).start()
    # progress bar
        #real work
    leidos = 0
    while True:
        data = file_handler.read(block_size)
        if not data:
            break
        md5.update(data)
        leidos += block_size
        pbar.update(leidos)
        #realwork
    
    pbar.finish()
    # progress bar
    
    return md5.hexdigest()


def get_series_list():
    """
    Loads line by line Series name and path
    in the form of Series:/path/to/
    """
    col_series = []
    try:
        file_handler = open(CONFIG_FILE, 'r')
        for line in file_handler:
            conf_serie = line.split(":")
            conf_serie[1] = conf_serie[1].replace("\n", "")  # removes the \n
            col_series.append(conf_serie)
    except:
        print "series.conf should exist in the same folder as this file"
    
    return col_series


def normalize(string):
    """
    Cleans the names series little bit for make it more easy later on.
    """
    string = string.replace(".", " ")
    string = string.replace(" - ", "")
    string = string.title()
    if string.endswith(" "):
        string = string[:-1]
    return string

def save(data, file_path):
    """
    Dumps the object to the disk
    """
    output = open(file_path, 'wb')
    pickle.dump(data, output)
    output.close()

def load(file_path):
    """
    Loads the object back into memory
    """
    if not os.path.exists(file_path):
        save(dict(), file_path)
    archivo = open(file_path, 'rb')
    data = pickle.load(archivo)
    archivo.close()
    return data


def find_duplicates(series_found):
    """
    Get a unique hash for each file and then compares its uniqueness
    """
    # que no borre todo cuando se desconecta un externo (buscar /media, por ej)
    # global processed_series_size
    total = 0
    #set_hack = Set()
    duplicates_list = []
    dic_of_names_and_md5 = dict() #crea un dicionario vacio para el picke
    file_handler = os.path.join(sys.path[0], "hashes.md5")
    dic_of_names_and_md5 = load(file_handler)
    pbar = ProgressBar(widgets=[Percentage(), Bar()], \
                       maxval=processed_series_size).start()    
    
#   Rainbow table for the already discovered hashes
    for item in series_found:
        size = os.path.getsize(item[2]) / 1024 / 1024
        total += size
        pbar.update(total)
        if item[2] not in dic_of_names_and_md5:
            dic_of_names_and_md5[item[2]] = md5_file(item[2])
#   Rainbow table for the already discovered hashes
    pbar.finish()
    
    hash_dic = dict()
    for item in dic_of_names_and_md5.keys():
        if not os.path.exists(item):
            print item, "Doesn't exists anymore"
            del dic_of_names_and_md5[item]
            continue
    
        lista = []
        if dic_of_names_and_md5[item] not in hash_dic:
            lista.append(item)
            hash_dic[dic_of_names_and_md5[item]] = lista
        else:
            for cosa in hash_dic[dic_of_names_and_md5[item]]:
                lista.append(cosa)
            lista.append(item)
            hash_dic[dic_of_names_and_md5[item]] = lista
    for item in hash_dic:
        if len(hash_dic[item]) > 1:
            duplicates_list.extend(hash_dic[item])
            
    save(dic_of_names_and_md5, file_handler)
    
    if len(duplicates_list) != 0:
        print "\n \n These are the duplicates that have been found"
        for item in duplicates_list:
            print item
        print "Do you want to delete some? [y] [n]"
        user_input = raw_input()
        if user_input in ('no', 'n'):
            quit()
        elif user_input in ('yes', 'y'):
            for item in duplicates_list:
                print item, "delete?"
                if raw_input() in ('yes', 'y'):
                    os.remove(item)


def automatic_behaviour():
    
    series_found = process_series(__DIRECTORY_TO_WORK_WITH__, 0)
    move_to_target(series_found, TARGET, 0)
    

def freespace(path):
    """
    Returns the number of free bytes on the drive that ``path`` is on
    """
    size = os.statvfs(path)
    return size.f_bsize * size.f_bavail


def move_to_target(col_findings, target_folder, verbose):
    """
    @precondition: run process_series to have series valid collection of files
    to move
    Moves the series to their new sorted location     
    """
    special_series_list = get_series_list()
    data_moved = 0
    start_time = time.time()
    if not os.path.isdir(target_folder):
        if verbose is 1:
            print "Creating " + target_folder
        os.mkdir(target_folder)
    for item in col_findings:
        # ex ['series', 'SXXEXX', fullpath, root, season_number, filename]
        serie = os.path.join(target_folder, item[0])
        fullpath = item[2]
        root = item[3]
        temporada = item[4]
        filename = item[5]
#        if info_episodio.find('S') is not -1:                    
#            filename = item[5]
#        si tiene la forma xXxx le creamos un nuevo filename
#            season = info_episodio[0]
#            print "season", season

      
        # 21 / NOV / 2011, 1st implementation of This Week
#        print fullpath
#        __week__ = 60 * 60 * 24 * 7 
#        if os.path.getmtime(fullpath) < (time.clock() * __week__):
#            print "last modified: %s" % os.path.getmtime(fullpath)
#            #serie = os.path.join(serie_from_conf[1], item[0])
# basicamente si tiene menos de una semana de bajado ponerlo en otra carpeta de NUEVOS
#       print "created: %s" % time.ctime(os.path.getctime(fullpath))
        
        # Special Cases  
        
        for serie_from_conf in special_series_list:
            if item[0].lower() == serie_from_conf[0].lower():
                # special check for external drives
                if not os.path.isdir(serie_from_conf[1]):
                    serie = os.path.join(target_folder, item[0])
                else:
                    serie = os.path.join(serie_from_conf[1], item[0])

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
                data_moved += os.path.getsize(fullpath) / 1024 / 1024
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
        print data_moved, "Mb moved in", int(total_time), \
        "seconds.", data_moved / total_time, "Mb/s"


def group(col_findings, by_what, record_what):
    """
    Groups collections based on conditions
    """
    sortkeyfn = key = lambda s: s[by_what]
    given_input = col_findings
    given_input.sort(key=sortkeyfn)
    result = []
    for key, valuesiter in groupby(given_input, key=sortkeyfn):
        result.append(dict(type=key, items=list(v[record_what] \
        for v in valuesiter)))
    result = {}
    for key, valuesiter in groupby(given_input, key=sortkeyfn):
        result[key] = list(v[record_what] for v in valuesiter)
    return result


def search_missing(col_findings):
    """
    Search the minimum and maximium episode number for series given Season
    and returns which ones are missing in that range.
    """
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
        for item in range(mini, maxi):
            set_hack = Set(list_episodes)
            if item not in set_hack:
                print "Missing episode", item, "of Season", info_episodio[1:3] 
                # ^^ agregar formato Sxxexx
#                os.system("nautilus \'" + item + "\'")
        list_episodes = []
        set_hack = []


def interactive(target_folder):
    """
    Defines the command line "interactive" behaviour
    """
    if sys.argv[2] == "/" or sys.argv[3] == "/":
        print "NO SE PUEDE /"
        quit()
    series_found = process_series(sys.argv[2], 1)
    move_to_target(series_found, target_folder, 1)


def clean(folder_to_clean):
    """
    Finds files we don't need, such as sample files also deletes
    empty folders
    """
    # "sample" is dangerous is current implementation
    unwanted = [".DS_Store", "Thumbs.db", "sample"]
    for root, dirs, files in os.walk(folder_to_clean):
        if len(dirs) == 0 and len(files) == 0:
            print root + " is empty delete?"
            if raw_input() in ('yes', 'y'):
                try:
                    os.rmdir(root)
                except OSError as ex:
                    if ex.errno == errno.ENOTEMPTY:
                        print "directory not empty"
        for item in files:
            for no_quiero in unwanted:
                if item.find(no_quiero) is not -1:
                    print os.path.join(root, item) + " delete?"
                    if raw_input() in ('yes', 'y'):
                        os.remove(os.path.join(root, item))

if __name__ == '__main__':
    # pylint: disable-msg=C0103
    mode = len(sys.argv)    
    if mode == 1:
        automatic_behaviour()
    elif mode >= 2:
        if sys.argv[1] in ('--interactive', '-i'):
            if mode == 4:
                interactive(sys.argv[3])
            else:
                print "For interactive mode you need [source] " + \
                      "and [destination] parameters"
        elif sys.argv[1] in ('--clean', '-c'):
            clean(sys.argv[2])
        elif sys.argv[1] in ('--missing', '-m'):
            if mode == 3:
                series = process_series(sys.argv[2], 0)
                search_missing(series)
            else:
                print "For finding missing you need series sorted [source]"
    
        elif sys.argv[1] in ('--duplicates', '-d'):
            if mode == 3:
                print "This process WILL take series long time"
                found_series = process_series(sys.argv[2], 1)
                if len(found_series) != 0:
                    find_duplicates(found_series)
            else:
                print "For finding duplicates you need \
                       to especify series [source]"
        else:
            print "help ahora"
            quit()
    else:
        automatic_behaviour()