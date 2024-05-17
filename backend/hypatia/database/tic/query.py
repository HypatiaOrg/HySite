import astroquery.mast


def query_tic_data(allowed_star_name: str):
    # preform the TIC database Query
    try:
        print(f'  Querying TIC for {allowed_star_name}')
        raw_tic_data = astroquery.mast.Catalogs.query_object(allowed_star_name, catalog="TIC", radius=0.0001)
    except astroquery.exceptions.ResolverError:
        # this is the error that happens when the star is not found.
        return None
    else:
        # broadcast the table data into a dictionary
        raw_tic_dict = dict(raw_tic_data)
        # clean the dictionary to reveal only the data
        tic_dict = {key: str(raw_tic_dict[key]).split("\n")[2:] for key in raw_tic_dict.keys()}
        if tic_dict["ID"]:
            return tic_dict
        return None
