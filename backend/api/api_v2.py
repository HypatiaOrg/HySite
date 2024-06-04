


def composition_query(request, requested_star_names, elements, solarnorms):

    # # star data query
    if type(requested_star_names) != list:
        requested_star_names = [requested_star_names]
    # get a unique set of star names that were requested
    requested_star_names_unique = list(set(requested_star_names))
    # a query for all the stars in the database return a table with the field f_hip, f_all_names, f_preferred_name
    stars = db(db.t_star.id > 0).select(db.t_star.f_hip, db.t_star.f_all_names, db.t_star.f_preferred_name)
    # get the unique database id for each unique star name requested
    star_db_ids_unique = {}
    for request_index, requested_star_name_unique in list(enumerate(requested_star_names_unique)):
        star = stars.find(lambda s: s.f_hip == intable(requested_star_name_unique))
        found_star_id = None
        if star:
            found_star_id = star.first().f_hip
        else:
            star = stars.find(lambda s: requested_star_name_unique in s.f_all_names)
            if star:
                found_star_id = star.first().f_hip
        star_db_ids_unique[requested_star_name_unique] = found_star_id
        # print('unique requested star name', request_index + 1, requested_star_name_unique, "found star id", found_star_id)
    # put the star database ids in the same order as the requested star names
    star_db_ids = [star_db_ids_unique[a_requested_star_name] for a_requested_star_name in requested_star_names]

    # # element data query
    if type(elements) != list:
        elements = [elements]
    # get a unique set of elements that were requested
    element_to_formatted_element = {}
    formatted_element_to_element = {}
    elements_unique = set()
    for an_element in elements:
        formatted_element = an_element.strip().lower()
        if formatted_element[-1] != "h" or formatted_element in {'bh', 'rh'}:
            formatted_element += "h"
        elements_unique.add(formatted_element)
        element_to_formatted_element[an_element] = formatted_element
        formatted_element_to_element[formatted_element] = an_element
    # a query for all the elements in the database return a table with the field f_name
    elements_id_unique = {}
    element_names_by_element_id = {}
    for element_index, element_unique in list(enumerate(elements_unique)):
        element_id_found = db(db.t_element.f_name.like(element_unique, case_sensitive=False)).select().first().id
        elements_id_unique[element_unique] = element_id_found
        element_names_by_element_id[element_id_found] = formatted_element_to_element[element_unique]
        # print('requested element', element_index + 1, element_unique, "found element id", element_id_found)
    element_ids = [elements_id_unique[element_to_formatted_element[an_element]] for an_element in elements]

    # # solarnorm data query
    if solarnorms == None:
        solarnorms = ["lod09"] * len(requested_star_names)
    elif type(solarnorms) != list:
        solarnorms = [solarnorms]
    # get a unique set of solarnorms that were requested
    solarnorms_unique = list(set(solarnorms))
    # a query for all the solarnorms in the database return a table with the field f_identifier
    solarnorm_ids_unique = {}
    solarnorm_names_by_solarnorm_id = {}
    for solarnorm_index, solarnorm_unique in list(enumerate(solarnorms_unique)):
        solarnorm_id_found = db(
            db.t_solarnorm.f_identifier.like(solarnorm_unique, case_sensitive=False)).select().first().id
        solarnorm_ids_unique[solarnorm_unique] = solarnorm_id_found
        solarnorm_names_by_solarnorm_id[solarnorm_id_found] = solarnorm_unique
        # print('unique requested solarnorm', solarnorm_index + 1, solarnorm_unique, "found solarnorm id", solarnorm_id_found)
    # put the solarnorm database ids in the same order as the requested solarnorms
    solarnorm_ids = [solarnorm_ids_unique[a_solarnorm] for a_solarnorm in solarnorms]
    # # composition data query
    result_dict = {}
    solarnorm_id_current = None
    star_db_id_current = None
    compositions_per_norm = None
    compositions_per_star = None
    preferred_star_name = None
    all_star_names = None
    solarnorm_name = None
    last_updated = None
    # sort the data by solarnorm_id then star_db_id to make a more efficient query
    for solarnorm_id, star_db_id, element_id in sorted(zip(solarnorm_ids, star_db_ids, element_ids)):
        # print(solarnorm_id, star_db_id, element_id)
        # elemental compositions are available on a per solarnorm basis
        if solarnorm_id != solarnorm_id_current:
            # get the elemental data for the requested solarnorm
            norm_path = os.path.join(HYP_DATA_DIR, "compositions.%s.h5" % solarnorm_id)
            compositions_per_norm = pd.read_hdf(norm_path, "compositions")
            solarnorm_name = solarnorm_names_by_solarnorm_id[solarnorm_id]
            last_updated = round(os.path.getmtime(norm_path))
            solarnorm_id_current = solarnorm_id
            # print('Loaded solarnorm: %s' % solarnorm_names_by_solarnorm_id[solarnorm_id])
        if star_db_id != star_db_id_current:
            # get the per star elemental data
            compositions_per_star = compositions_per_norm[compositions_per_norm.star_hip == star_db_id]
            names_this_star = stars.find(lambda s: s.f_hip == star_db_id).first()
            preferred_star_name = names_this_star.f_preferred_name
            all_star_names = names_this_star.f_all_names.split(", ")[1:]
            star_db_id_current = star_db_id
            # print('Loaded star database id: %s' % star_db_id)
        # get the elemental data for the requested element
        element_info = compositions_per_star[compositions_per_star.element == element_id]
        # set the result
        result_dict[(solarnorm_id, star_db_id, element_id)] = package_element_info(
            element_info=element_info,
            preferred_name=preferred_star_name,
            all_names=all_star_names,
            star_db_id=star_db_id,
            element_name=element_names_by_element_id[element_id],
            solarnorm_name=solarnorm_name,
            request=request,
            for_nea=False,
        )
    # return the data in the same order as the requested data
    result = [result_dict[(solarnorm_id, star_db_id, element_id)]
              for solarnorm_id, star_db_id, element_id in zip(solarnorm_ids, star_db_ids, element_ids)]
    return result



def api_defs(request):
    # # reaching this point means we have an authorized request, now we work to return the requested data
    noun = request.args[0]
    result = []
    if noun == "element":
        elements = db(db.t_element.id > 0).select()
        for element in elements:
            result.append(element.f_name)
    elif noun == "catalog":
        catalogs = db(db.t_catalogue.id > 0).select()
        for catalog in catalogs:
            result.append({
                "id": catalog.id,
                "author": catalog.f_author,
                "year": catalog.f_year,
                "version": catalog.f_version,
                "li": catalog.f_li == "True",
                "override_name": catalog.f_display_name
            })
    elif noun == "star":
        starlist = []
        if request.vars.hip:
            if isinstance(request.vars.hip, list):
                for hip in request.vars.hip:
                    starlist.append({"hip": hip})
            else:
                starlist.append({"hip": request.vars.hip})
        if request.vars.name:
            if isinstance(request.vars.name, list):
                for name in request.vars.name:
                    starlist.append({"name": name})
            else:
                starlist.append({"name": request.vars.name})
        if request.vars.hd:
            if isinstance(request.vars.hd, list):
                for hd in request.vars.hd:
                    starlist.append({"hd": hd})
            else:
                starlist.append({"hd": request.vars.hd})
        if request.vars.bd:
            if isinstance(request.vars.bd, list):
                for bd in request.vars.bd:
                    starlist.append({"bd": bd})
            else:
                starlist.append({"bd": request.vars.bd})
        if request.vars.twomass:
            if isinstance(request.vars.twomass, list):
                for twomass in request.vars.twomass:
                    starlist.append({"twomass": twomass})
            else:
                starlist.append({"twomass": request.vars.twomass})
        if request.vars.gaiadr2:
            if isinstance(request.vars.gaiadr2, list):
                for gaiadr2 in request.vars.gaiadr2:
                    starlist.append({"gaiadr2": gaiadr2})
            else:
                starlist.append({"gaiadr2": request.vars.gaiadr2})
        if request.vars.tyc:
            if isinstance(request.vars.tyc, list):
                for tyc in request.vars.tyc:
                    starlist.append({"tyc": tyc})
            else:
                starlist.append({"tyc": request.vars.tyc})
        if request.vars.other:
            if isinstance(request.vars.other, list):
                for other in request.vars.other:
                    starlist.append({"other": other})
            else:
                starlist.append({"other": request.vars.other})
        for star in starlist:
            if "v2" in request.url:
                result_not_found = {"status": "not-found"}
            else:
                result_not_found = {"status": "not-found",
                                    "hip": None,
                                    "hd": None,
                                    "bd": None,
                                    "spec": None,
                                    "vmag": None,
                                    "bv": None,
                                    "dist": None,
                                    "ra": None,
                                    "dec": None,
                                    "x": None,
                                    "y": None,
                                    "z": None,
                                    "disk": None,
                                    "u": None,
                                    "v": None,
                                    "w": None,
                                    "teff": None,
                                    "logg": None,
                                    "2MASS": None,
                                    "ra_proper_motion": None,
                                    "dec_proper_motion": None,
                                    "bmag": None,
                                    "planets": None}
            if "hip" in star:
                stardata = db(db.t_star.f_hip == star['hip']).select().first()
                if stardata:
                    result.append(stardata)
                else:
                    result_not_found['hip'] = int(star['hip'])
                    result.append(result_not_found)
            if "name" in star:
                stardata = db(db.t_star.f_all_names.contains(star['name'])).select().first()
                if stardata:
                    result.append(stardata)
                else:
                    result_not_found['name'] = star['name']
                    result.append(result_not_found)
            if "hd" in star:
                stardata = db(db.t_star.f_hd == star['hd']).select().first()
                if stardata:
                    result.append(stardata)
                else:
                    result_not_found['hd'] = star['hd']
                    result.append(result_not_found)
            if "bd" in star:
                stardata = db(db.t_star.f_bd == star['bd']).select().first()
                if stardata:
                    result.append(stardata)
                else:
                    result_not_found['bd'] = star['bd']
                    result.append(result_not_found)
            if "twomass" in star:
                stardata = db(db.t_star.f_2mass == star['twomass'].replace("plus", "+")).select().first()
                if stardata:
                    result.append(stardata)
                elif "v2" in request.url:
                    result_not_found['2mass'] = star['twomass']
                    result.append(result_not_found)
                else:
                    result_not_found['2MASS'] = star['twomass']
                    result.append(result_not_found)
            if "gaiadr2" in star:
                stardata = db(db.t_star.f_gaia_dr2 == star['gaiadr2']).select().first()
                if stardata:
                    result.append(stardata)
                else:
                    result_not_found['gaia_dr2'] = star['gaiadr2']
                    result.append(result_not_found)
            if "tyc" in star:
                stardata = db(db.t_star.f_tyc == star['tyc']).select().first()
                if stardata:
                    result.append(stardata)
                else:
                    result_not_found['tyc'] = star['tyc']
                    result.append(result_not_found)
            if "other" in star:
                stardata = db(db.t_star.f_other_names.contains(star['other'])).select().first()
                if stardata:
                    result.append(stardata)
                else:
                    result_not_found['other_name'] = star['other']
                    result.append(result_not_found)
        for i in range(len(result)):
            if not isinstance(result[i], dict):
                stardata = result[i]
                planetdata = db(db.t_planet.f_star == stardata.id).select()
                planets = []
                for planet in planetdata:
                    if "v2" in request.url:
                        planets.append({
                            "name": planet.f_name,
                            "m_p": planet.f_m_p,
                            "m_p_min_err": planet.f_m_p_min_err,
                            "m_p_max_err": planet.f_m_p_max_err,
                            "p": planet.f_p,
                            "p_min_err": planet.f_p_min_err,
                            "p_max_err": planet.f_p_max_err,
                            "e": planet.f_e,
                            "e_min_err": planet.f_e_min_err,
                            "e_max_err": planet.f_e_max_err,
                            "a": planet.f_a,
                            "a_min_err": planet.f_a_min_err,
                            "a_max_err": planet.f_a_max_err,
                        })
                    else:
                        planets.append({
                            "name": planet.f_name,
                            "m_p": planet.f_m_p,
                            "m_p_min_err": planet.f_m_p_min_err,
                            "m_p_max_err": planet.f_m_p_max_err,
                            "m_p_err": planet.f_m_p_err,
                            "p": planet.f_p,
                            "p_min_err": planet.f_p_min_err,
                            "p_max_err": planet.f_p_max_err,
                            "p_err": planet.f_p_err,
                            "e": planet.f_e,
                            "e_min_err": planet.f_e_min_err,
                            "e_max_err": planet.f_e_max_err,
                            "e_err": planet.f_e_err,
                            "a": planet.f_a,
                            "a_min_err": planet.f_a_min_err,
                            "a_max_err": planet.f_a_max_err,
                            "a_err": planet.f_a_err,
                        })
                result[i] = {
                    "name": stardata.f_preferred_name,
                    "hip": stardata.f_hipparcos,
                    "hd": stardata.f_hd_str,
                    "bd": stardata.f_bd,
                    "2mass": stardata.f_2mass,
                    "gaia_dr2": stardata.f_gaia_dr2,
                    "tyc": stardata.f_tyc,
                    "other_names": stardata.f_other_names,
                    "spec": stardata.f_spec,
                    "vmag": stardata.f_vmag,
                    "bv": stardata.f_bv,
                    "dist": stardata.f_dist,
                    "ra": stardata.f_ra,
                    "dec": stardata.f_dec,
                    "x": stardata.f_x,
                    "y": stardata.f_y,
                    "z": stardata.f_z,
                    "disk": stardata.f_disk,
                    "u": stardata.f_u,
                    "v": stardata.f_v,
                    "w": stardata.f_w,
                    "teff": stardata.f_teff,
                    "logg": stardata.f_logg,
                    "ra_proper_motion": stardata.f_ra_proper_motion,
                    "dec_proper_motion": stardata.f_dec_proper_motion,
                    "bmag": stardata.f_bmag,
                    "planets": planets,
                    "status": "found"
                }
                if "v2" in request.url:
                    result[i]['hd'] = stardata.f_hd_str
                else:
                    result[i]['hd'] = stardata.f_hd
                    result[i]['hd_letter'] = stardata.f_hd_letter
                    result[i]["2MASS"] = stardata.f_2mass
    elif noun == "composition":
        if request.vars.name:
            requested_star_names = request.vars.name
        else:
            requested_star_names = request.vars.hip
        elements = request.vars.element
        solarnorms = request.vars.solarnorm
        result = composition_query(requested_star_names, elements, solarnorms, request=request)

    elif noun == "data":
        inputs = Storage()
        for key in list(request.vars.keys()):
            inputs[key] = request.vars[key]
        inputs.filter1_1 = inputs.filter1_1 or "none"
        inputs.filter1_2 = inputs.filter1_2 or "H"
        inputs.filter2_1 = inputs.filter2_1 or "none"
        inputs.filter2_2 = inputs.filter2_2 or "H"
        inputs.filter3_1 = inputs.filter3_1 or "none"
        inputs.filter3_2 = inputs.filter3_2 or "H"
        inputs.xaxis1 = inputs.xaxis1 or "Fe"
        inputs.xaxis2 = inputs.xaxis2 or "H"
        inputs.yaxis1 = inputs.yaxis1 or "Si"
        inputs.yaxis2 = inputs.yaxis2 or "H"
        inputs.zaxis1 = inputs.zaxis1 or "none"
        inputs.zaxis2 = inputs.zaxis2 or "H"
        inputs.cat_action = inputs.cat_action or "exclude"
        inputs.statistic = inputs.statistic or "median"
        inputs.tablecols = inputs.tablecols or "Fe,C,O,Mg,Si,S,Ca,Ti"
        inputs.tablesource = inputs.tablesource or "graph"
        if type(inputs.tablecols) == str:
            inputs.tablecols = inputs.tablecols.split(",")
        if request.vars.graph_submit and not request.vars.xaxislog:
            inputs.xaxislog = False
        if request.vars.graph_submit and not request.vars.yaxislog:
            inputs.yaxislog = False
        if request.vars.graph_submit and not request.vars.zaxislog:
            inputs.zaxislog = False
        if request.vars.graph_submit and not request.vars.xaxisinv:
            inputs.xaxisinv = False
        if request.vars.graph_submit and not request.vars.yaxisinv:
            inputs.yaxisinv = False
        if request.vars.graph_submit and not request.vars.zaxisinv:
            inputs.zaxisinv = False
        if request.vars.graph_submit and not request.vars.filter1_inv:
            inputs.filter1_inv = False
        if request.vars.graph_submit and not request.vars.filter2_inv:
            inputs.filter2_inv = False
        if request.vars.graph_submit and not request.vars.filter3_inv:
            inputs.filter3_inv = False
        if request.vars.graph_submit and not request.vars.normalize:
            inputs.normalize = False
        if request.vars.graph_submit and not request.vars.catalogs:
            inputs.catalogs = []
        if request.vars.graph_submit and type(request.vars.catalogs) == str:
            inputs.catalogs = [request.vars.catalogs]
        if inputs.catalogs:
            inputs.catalogs = [intable(i, invalid=-1) for i in inputs.catalogs]
        if request.vars.mode != "hist":
            inputs.mode = "scatter"

        solarnorm = db(db.t_solarnorm.f_identifier == request.vars.solarnorm).select().first()
        try:
            inputs.solarnorm = int(solarnorm.id)
        except:
            solarnorm = db(db.t_solarnorm.f_author.contains("Lodders")).select().first()
            try:
                inputs.solarnorm = int(solarnorm.id)
            except:
                solarnorm = db(db.t_solarnorm.id > 0).select().first()
                inputs.solarnorm = int(solarnorm.id)

        catalogs = db(db.t_catalogue.id > 0).select(
            orderby=db.t_catalogue.f_author.lower() | db.t_catalogue.f_year | db.t_catalogue.f_version)

        # define variables
        elements = {}
        stellarProps = {}
        planetProps = {}
        filters = {}
        planetFilters = {}
        inputs.hipcode = None

        # which axes are needed?
        # histogram: X only
        # scatter: X, Y
        # scatter with color: X, Y, Z
        axes = ['xaxis']
        if inputs.mode == "scatter":
            axes.append('yaxis')
            if inputs.zaxis1 != "none":
                axes.append('zaxis')

        # filter the data
        if inputs.filter1_1 != "none" and (floatable(inputs.filter1_3) != None or floatable(inputs.filter1_4) != None):
            axes.append('filter1_')
            if inputs.filter1_1 in ["p", "m_p", "e", "a"]:
                planetFilters['filter1_'] = (
                floatable(inputs.filter1_3), floatable(inputs.filter1_4), inputs.filter1_inv)
            else:
                filters['filter1_'] = (floatable(inputs.filter1_3), floatable(inputs.filter1_4), inputs.filter1_inv)
        if inputs.filter2_1 != "none" and (floatable(inputs.filter2_3) != None or floatable(inputs.filter2_4) != None):
            axes.append('filter2_')
            if inputs.filter2_1 in ["p", "m_p", "e", "a"]:
                planetFilters['filter2_'] = (
                floatable(inputs.filter2_3), floatable(inputs.filter2_4), inputs.filter2_inv)
            else:
                filters['filter2_'] = (floatable(inputs.filter2_3), floatable(inputs.filter2_4), inputs.filter2_inv)
        if inputs.filter3_1 != "none" and (floatable(inputs.filter3_3) != None or floatable(inputs.filter3_4) != None):
            axes.append('filter3_')
            if inputs.filter3_1 in ["p", "m_p", "e", "a"]:
                planetFilters['filter3_'] = (
                floatable(inputs.filter3_3), floatable(inputs.filter3_4), inputs.filter3_inv)
            else:
                filters['filter3_'] = (floatable(inputs.filter3_3), floatable(inputs.filter3_4), inputs.filter3_inv)

        # handle axes
        for item in axes:
            elements[item + "1"] = db(db.t_element.f_name == inputs[item + "1"] + "H").select().first()
            if elements[item + "1"]:
                elements[item + "1"] = elements[item + "1"].id
                if inputs[item + "2"] != 'H':
                    elements[item + "2"] = db(db.t_element.f_name == inputs[item + "2"] + "H").select().first()
                    if elements[item + "2"]:
                        elements[item + "2"] = elements[item + "2"].id
            elif inputs.get(item + "1") in ["p", "m_p", "e", "a"]:
                planetProps[item] = inputs.get(item + "1")
            else:
                stellarProps[item] = inputs.get(item + "1")

        # get compositions
        compositions = pd.read_hdf(os.path.join(HYP_DATA_DIR, "compositions.%s.h5" % inputs.solarnorm), "compositions")

        # include/exclude catalogs
        if inputs.catalogs and inputs.cat_action == "exclude":
            compositions = compositions[~compositions.catalogue.isin(inputs.catalogs)]
        elif inputs.catalogs:
            compositions = compositions[compositions.catalogue.isin(inputs.catalogs)]

        # include/exclude stars
        if inputs.star_list:
            # convert all hds to hips
            if inputs.star_source == "hd":
                hdData = inputs.star_list.split(",")
                hipData = []
                stars = db(db.t_star.id > 0).select()
                for hd in hdData:
                    star = stars.find(lambda s: s.f_hd_string == hd)
                    if star:
                        hipData.append(star.first().f_hip)
                    else:
                        star = stars.find(lambda s: hd in s.f_all_names)
                        if star:
                            hipData.append(star.first().f_hip)
                    # print(repr(hipData))
            else:
                # build the list of hips
                hipDataWithNames = inputs.star_list.split(",")
                hipData = []
                stars = db(db.t_star.id > 0).select()
                for hip in hipDataWithNames:
                    star = stars.find(lambda s: s.f_hipparcos == intable(hip))
                    if star:
                        hipData.append(star.first().f_hip)
                    else:
                        star = stars.find(lambda s: hip in s.f_all_names)
                        if star:
                            hipData.append(star.first().f_hip)
                    # print(repr(hipData))
            if inputs.star_action == "exclude":
                compositions = compositions[~compositions.star_hip.isin(hipData)]
            else:
                compositions = compositions[compositions.star_hip.isin(hipData)]

        # get all the hips
        stars = db(db.t_star.id > 0).select(db.t_star.f_hip)
        hips = [star.f_hip for star in stars]

        # get planet/stellar properties
        hashTable = PersistentDict(os.path.join(HYP_DATA_DIR, "hashtable.shelf"))

        # get compositions relevant to scatter plot
        xy_data = compositions[compositions.element.isin(list(elements.values()))]

        # add abundances
        myStars = Stars()
        for abundance in xy_data.itertuples():
            myStars.addAbundance(abundance.star_hip, abundance.element, abundance.value)

        # generate outputs
        outputs = {'hip': [], 'name': []}
        for axis in axes:
            outputs[axis] = []
        value = {}
        for hip in hips:
            for item in axes:
                if item in planetProps:  # planet parameter
                    value[item] = random.randint(9000, 9999)  # we'll fill this out later
                    continue
                if item in stellarProps:  # stellar parameter
                    value[item] = hashTable['star-%s' % hip].get("f_" + stellarProps[item])
                    if value[item] == 9999:
                        value[item] = None
                    if value[item] == "thin":
                        value[item] = 0
                    if value[item] == "thick":
                        value[item] = 1
                    if value[item] == "N/A":
                        value[item] = None
                    if stellarProps[item] == "spec":
                        value[item] = spectype(value[item])
                    continue
                value[item] = myStars.getStatistic(hip, elements[item + "1"])  # element ratio
                if value[item] == None:
                    continue
                if item + "2" in elements:  # denominator is not H
                    value2 = myStars.getStatistic(hip, elements[item + "2"])
                    if value2 == None:
                        value[item] = None
                        continue
                    value[item] -= value2
            # only plot if there is a value for each axis and it matches the filter
            if (all([value[axis] != None for axis in axes])
                    and all([check_filter(value[f], filters[f]) for f in filters])):
                for axis in axes:
                    outputs[axis].append(value[axis])
                outputs['hip'].append(hip)
                outputs['name'].append(hashTable['star-%s' % hip].get("f_preferred_name"))

        # if there are any planet parameters, then each data point should be
        # a planet as opposed to a star. Start the process again
        if len(planetProps) > 0:
            planet_outputs = {'hip': []}
            for axis in axes:
                planet_outputs[axis] = []
            value = {}
            hiplist = []
            for i in range(len(outputs['hip'])):
                starid = hashTable['starid-%s' % outputs['hip'][i]][0]
                for char in "bcdefghijklmnopqrstuvwxyz":
                    if "planetid-%s-%s" % (starid, char) not in hashTable:
                        break
                    for item in axes:
                        if item in planetProps:  # planet parameter
                            value[item] = hashTable['planetid-%s-%s' % (starid, char)].get("f_" + planetProps[item])
                            if value[item] == 999:
                                value[item] = None
                        else:  # leftover stellar parameter or element ratio
                            value[item] = outputs[item][i]
                    # only plot if there is a value for each axis and it matches the filter
                    if (all([value[axis] for axis in axes])
                            and all([check_filter(value[f], planetFilters[f]) for f in planetFilters])):
                        for axis in axes:
                            planet_outputs[axis].append(value[axis])
                        planet_outputs['hip'].append(str(outputs['hip'][i]) + char)
                        hiplist.append(outputs['hip'][i])
            outputs = planet_outputs
        else:
            hiplist = outputs['hip']

        # build the plot
        TOOLS = "crosshair,pan,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,tap,save,box_select,poly_select,lasso_select,"

        # build the labels
        labels = {}
        unique_labels = {}
        for axis in axes:
            if axis in stellarProps:
                labels[axis] = inputs.get(axis + "1")
            elif axis in planetProps:
                labels[axis] = inputs.get(axis + "1")
            else:
                labels[axis] = "[%s/%s]" % (inputs.get(axis + "1"), inputs.get(axis + "2"))
            if labels[axis] not in list(unique_labels.values()):
                unique_labels[axis] = labels[axis]

        # set the axis type: log or linear
        x_axis_type = (inputs.xaxislog and "log" or "linear")
        y_axis_type = (inputs.yaxislog and "log" or "linear")

        # if there is no data then return a message
        if len(outputs['xaxis']) == 0:
            result = {"count": 0}

        # histogram
        elif inputs.mode == "hist":
            # counts stars with planets
            with_planet = []
            for i in range(len(outputs['xaxis'])):
                getstarid = outputs['hip'][i]
                try:
                    getstarid = re.sub("[^0-9]", "", getstarid)
                except:
                    pass
                starid = hashTable['starid-%s' % getstarid][0]
                if ("planet-%s-b" % starid) in hashTable:
                    with_planet.append(outputs['xaxis'][i])
            # builds the histogram
            hist_all, edges = np.histogram(outputs['xaxis'], bins=20)
            hist_planet, edges = np.histogram(with_planet, bins=edges)
            # get maximum point on the histogram
            max_hist_all = float(max(hist_all))
            max_hist_planet = float(max(hist_planet))
            # normalize if necessary
            if inputs.normalize:
                hist_all = hist_all / max_hist_all
                hist_planet = hist_planet / max_hist_planet
                max_hist_all = 1
                max_hist_planet = 1
                labels['yaxis'] = "Relative Frequency"
                fill_alpha = 0.5
                line_alpha = 0.2
            else:
                labels['yaxis'] = 'Number of Stellar Systems'
                fill_alpha = 1
                line_alpha = 1
            result = {"all_hypatia": hist_all.tolist(), "exo_hosts": hist_planet.tolist(), "edges": edges.tolist(),
                      "labels": labels, "count": len(outputs['xaxis'])}
        else:  # Scatter
            for i in range(len(outputs['hip'])):
                point = {}
                for col in outputs:
                    point[col.replace("_", "")] = outputs[col][i]
                result.append(point)
            for col in labels:
                if "_" in col:
                    labels[col.replace("_", "")] = labels[col]
                    del (labels[col])
            result = {"values": result, "labels": labels, "count": len(outputs['xaxis'])}
            if "v2" in request.url:
                for item in result['values']:
                    del (item['hip'])
            else:
                for item in result['values']:
                    if not hashTable['star-%s' % item['hip']].get("f_hipparcos"):
                        item['hip'] = -9999
        result['solarnorm'] = {
            "identifier": solarnorm.f_identifier,
            "author": solarnorm.f_author,
            "year": solarnorm.f_year,
            "version": solarnorm.f_version,
            "notes": solarnorm.f_notes
        }
    elif noun == 'nea':
        solar_norm = 'lod09'
        elements = ['FeH', 'CH', 'OH', 'NaH', 'MgH', 'AlH', 'SiH', 'CaH', 'YH', 'BaIIH']
        # get the database ids for the requested solarnorm and elements
        solarnorm_id = db(db.t_solarnorm.f_identifier.like(solar_norm, case_sensitive=False)).select().first().id
        elements_id = [db(db.t_element.f_name.like(element, case_sensitive=False)).select().first().id
                       for element in elements]
        # get the elemental data for the requested solarnorm
        norm_path = os.path.join(HYP_DATA_DIR, "compositions.%s.h5" % solarnorm_id)
        compositions_per_norm = pd.read_hdf(norm_path, "compositions")
        last_updated = round(os.path.getmtime(norm_path))
        # a query for all the stars in the database return a table with the field f_hip, f_all_names, f_preferred_name
        stars = db(db.t_star.id > 0).select(db.t_star.id, db.t_star.f_hip,
                                            db.t_star.f_all_names, db.t_star.f_preferred_name)
        # get all the stars with planets
        star_id_with_planets = sorted({row['f_star'] for row in db(db.t_planet.f_star != None).select('f_star')})
        star_id_with_planets_test_set = set(star_id_with_planets)
        # get all the star ids
        star_ids_all = sorted({row['id'] for row in db(db.t_star.id != None).select('id')})
        for star_id in star_ids_all:
            # get the elemental compositions for this star
            compositions_per_star = compositions_per_norm[compositions_per_norm.star_id == star_id]
            names_this_star = [row for row in stars.find(lambda row: row.id == star_id)][0]
            # names_this_star = stars.find(lambda s: s.id == star_id).first()
            preferred_star_name = names_this_star.f_preferred_name
            all_star_names = names_this_star.f_all_names.split(", ")[1:]
            # is this star a planet host?
            is_planet_host = star_id in star_id_with_planets_test_set
            for element_id, element_name in zip(elements_id, elements):
                # get the elemental data for the requested element
                element_info = compositions_per_star[compositions_per_star.element == element_id]
                # package the data to be returned
                result.append(package_element_info(
                    element_info=element_info,
                    preferred_name=preferred_star_name,
                    all_names=all_star_names,
                    star_db_id=star_id,
                    element_name=element_name,
                    solarnorm_name=solar_norm,
                    request=request,
                    for_nea=True,
                    is_planet_host=is_planet_host,
                ))
    else:
        raise KeyError("noun %s not recognized" % noun)


    response.headers['Content-Type'] = 'application/json'
    if "v1" in request.url:
        if type(result) == dict:
            result[
                'announcement'] = "Version 1 of the Hypatia Catalog has been deprecated and will be taken offline soon. Please test your code on version 2 of the API by replacing v1 with v2 in the URL. For more information, visit hypatiacatalog.com/api."
        elif type(result[0]) == dict:
            result[0][
                'announcement'] = "Version 1 of the Hypatia Catalog has been deprecated and will be taken offline soon. Please test your code on version 2 of the API by replacing v1 with v2 in the URL. For more information, visit hypatiacatalog.com/api."
    return json.dumps(result)
