# catalog read-in
allowed_name_types = {'Star', 'star', 'Stars', 'starname', 'Starname', 'Name', 'ID', 'Object', 'simbad_id'}

# catalog normalization
norm_keys_default = ['anders89', 'asplund05', 'asplund09', 'grevesse98', 'lodders09', 'original', 'grevesse07']

# star-names database
simbad_big_sleep_seconds = 30.0
simbad_small_sleep_seconds = 1.0
simbad_batch_size = 1000
default_reset_time_seconds = 60 * 60 * 24 * 365.24 * 3  # 3 years
no_simbad_reset_time_seconds = 60 * 60 * 24 * 365.24  # 1 year

# nea database
nea_ref = 'NASA Exoplanet Archive'
known_micro_names = {'kmt', 'ogle', 'moa', 'k2'}
system_designations = {'a', 'b', 'c', 'ab', 'ac', 'bc'}

# hacked stellar parameters, these will override any values from reference data.
hacked = {
    'Kepler-84': ('dist', 1443.26796, '[pc]', 'Hypatia Override for Kepler-84'),
}
# For these SIMBAD names, the API fails to return a few of the values that are available on the main website.
simbad_parameters_hack = {'Gaia DR2 4087838959097352064':
                              {'DEC': '-16 35 27.118803876'},
                          'BD+39 03309':
                              {'RA': '18 03 47.3520267264'},
                          }

# NEA provided names that return SIMBAD ids that refer a different part of a multiple star system.
# Example: Gaia DR2 4794830231453653888 is incorrectly associated with HD 41004B in the NEA sources,
# but this GAIA name is for HD 41004A, which also has an entry in the NEA sources.
# one line per star name that is causing the conflict
nea_names_the_cause_wrong_simbad_references = {
    'HD 132563',
    'Gaia DR2 4794830231453653888',
    'TIC 392045047', 'Oph 11',
    'TIC 1129033', # NEA NAME: WASP-77 A
    'HD 358155', 'TIC 442530946', # NEA NAME: WASP-70 A
    'TIC 122298563', 'Kepler-759', # NEA NAME: Kepler-759
    'HIP 14101', # LTT 1445 A
    'TIC 21113347', # HATS-58 A
    'TIC 37348844', 'NGTS-10', # NEA NAME: HATS-58 A
    'Gaia DR2 2106370541711607680', # NEA NAME: Kepler-983
    'TIC 454227159', '2MASS J11011926-7732383', # NEA NAME: 2MASS J11011926-7732383
    'Kepler-1855', # NEA NAME: Kepler-1855
    'TIC 122605766', 'Kepler-497',  # NEA NAME: Kepler-497
    'Kepler-1281', 'TIC 27458799', # NEA NAME: Kepler-1281
    'TIC 171098231', 'Kepler-1309', # NEA NAME: Kepler-1309
    'TIC 120764338', 'Kepler-1495', # NEA NAME: Kepler-1495
    'TIC 239291510', 'Kepler-1802', # NEA NAME: Kepler-1802
    'TIC 26541175', 'Kepler-1437', # NEA NAME: Kepler-1437
    'TIC 63285279', 'Kepler-1534', # NEA NAME: Kepler-1534
    'TIC 95431294',  # NEA NAME: gam1 Leo
    'TrES-1',
    'TrES-2',
    'TrES-3',
    'TrES-4',
    'TrES-5',
    'HIP 51260', 'TIC 165297570', #  NEA NAME: KELT-4 A
    'TIC 290131778',
    'TIC 158324245', 'KOI-13', #  NEA NAME: Gaia DR2 2130632159134827392
    'TIC 121656582', 'Kepler-1493', # NEA NAME: TIC 121656582
    'Kepler-1952', 'TIC 158635959',  # NEA NAME: Gaia DR2 2103115403182003328
    'TIC 380619414',  # NEA NAME: WASP-85 A
    'Kepler-645', 'TIC 159381747',  # NEA NAME: Gaia DR2 2126865575897687168
    'Kepler-650', 'TIC 158934047',  # NEA NAME: Gaia DR2 2127172919457889792
}