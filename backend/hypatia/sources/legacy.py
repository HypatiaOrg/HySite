import os
import csv
import copy
import json
import pickle
import shutil
from datetime import datetime

import pandas as pd

from hypatia.config import star_data_output_dir

from hypatia.sources.sqlite import get_db, test_database_dir, hdf5_data_dir

ordered_outputs = ["absolute", "anders89", "asplund05", "asplund09",
                   "grevesse98", "lodders09", "original", "grevesse07"]

outputs_dict = {output_type: output_index + 1 for output_index, output_type in list(enumerate(ordered_outputs))}


def intable(x, invalid=None):
    try:
        return int(x)
    except:
        return invalid


def floatable(x, invalid=None):
    try:
        return float(x)
    except:
        return invalid


def sortable(x, reverse):
    if x in [None, "999.0", 9999, ""]:
        if reverse:
            return -1e20
        else:
            return 1e20
    else:
        return x


def maxable(a, b, invalid=None):
    try:
        return max(-a, b)
    except:
        return invalid


class PersistentDict(dict):
    """ Persistent dictionary with an API compatible with shelve and anydbm.

    The dict is kept in memory, so the dictionary operations run as fast as
    a regular dictionary.

    Write to disk is delayed until close or sync (similar to gdbm's fast mode).

    Input file format is automatically discovered.
    Output file format is selectable between pickle, json, and csv.
    All three serialization formats are backed by fast C implementations.

    """

    def __init__(self, filename, flag='c', mode=None, format_type='pickle', *args, **kwds):
        self.flag = flag  # r=readonly, c=create, or n=new
        self.mode = mode  # None or an octal triple like 0644
        self.format = format_type  # 'csv', 'json', or 'pickle'
        self.filename = filename
        if flag != 'n' and os.access(filename, os.R_OK):
            fileobj = open(filename, 'rb' if format_type == 'pickle' else 'r')
            with fileobj:
                self.load(fileobj)
        dict.__init__(self, *args, **kwds)

    def sync(self):
        # Write dict to disk
        if self.flag == 'r':
            return
        filename = self.filename
        tempname = filename + '.tmp'
        fileobj = open(tempname, 'wb' if self.format == 'pickle' else 'w')
        try:
            self.dump(fileobj)
        except Exception:
            os.remove(tempname)
            raise
        finally:
            fileobj.close()
        shutil.move(tempname, self.filename)  # atomic commit
        if self.mode is not None:
            os.chmod(self.filename, self.mode)

    def close(self):
        self.sync()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def dump(self, fileobj):
        if self.format == 'csv':
            csv.writer(fileobj).writerows(self.items())
        elif self.format == 'json':
            json.dump(self, fileobj, separators=(',', ':'))
        elif self.format == 'pickle':
            pickle.dump(dict(self), fileobj, protocol=2)
        else:
            raise NotImplementedError('Unknown format: ' + repr(self.format))

    def load(self, fileobj):
        # try formats from most restrictive to the least restrictive
        for loader in (pickle.load, json.load, csv.reader):
            fileobj.seek(0)
            try:
                return self.update(loader(fileobj))
            except Exception:
                pass
        raise ValueError('File not in a supported format')


def upload_star_data(HYP_DATA_DIR: str, filePath: str, solarnorm: int, test_mode: bool = False):
    hashtable = PersistentDict(os.path.join(HYP_DATA_DIR, "hashtable.shelf"))
    compositions = PersistentDict(os.path.join(HYP_DATA_DIR, "compositions-%s.shelf" % solarnorm))
    sqlite = get_db(test_mode=test_mode)

    with open(filePath) as infile:
        numberOfChars = len(infile.read())
    with open(filePath) as infile:
        blankPlanet = dict.fromkeys([
            'f_name',
            'f_m_p',
            'f_m_p_err',
            'f_p',
            'f_p_err',
            'f_e',
            'f_e_err',
            'f_a',
            'f_a_err'])
        blankNewData = dict.fromkeys([
            'f_hip',
            'f_hd',
            'f_bd',
            'f_spec',
            'f_vmag',
            'f_bv',
            'f_dist',
            'f_ra',
            'f_dec',
            'f_x',
            'f_y',
            'f_z',
            'f_disk',
            'f_u',
            'f_v',
            'f_w',
            'f_teff',
            'f_logg',
            'f_mass',
            'f_radius',
            'f_number_of_planets',
            'f_2mass',
            'f_ra_proper_motion',
            'f_dec_proper_motion',
            'f_bmag'])
        newData = copy.deepcopy(blankNewData)
        newAuthor = []
        newYear = []
        newElement = []
        # added
        newElementValue = []
        newNLTE = []
        newVersion = []
        newPlanetData = {}
        newLi = []

        starNo = 1
        curPos = 0

        for line in infile:
            curLine = line.split()
            curPos += len(line)
            # print len(curLine)

            if len(curLine) > 1:
                if curLine[0] == 'Star:':
                    val = int(curLine[1][-12:])
                    newData['f_hip'] = val
                    newData['f_all_names'] = curLine[1]
                if curLine[0] == 'hip':
                    if len(curLine) > 2:
                        try:
                            val = int(curLine[2])
                        except ValueError:
                            # drop the binary flag
                            val = int(curLine[2][:-1])
                        newData['f_hip'] = val
                        newData['f_hipparcos'] = val
                        newData['f_all_names'] += ", HIP " + curLine[2]
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = "HIP " + curLine[2]
                    else:
                        newData['f_hipparcos'] = None
                if curLine[0] == 'hd':
                    if len(curLine) > 2:
                        val = curLine[2]
                        val = val.replace("[", "")
                        val = val.replace("]", "")
                        val = val.replace("'", "")
                        newData['f_hd_str'] = val
                        newData['f_all_names'] += ", HD " + val
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = "HD " + val
                        try:
                            val = int(val)
                            newData['f_hd'] = val
                        except:  # HD ends with a letter
                            newData['f_hd_letter'] = val[-1]
                            val = int(val[:-1])
                            newData['f_hd'] = val
                    else:
                        newData['f_hd'] = None
                        newData['f_hd_str'] = None
                        newData['f_hd_letter'] = None
                if curLine[0] == 'bd':
                    if len(curLine) > 2:
                        val = curLine[2] + ' ' + curLine[3]
                        newData['f_bd'] = val
                        newData['f_all_names'] += ", " + val.replace("B+", "BD+") + " " + val
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = val.replace("B+", "BD+")
                    else:
                        newData['f_bd'] = None
                if curLine[0] == '2MASS':
                    if len(curLine) > 2:
                        val = curLine[2]
                        newData['f_2mass'] = val
                        newData['f_all_names'] += ", 2MASS " + val
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = "2MASS " + val
                    else:
                        newData['f_2mass'] = None
                if curLine[0] == 'Gaia' and curLine[1] == "DR2":
                    if len(curLine) > 3:
                        val = curLine[3]
                        newData['f_gaia_dr2'] = val
                        newData['f_all_names'] += ", Gaia DR2 " + val
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = "Gaia DR2 " + val
                    else:
                        newData['f_gaia_dr2'] = None
                if curLine[0] == 'Gaia' and curLine[1] == "EDR3":
                    if len(curLine) > 3:
                        val = curLine[3]
                        newData['f_gaia_edr3'] = val
                        newData['f_all_names'] += ", Gaia EDR3 " + val
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = "Gaia EDR3 " + val
                    else:
                        newData['f_gaia_edr3'] = None
                if curLine[0] == 'Gaia' and curLine[1] == "DR3":
                    if len(curLine) > 3:
                        val = curLine[3]
                        newData['f_gaia_dr3'] = val
                        newData['f_all_names'] += ", Gaia DR3 " + val
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = "Gaia DR3 " + val
                    else:
                        newData['f_gaia_dr3'] = None
                if curLine[0] == 'Gaia' and curLine[1] == "EDR4":
                    if len(curLine) > 3:
                        val = curLine[3]
                        newData['f_gaia_edr4'] = val
                        newData['f_all_names'] += ", Gaia EDR4 " + val
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = "Gaia EDR4 " + val
                    else:
                        newData['f_gaia_edr4'] = None
                if curLine[0] == 'Gaia' and curLine[1] == "DR4":
                    if len(curLine) > 3:
                        val = curLine[3]
                        newData['f_gaia_dr4'] = val
                        newData['f_all_names'] += ", Gaia DR4 " + val
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = "Gaia DR4 " + val
                    else:
                        newData['f_gaia_dr4'] = None
                if curLine[0] == 'Gaia' and curLine[1] == "EDR5":
                    if len(curLine) > 3:
                        val = curLine[3]
                        newData['f_gaia_edr5'] = val
                        newData['f_all_names'] += ", Gaia EDR5 " + val
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = "Gaia EDR5 " + val
                    else:
                        newData['f_gaia_edr5'] = None
                if curLine[0] == 'Gaia' and curLine[1] == "DR5":
                    if len(curLine) > 3:
                        val = curLine[3]
                        newData['f_gaia_dr5'] = val
                        newData['f_all_names'] += ", Gaia DR5 " + val
                        if 'f_preferred_name' not in newData:
                            newData['f_preferred_name'] = "Gaia DR5 " + val
                    else:
                        newData['f_gaia_dr5'] = None
                if curLine[0] == 'TYC':
                    if len(curLine) > 2:
                        val = curLine[2]
                        newData['f_tyc'] = val
                        newData['f_all_names'] += ", TYC " + val
                    else:
                        newData['f_tyc'] = None
                if curLine[0] == 'Other':
                    if len(curLine) > 2:
                        val = " ".join(curLine[2:])
                        newData['f_other_names'] = val
                        newData['f_all_names'] += ", " + val
                        if 'f_preferred_name' not in newData:
                            # find the WDS name first
                            other_names = val.split(",")
                            for name in other_names:
                                if name.strip().startswith("WDS"):
                                    newData['f_preferred_name'] = name.strip()
                                    break
                            else:
                                # use the first name given
                                newData['f_preferred_name'] = other_names[0].strip()
                                # if len(other_names) > 1:
                                #    newData['f_preferred_name'] += " ..."
                    else:
                        newData['f_other_names'] = None
                if curLine[0] == 'dist':
                    if len(curLine) > 3:
                        val = float(curLine[3])
                        newData['f_dist'] = val
                    else:
                        newData['f_dist'] = None
                if curLine[0] == 'Spec':
                    if len(curLine) > 3:
                        val = curLine[3]
                        newData['f_spec'] = val
                    else:
                        newData['f_spec'] = None
                if curLine[0] == 'Vmag':
                    if len(curLine) > 2:
                        val = float(curLine[2])
                        newData['f_vmag'] = val
                    else:
                        newData['f_vmag'] = None
                if curLine[0] == 'Bmag':
                    if len(curLine) > 2:
                        val = float(curLine[2])
                        newData['f_bmag'] = val
                    else:
                        newData['f_bmag'] = None
                if curLine[0] == 'B-V':
                    if len(curLine) > 2:
                        val = curLine[2]
                        if (val != 'nan'):
                            newData['f_bv'] = float(val)
                        else:
                            newData['f_bv'] = None
                    else:
                        newData['f_bv'] = None
                if curLine[0] == 'RA' and curLine[1] != 'proper':
                    if len(curLine) > 2:
                        val = float(curLine[2])
                        newData['f_ra'] = val
                    else:
                        newData['f_ra'] = None
                if curLine[0] == 'RA' and curLine[1] == 'proper':
                    if len(curLine) > 4:
                        val = float(curLine[4])
                        newData['f_ra_proper_motion'] = val
                    else:
                        newData['f_ra_proper_motion'] = None
                if curLine[0] == 'Dec' and curLine[1] != 'proper':
                    if len(curLine) > 2:
                        val = float(curLine[2])
                        newData['f_dec'] = val
                if curLine[0] == 'Dec' and curLine[1] == 'proper':
                    if len(curLine) > 4:
                        val = float(curLine[4])
                        newData['f_dec_proper_motion'] = val
                    else:
                        newData['f_dec_proper_motion'] = None
                if curLine[0] == 'Position':
                    if len(curLine) > 2:
                        x = curLine[2]
                        y = curLine[3]
                        z = curLine[4]
                        x = float(x[1:len(x) - 1])
                        y = float(y[0:len(y) - 1])
                        z = float(z[0:len(z) - 1])
                        newData['f_x'] = x
                        newData['f_y'] = y
                        newData['f_z'] = z
                    else:
                        newData['f_x'] = None
                        newData['f_y'] = None
                        newData['f_z'] = None
                if curLine[0] == 'Disk':
                    if len(curLine) > 2:
                        val = curLine[2]
                        newData['f_disk'] = val
                    else:
                        newData['f_disk'] = None
                if curLine[0] == 'UVW':
                    if len(curLine) > 2:
                        u = curLine[2]
                        v = curLine[3]
                        w = curLine[4]
                        u = float(u[1:len(u) - 1])
                        v = float(v[0:len(v) - 1])
                        w = float(w[0:len(w) - 1])
                        if u == 9999.0:
                            u = None
                        if v == 9999.0:
                            v = None
                        if w == 9999.0:
                            w = None
                        newData['f_u'] = u
                        newData['f_v'] = v
                        newData['f_w'] = w
                    else:
                        newData['f_u'] = None
                        newData['f_v'] = None
                        newData['f_w'] = None
                if curLine[0] == 'Teff':
                    if len(curLine) > 2:
                        val = curLine[2]
                        if (val != 'nan'):
                            newData['f_teff'] = float(val)
                        else:
                            newData['f_teff'] = None
                    else:
                        newData['f_teff'] = None
                if curLine[0] == 'logg':
                    if len(curLine) > 2:
                        val = curLine[2]
                        if (val != 'nan'):
                            newData['f_logg'] = float(val)
                        else:
                            newData['f_logg'] = None
                    else:
                        newData['f_logg'] = None
                if curLine[0] == 'mass':
                    if len(curLine) > 3:
                        val = float(curLine[3])
                        newData['f_mass'] = val
                    else:
                        newData['f_mass'] = None
                if curLine[0] == 'radius':
                    if len(curLine) > 3:
                        val = float(curLine[3])
                        newData['f_radius'] = val
                    else:
                        newData['f_radius'] = None
                if curLine[0] == 'Number':
                    if len(curLine) > 4:
                        val = int(curLine[4])
                        newData['f_number_of_planets'] = val
                    else:
                        newData['f_number_of_planets'] = None
                # Added planets stuffs
                if curLine[0][0] == '[':
                    planet = copy.deepcopy(blankPlanet)

                    name = curLine[0]
                    name = name.replace("[", "")
                    name = name.replace("]", "")
                    planet['f_name'] = name

                    if "M_p" in curLine:
                        mp_index = curLine.index("M_p")  # normally 1
                        planet['f_m_p'] = float(curLine[mp_index + 1])
                        mp_err = curLine[mp_index + 3]
                        mp_err = mp_err.replace("}(M_J),", "")
                        mp_err = mp_err.replace("{", "")
                        mp_err = mp_err.split(",")
                        planet['f_m_p_min_err'] = floatable(mp_err[1])
                        planet['f_m_p_max_err'] = floatable(mp_err[0])
                        planet['f_m_p_err'] = maxable(planet['f_m_p_min_err'], planet['f_m_p_max_err'])
                    else:
                        planet['f_m_p_min_err'] = None
                        planet['f_m_p_max_err'] = None
                        planet['f_m_p_err'] = None

                    if "P" in curLine:
                        p_index = curLine.index("P")  # normally 5
                        planet['f_p'] = float(curLine[p_index + 1])
                        p_err = curLine[p_index + 3]
                        p_err = p_err.replace("}(d),", "")
                        p_err = p_err.replace("{", "")
                        p_err = p_err.split(",")
                        planet['f_p_min_err'] = floatable(p_err[1])
                        planet['f_p_max_err'] = floatable(p_err[0])
                        planet['f_p_err'] = maxable(planet['f_p_min_err'], planet['f_p_max_err'])
                    else:
                        planet['f_p_min_err'] = None
                        planet['f_p_max_err'] = None
                        planet['f_p_err'] = None

                    if "e" in curLine:
                        e_index = curLine.index("e")  # normally 9
                        planet['f_e'] = float(curLine[e_index + 1])
                        e_err = curLine[e_index + 3]
                        e_err = e_err.replace("},", "")
                        e_err = e_err.replace("{", "")
                        e_err = e_err.split(",")
                        planet['f_e_min_err'] = floatable(e_err[1])
                        planet['f_e_max_err'] = floatable(e_err[0])
                        planet['f_e_err'] = maxable(planet['f_e_min_err'], planet['f_e_max_err'])
                    else:
                        planet['f_e_min_err'] = None
                        planet['f_e_max_err'] = None
                        planet['f_e_err'] = None

                    if "a" in curLine:
                        a_index = curLine.index("a")  # normally 13
                        planet['f_a'] = float(curLine[a_index + 1])
                        a_err = curLine[a_index + 3]
                        a_err = a_err.replace("}(AU)", "")
                        a_err = a_err.replace("{", "")
                        a_err = a_err.split(",")
                        planet['f_a_min_err'] = floatable(a_err[1])
                        planet['f_a_max_err'] = floatable(a_err[0])
                        planet['f_a_err'] = maxable(planet['f_a_min_err'], planet['f_a_max_err'])
                    else:
                        planet['f_a_min_err'] = None
                        planet['f_a_max_err'] = None
                        planet['f_a_err'] = None

                    newPlanetData[name] = planet

                if curLine[0][-1] == 'H':  # checking for elements data
                    version = ''
                    element = curLine[0]

                    if (curLine[1] == '(NLTE)'):
                        curLine.pop(1)
                        newNLTE.append(1)
                    else:
                        newNLTE.append(0)

                    elementValue = float(curLine[1])
                    author = curLine[2][1:len(curLine[2])]  # gets rid of [
                    for i in range(3, len(curLine)):
                        if curLine[i][0] != '(':
                            author = author + ' ' + curLine[i]

                    year = curLine[len(curLine) - 1]  # isolates year
                    year = year.replace("(", "")
                    year = year.replace(")", "")
                    year = year.replace("]", "")

                    tmpYr = year

                    year = year.replace("-Li", "")

                    if tmpYr != year:
                        li = True
                    else:
                        li = False

                    tmpYr = year

                    for letter in "abcdefghijklmnopqrstuvwxyz":
                        year = year.replace(letter, "")
                        if tmpYr != year:
                            version = letter

                    year = year.replace(",", "")

                    newElement.append(element)
                    newAuthor.append(author)
                    newYear.append(year)
                    newVersion.append(version)
                    newLi.append(li)
                    newElementValue.append(elementValue)
            if len(curLine) == 0 or curPos == numberOfChars:
                starId = []
                hipNum = newData['f_hip']
                if 'f_preferred_name' not in newData:
                    if "TYS" in newData:
                        newData['f_preferred_name'] = newData['TYS']
                    else:
                        newData['f_preferred_name'] = "No name given"
                if (hipNum != None):
                    print(("Adding star #%s: %s" % (starNo, hipNum)))
                    starNo = starNo + 1
                    hashable_star_id_key = 'starid-%s' % hipNum
                    if hashtable.get(hashable_star_id_key):
                        starId = hashtable[hashable_star_id_key]
                    else:
                        # db.t_star.update_or_insert(db.t_star.f_hip == hipNum, **newData)
                        sqlite.insert_into_table("t_star", data_dict=newData)
                        hashtable['star-%s' % hipNum] = newData
                        # star = db(db.t_star.f_hip == newData['f_hip']).select()
                        star = sqlite.get_table_data_from_key(table_name="t_star", column_name='f_hip',
                                                              column_value=newData['f_hip'])
                        for row in star:
                            starId.append(row.id)
                        hashtable[hashable_star_id_key] = starId

                for i in range(0, len(newNLTE)):
                    element_ = newElement[i]
                    nlte_ = newNLTE[i]
                    elementValue_ = newElementValue[i]
                    author_ = newAuthor[i]
                    version_ = newVersion[i]
                    li_ = newLi[i]
                    year_ = str(newYear[i])
                    version = newVersion[i]
                    hashable_element_id_key = 'elementid-%s' % element_
                    if hashable_element_id_key in hashtable.keys():
                        elemId = hashtable[hashable_element_id_key]
                    else:
                        # db.t_element.update_or_insert(db.t_element.f_name == element_, f_name=element_)
                        sqlite.insert_into_table("t_element", data_dict={
                            'f_name': element_,
                        })
                        hashtable['element-%s' % element_] = 1
                        # elem = db(db.t_element.f_name == element_).select()
                        elem = sqlite.get_table_data_from_key(table_name="t_element", column_name='f_name',
                                                              column_value=element_)
                        elemId = []
                        for row in elem:
                            elemId.append(row.id)
                        hashtable[hashable_element_id_key] = elemId
                    hashtable_catalogue_id_key = 'catalogueid-%s-%s-%s-%s' % (author_, year_, version_, li_)
                    if hashtable_catalogue_id_key in hashtable.keys():
                        catId = hashtable[hashtable_catalogue_id_key]
                    else:
                        # db.t_catalogue.update_or_insert(
                        #     (db.t_catalogue.f_author == author_) &
                        #     (db.t_catalogue.f_year == year_) &
                        #     (db.t_catalogue.f_version == version_) &
                        #     (db.t_catalogue.f_li == li_),
                        #     f_author=author_,
                        #     f_year=year_,
                        #     f_version=version_,
                        #     f_li=li_)
                        sqlite.insert_into_table("t_catalogue", data_dict={
                            'f_author': author_,
                            'f_year': year_,
                            'f_version': version_,
                            'f_li': li_
                        })
                        hashtable["catalogue-%s-%s-%s-%s" % (author_, year_, version_, li_)] = 1
                        # cat = db((db.t_catalogue.f_author == author_) & (db.t_catalogue.f_year == year_) & (
                        #         db.t_catalogue.f_version == version_)).select()
                        cat = sqlite.get_table_data_from_compound_keys(table_name="t_catalogue", key_value_dict={
                            'f_author': author_,
                            'f_year': year_,
                            'f_version': version_,
                        })
                        catId = []
                        for row in cat:
                            catId.append(row.id)
                        hashtable[hashtable_catalogue_id_key] = catId
                    found = True
                    count = 0
                    while found:
                        hashable_composition_id_key = '%s-%s-%s-%s-%s-%s-%s' % \
                                                    (solarnorm, starId[0], hipNum, catId[0], elemId[0], nlte_, count)
                        if hashable_composition_id_key in compositions.keys():
                            count += 1
                        else:
                            found = False
                    compositions[hashable_composition_id_key] = elementValue_

                for plannet_letter, per_planet_data in newPlanetData.items():
                    star_index = starId[0]
                    hashable_planet_id_key = 'planetid-%s-%s' % (star_index, plannet_letter)
                    if hashable_planet_id_key not in hashtable.keys():
                        # db.t_planet.update_or_insert(
                        #     (db.t_planet.f_star == starId[0]) &
                        #     (db.t_planet.f_name == name) &
                        #     (db.t_planet.f_m_p == mp) &
                        #     (db.t_planet.f_m_p_min_err == mpminerr) &
                        #     (db.t_planet.f_m_p_max_err == mpmaxerr) &
                        #     (db.t_planet.f_m_p_err == mperr) &
                        #     (db.t_planet.f_p == p) &
                        #     (db.t_planet.f_p_min_err == pminerr) &
                        #     (db.t_planet.f_p_max_err == pmaxerr) &
                        #     (db.t_planet.f_p_err == perr) &
                        #     (db.t_planet.f_e == e) &
                        #     (db.t_planet.f_e_min_err == eminerr) &
                        #     (db.t_planet.f_e_max_err == emaxerr) &
                        #     (db.t_planet.f_e_err == eerr) &
                        #     (db.t_planet.f_a == a) &
                        #     (db.t_planet.f_a_min_err == aminerr) &
                        #     (db.t_planet.f_a_max_err == amaxerr) &
                        #     (db.t_planet.f_a_err == aerr),
                        #     f_star=starId[0],
                        #     **(newPlanetData[key]))
                        planet_dict = {'f_star': star_index, **per_planet_data}
                        sqlite.insert_into_table("t_planet", data_dict=planet_dict)
                        hashtable[hashable_planet_id_key] = per_planet_data

                newData = copy.deepcopy(blankNewData)
                newAuthor = []
                newYear = []
                newElement = []
                newNLTE = []
                newVersion = []
                newLi = []
                newElementValue = []
                newPlanetData = {}
    # db(db.t_star.f_hip == None).delete()
    hashtable.close()
    compositions.close()
    # db.commit()
    pickle_to_hdf5(HYP_DATA_DIR, solarnorm)
    return "Done"


def try_int(s):
    try:
        return int(s)
    except ValueError:
        return s


def pickle_to_hdf5(HYP_DATA_DIR: str, solarnorm: int):
    compositions_tbl = []
    print("Selecting data...")
    compositions = PersistentDict(os.path.join(HYP_DATA_DIR, "compositions-%s.shelf" % solarnorm))
    print("Building table...")
    for row in compositions.keys():
        rowspl = [int(item) for item in row.split("-")] + [compositions[row]]
        compositions_tbl.append(rowspl)
    print("Building dataframe...")
    cache = pd.DataFrame(compositions_tbl,
                         columns=["solarnorm", "star_id", "star_hip", "catalogue", "element", "nlte", "count", "value"])
    print("Saving...")
    cache.to_hdf(os.path.join(HYP_DATA_DIR, "compositions.%s.h5" % solarnorm), 'compositions')


def update_one_norm(norm: str, test_mode: bool = False):
    if test_mode:
        compositions_dir = test_database_dir
    else:
        compositions_dir = hdf5_data_dir
    today_date = datetime.now().strftime("%Y_%m_%d")
    if norm == "absolute":
        filename = f'hypatia_{today_date}_exo_absolute.txt'
    elif norm == "original":
        filename = f'hypatia_{today_date}_exo_normOriginal.txt'
    else:
        filename = f'hypatia_{today_date}_exo_norm{norm}.txt'
    upload_star_data(
        HYP_DATA_DIR=compositions_dir,
        filePath=os.path.join(star_data_output_dir, filename),
        solarnorm=outputs_dict[norm],
        test_mode=test_mode,
    )