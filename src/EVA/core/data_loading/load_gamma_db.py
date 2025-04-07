import os
import sys
from pathlib import Path
from collections import namedtuple
import logging

from EVA.util.path_handler import get_path

logger = logging.getLogger(__name__)

# check if running from the executable or not
bundle_dir = getattr(sys, '_MEIPASS', "")

def load_gamma_data():
    minZ, maxZ = 0, 117

    gamma_levels_path = get_path('src/EVA/databases/gammas/levels/')
    gamma_data = []

    logger.debug("working directory: %s", os.getcwd())

    i = 0
    for i in range(119):
        gamma_data.append([])

    gamma_data = {}

    for i in range(minZ, maxZ):
        Z = i + 1
        if len(str(Z)) == 1:
            data, elem_name = decode_gammas(os.path.abspath(os.path.join(gamma_levels_path, f"z00{str(Z)}.dat")))
        if len(str(Z)) == 2:
            data, elem_name = decode_gammas(os.path.abspath(os.path.join(gamma_levels_path, f"z0{str(Z)}.dat")))
        if len(str(Z)) == 3:
            data, elem_name = decode_gammas(os.path.abspath(os.path.join(gamma_levels_path, f"z{str(Z)}.dat")))

        gamma_data[elem_name] = data

    return gamma_data


"""
def loadgamma():
    # check if gammas have already been loaded by checking random index
    if not globals.Full_Gammas[20]:
        loadgammascan(0,117)



def loadgammascan(minA,maxA):
    str1 = 'src/EVA/databases/gammas/levels/z'

    for i in range(minA,maxA):
        A = i+1
        if len(str(A)) == 1:
            decodegammas2(str1+'00'+str(A)+'.dat',A)
        if len(str(A)) == 2:
            decodegammas2(str1 + '0' + str(A) + '.dat',A)
        if len(str(A)) == 3:
            decodegammas2(str1 + str(A) + '.dat',A)

    #print('gammas',globals.Full_Gammas)
"""

def decode_gammas(filename):
    f = open(filename, 'r')
    record = namedtuple('Isotope',
                        'SYMB A Z Nol Nog Nmax Nc Sn Sp')
    columns1 = ((0, 5), (6, 10), (11, 15), (16, 20), (21, 25), (26, 30), (31, 35), (36, 47), (48, 60))

    record2 = namedtuple('Level',
                         'N1 Elv s p T_half Ng J')
    columns2 = ((0, 3), (5, 14), (16, 20), (21, 23), (25, 33), (34, 38), (39, 39))

    record3 = namedtuple('Gammas',
                         'Nf Eg Pg Pe ICC')
    columns3 = ((39, 43), (45, 55), (55, 65), (66, 76), (77, 87))

    gamma_data = []
    symb = ""

    while f:
        string = f.readline()

        if string == "":
            break

        nucl = record._make([string[c[0]:c[1]] for c in columns1])
        symb = nucl.SYMB

        if int(nucl.Nol) >= 1:

            for x in range(int(nucl.Nol)):
                string = f.readline()
                level = record2._make([string[c[0]:c[1]] for c in columns2])

                if int(level.Ng) >= 1:
                    for y in range(int(level.Ng)):
                        string = f.readline()
                        gammas = record3._make([string[c[0]:c[1]] for c in columns3])
                        gamma_data.append((nucl.SYMB, float(gammas.Eg)*1000, float(gammas.Pg)*100, level.T_half))
    f.close()

    elem_name = str("".join(filter(lambda c: c.isalpha(), symb)))
    return gamma_data, elem_name

"""
def decodegammas(filename, A):
    #not used keep for time being :)
    #print('A=',A)
    #print('filename',filename)
    f = open(filename,'r')

    record = namedtuple('Isotope',
                        'SYMB A Z Nol Nog Nmax Nc Sn Sp')
    columns1 = ((0,5),(6,10),(11,15),(16,20),(21,25),(26,30),(31,35),(36,47),(48,60))

    record2 = namedtuple('Level',
                        'N1 Elv s p T_half Ng J')
    columns2 = ((0,3),(5,14),(16,20),(21,23),(25,33),(34,38),(39,39))

    record3 = namedtuple('Gammas',
                          'Nf Eg Pg Pe ICC')
    columns3 = ((39,43),(45,55),(55,65),(66,76),(77,87))

    while f:
        string = f.readline()
        if string == "":
            break

        dataline = [string[c[0]:c[1]] for c in columns1]

        nucl =record._make([string[c[0]:c[1]] for c in columns1])

        if int(nucl.Nol) >= 1:

            for x in range(int(nucl.Nol)):
                string = f.readline()
                level =record2._make([string[c[0]:c[1]] for c in columns2])

                if int(level.Ng) >= 1:
                    for y in range(int(level.Ng)):
                        string = f.readline()
                        gammas = record3._make([string[c[0]:c[1]] for c in columns3])

                        temp1 = list(globals.Full_Gammas)
                        temp1.append((nucl.SYMB,gammas.Eg,gammas.Pg,level.T_half))
                        globals.Full_Gammas = tuple(temp1)

    f.close()


def decodegammas2(filename, A):
    f = open(filename,'r')
    record = namedtuple('Isotope',
                        'SYMB A Z Nol Nog Nmax Nc Sn Sp')
    columns1 = ((0,5),(6,10),(11,15),(16,20),(21,25),(26,30),(31,35),(36,47),(48,60))

    record2 = namedtuple('Level',
                        'N1 Elv s p T_half Ng J')
    columns2 = ((0,3),(5,14),(16,20),(21,23),(25,33),(34,38),(39,39))

    record3 = namedtuple('Gammas',
                          'Nf Eg Pg Pe ICC')
    columns3 = ((39,43),(45,55),(55,65),(66,76),(77,87))

    while f:
        string = f.readline()
        if string == "":
            break

        dataline = [string[c[0]:c[1]] for c in columns1]

        nucl =record._make([string[c[0]:c[1]] for c in columns1])

        if int(nucl.Nol) >= 1:

            for x in range(int(nucl.Nol)):
                string = f.readline()
                level =record2._make([string[c[0]:c[1]] for c in columns2])

                if int(level.Ng) >= 1:
                    for y in range(int(level.Ng)):
                        string = f.readline()
                        gammas = record3._make([string[c[0]:c[1]] for c in columns3])

                        globals.Full_Gammas[A].append((nucl.SYMB, gammas.Eg, gammas.Pg, level.T_half))

    f.close()
    """
