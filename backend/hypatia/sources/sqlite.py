import os
import sqlite3
import datetime
from typing import Optional, Union, Dict, Tuple

from hypatia.config import sqlite_data_dir, test_database_dir, hdf5_data_dir


hypatia_db_path = os.path.join(sqlite_data_dir, "storage.sqlite")
value_type = Union[int, float, str, bool, datetime.datetime, None]
table_strings = {
    "t_solarnorm":
    """
    CREATE TABLE t_solarnorm(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_author CHAR(512),
    f_year INTEGER,
    f_version CHAR(512),
    f_notes CHAR(512),
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE , "f_identifier" CHAR(512))
    """,
    "t_solarnorm_archive":
    """
    CREATE TABLE t_solarnorm_archive(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_author CHAR(512),
    f_year INTEGER,
    f_version CHAR(512),
    f_notes CHAR(512),
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    current_record INTEGER REFERENCES t_solarnorm (id) ON DELETE CASCADE  , "f_identifier" CHAR(512))
    """,
    "t_star":
    """
    CREATE TABLE t_star(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        f_hip INTEGER,
        f_hd INTEGER,
        f_bd CHAR(512),
        f_spec CHAR(512),
        f_vmag DOUBLE,
        f_bv DOUBLE,
        f_dist DOUBLE,
        f_ra DOUBLE,
        f_dec DOUBLE,
        f_x DOUBLE,
        f_y DOUBLE,
        f_z DOUBLE,
        f_disk CHAR(512),
        f_u DOUBLE,
        f_v DOUBLE,
        f_w DOUBLE,
        f_teff DOUBLE,
        f_logg DOUBLE,
        f_mass DOUBLE,
        f_radius DOUBLE,
        f_number_of_planets INTEGER,
        f_2mass CHAR(512),
        f_ra_proper_motion DOUBLE,
        f_dec_proper_motion DOUBLE,
        f_bmag DOUBLE,
        is_active CHAR(1),
        created_on TIMESTAMP,
        created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
        modified_on TIMESTAMP,
        modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  
    , "f_hd_str" CHAR(512), "f_preferred_name" CHAR(512), "f_other_names" CHAR(512), "f_gaia_dr4" CHAR(512), "f_gaia_edr4" CHAR(512), "f_gaia_edr5" CHAR(512), "f_gaia_dr5" CHAR(512), "f_gaia_dr2" CHAR(512), "f_gaia_dr3" CHAR(512), "f_tyc" CHAR(512), "f_gaia_edr3" CHAR(512), "f_hipparcos" INTEGER, "f_hd_letter" CHAR(512), "f_all_names" CHAR(512))
    """,
    "t_star_archive":
    """
    CREATE TABLE t_star_archive(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_hip INTEGER,
    f_hd INTEGER,
    f_bd CHAR(512),
    f_spec CHAR(512),
    f_vmag DOUBLE,
    f_bv DOUBLE,
    f_dist DOUBLE,
    f_ra DOUBLE,
    f_dec DOUBLE,
    f_x DOUBLE,
    f_y DOUBLE,
    f_z DOUBLE,
    f_disk CHAR(512),
    f_u DOUBLE,
    f_v DOUBLE,
    f_w DOUBLE,
    f_teff DOUBLE,
    f_logg DOUBLE,
    f_mass DOUBLE,
    f_radius DOUBLE,
    f_number_of_planets INTEGER,
    f_2mass CHAR(512),
    f_ra_proper_motion DOUBLE,
    f_dec_proper_motion DOUBLE,
    f_bmag DOUBLE,
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    current_record INTEGER REFERENCES t_star (id) ON DELETE CASCADE  , "f_hd_str" CHAR(512), "f_preferred_name" CHAR(512), "f_other_names" CHAR(512), "f_gaia_dr4" CHAR(512), "f_gaia_edr4" CHAR(512), "f_gaia_edr5" CHAR(512), "f_gaia_dr5" CHAR(512), "f_gaia_dr2" CHAR(512), "f_gaia_dr3" CHAR(512), "f_tyc" CHAR(512), "f_gaia_edr3" CHAR(512), "f_hipparcos" INTEGER, "f_hd_letter" CHAR(512), "f_all_names" CHAR(512))
    """,
    "t_element":
    """
    CREATE TABLE t_element(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_name CHAR(512),
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  )
    """,
    "t_element_archive":
    """
    CREATE TABLE t_element_archive(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_name CHAR(512),
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    current_record INTEGER REFERENCES t_element (id) ON DELETE CASCADE )
    """,
    "t_planet":
    """
    CREATE TABLE t_planet(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_name CHAR(512),
    f_star INTEGER REFERENCES t_star (id) ON DELETE CASCADE  ,
    f_m_p DOUBLE,
    f_m_p_err DOUBLE,
    f_p DOUBLE,
    f_p_err DOUBLE,
    f_e DOUBLE,
    f_e_err DOUBLE,
    f_a DOUBLE,
    f_a_err DOUBLE,
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  , "f_a_min_err" DOUBLE, "f_e_min_err" DOUBLE, "f_p_min_err" DOUBLE, "f_e_max_err" DOUBLE, "f_a_max_err" DOUBLE, "f_m_p_max_err" DOUBLE, "f_m_p_min_err" DOUBLE, "f_p_max_err" DOUBLE)
    """,
    "t_planet_archive":
    """
    CREATE TABLE t_planet_archive(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_name CHAR(512),
    f_star INTEGER REFERENCES t_star (id) ON DELETE CASCADE  ,
    f_m_p DOUBLE,
    f_m_p_err DOUBLE,
    f_p DOUBLE,
    f_p_err DOUBLE,
    f_e DOUBLE,
    f_e_err DOUBLE,
    f_a DOUBLE,
    f_a_err DOUBLE,
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    current_record INTEGER REFERENCES t_planet (id) ON DELETE CASCADE  , "f_a_min_err" DOUBLE, "f_e_min_err" DOUBLE, "f_p_min_err" DOUBLE, "f_e_max_err" DOUBLE, "f_a_max_err" DOUBLE, "f_m_p_max_err" DOUBLE, "f_m_p_min_err" DOUBLE, "f_p_max_err" DOUBLE)
    """,
    "t_catalogue":
    """
    CREATE TABLE t_catalogue(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_author CHAR(512),
    f_year INTEGER,
    f_version CHAR(512),
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  , f_li CHAR(512), f_display_name CHAR(512), "f_identifier" CHAR(512))
    """,
    "t_catalogue_archive":
    """
    CREATE TABLE t_catalogue_archive(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_author CHAR(512),
    f_year INTEGER,
    f_version CHAR(512),
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    current_record INTEGER REFERENCES t_catalogue (id) ON DELETE CASCADE  , f_li CHAR(512), f_display_name CHAR(512), "f_identifier" CHAR(512))
    """,
    "t_composition":
    """
    CREATE TABLE t_composition(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_solarnorm INTEGER REFERENCES t_solarnorm (id) ON DELETE CASCADE  ,
    f_star INTEGER REFERENCES t_star (id) ON DELETE CASCADE  ,
    f_catalogue INTEGER REFERENCES t_catalogue (id) ON DELETE CASCADE  ,
    f_element INTEGER REFERENCES t_element (id) ON DELETE CASCADE  ,
    f_nlte CHAR(1),
    f_value DOUBLE,
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  )
    """,
    "t_composition_archive":
    """
    CREATE TABLE t_composition_archive(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_author CHAR(512),
    f_year INTEGER,
    f_version CHAR(512),
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    current_record INTEGER REFERENCES t_composition (id) ON DELETE CASCADE  , f_li CHAR(512), f_display_name CHAR(512), "f_identifier" CHAR(512))
    """,
    "t_upload":
    """
    CREATE TABLE t_upload(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_file CHAR(512),
    f_solarnorm INTEGER REFERENCES t_solarnorm (id) ON DELETE CASCADE  ,
    f_uploaded CHAR(1),
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  )
    """,
    "t_upload_archive":
    """
    CREATE TABLE t_upload_archive(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_solarnorm INTEGER REFERENCES t_solarnorm (id) ON DELETE CASCADE  ,
    f_star INTEGER REFERENCES t_star (id) ON DELETE CASCADE  ,
    f_catalogue INTEGER REFERENCES t_catalogue (id) ON DELETE CASCADE  ,
    f_element INTEGER REFERENCES t_element (id) ON DELETE CASCADE  ,
    f_nlte CHAR(1),
    f_value DOUBLE,
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    current_record INTEGER REFERENCES t_upload (id) ON DELETE CASCADE  )
    """,
    "t_feedback":
    """
    CREATE TABLE t_feedback(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_name CHAR(512),
    f_email CHAR(512),
    f_message TEXT,
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  )
    """,
    "t_announcement":
    """
    CREATE TABLE t_announcement(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    f_message CHAR(512),
    is_active CHAR(1),
    created_on TIMESTAMP,
    created_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  ,
    modified_on TIMESTAMP,
    modified_by INTEGER REFERENCES auth_user (id) ON DELETE CASCADE  )
    """,
}


class AttributeDict:
    """A dictionary with attribute-style access. It maps attribute access to
    the real dictionary.
    """
    def __init__(self, initial_data: Dict[str, value_type]):
        for key in initial_data:
            setattr(self, key, initial_data[key])


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return AttributeDict(d)


class SQLite:
    def __init__(self, db_path: Optional[Union[str, None]] = None):
        if db_path is None:
            db_path = os.path.join(test_database_dir, "storage.sqlite")
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def query(self, query):
        self.cursor.execute(query)
        self.conn.commit()

    def fetchall_tables(self):
        query = "SELECT * FROM sqlite_master"
        self.query(query=query)
        return self.cursor.fetchall()

    def fetchall_from_table(self, table_name: str):
        query = f"SELECT * FROM {table_name}"
        self.query(query=query)
        return self.cursor.fetchall()

    def fetch_columns_from_table(self, table_name: str, column_names: Tuple[str]):
        query = f"SELECT {','.join(column_names)} FROM {table_name}"
        self.query(query=query)
        return self.cursor.fetchall()

    def create_all_tables(self):
        for table_string in table_strings.values():
            print(f"Creating table: {table_string[:min(50, len(table_string))]}")
            self.query(table_string)

    def create_table_from_name(self, table: str):
        self.query(table_strings[table])

    def insert_into_table(self, table_name: str, data_dict: Dict[str, value_type]):
        query = f"INSERT INTO {table_name} ("
        for key in data_dict.keys():
            query += f"{key}, "
        else:
            query = query[:-2]
        query += ") VALUES ("
        for value in data_dict.values():
            if isinstance(value, str):
                if "'" in value:
                    value = value.replace("'", "''")
                query += f"'{value}', "
            elif value is None:
                query += "NULL, "
            else:
                query += f"{value}, "
        else:
            query = query[:-2]
        query += ")"
        self.query(query=query)

    def get_table_data_from_key(self, table_name: str, column_name: str, column_value: str):
        query = f"SELECT * FROM {table_name} WHERE {column_name} = '{column_value}'"
        self.query(query=query)
        rows = self.cursor.fetchall()
        return [dict_factory(self.cursor, row) for row in rows]

    def get_table_data_from_compound_keys(self, table_name: str, key_value_dict: Dict[str, value_type]):
        key_value_dict = {key: value for key, value in key_value_dict.items() if value != ""}
        query = f"SELECT * FROM {table_name} WHERE "
        for key, value in key_value_dict.items():
            if isinstance(value, str):
                if "'" in value:
                    value = value.replace("'", "''")
                query += f"{key} = '{value}' AND "
            query += f"{key} = '{value}' AND "
        else:
            query = query[:-5]
        self.query(query=query)
        rows = self.cursor.fetchall()
        return [dict_factory(self.cursor, row) for row in rows]

    def drop_table_if_exists(self, table_name: str):
        query = f"DROP TABLE IF EXISTS {table_name}"
        self.query(query=query)


def get_db(test_mode: bool = True):
    if test_mode:
        sqlite = SQLite(db_path=None)
    else:
        sqlite = SQLite(db_path=hypatia_db_path)
    return sqlite


def initialize_tables(test_mode: bool = True):
    sqlite = get_db(test_mode=test_mode)
    sqlite.create_all_tables()


def fetch_all_tables(test_mode: bool = True):
    sqlite = get_db(test_mode=test_mode)
    return sqlite.fetchall_tables()


drop_web_tebles = [
    "t_star",
    "t_star_archive",
    "t_element",
    "t_element_archive",
    "t_planet",
    "t_planet_archive",
    "t_catalogue",
    "t_catalogue_archive",
]


def drop_all_web_tables(test_mode: bool = True):
    sqlite = get_db(test_mode=test_mode)
    for table_name in drop_web_tebles:
        sqlite.drop_table_if_exists(table_name=table_name)


def initialize_web_tables(test_mode: bool = True):
    sqlite = get_db(test_mode=test_mode)
    for table_name in drop_web_tebles:
        sqlite.create_table_from_name(table=table_name)


def delete_test_database(test_mode: bool = True, remove_compositions: bool = True):
    if test_mode:
        test_database_path = os.path.join(test_database_dir, "storage.sqlite")
        if os.path.exists(test_database_path):
            os.remove(test_database_path)
        initialize_tables(test_mode=test_mode)
        compositions_dir = test_database_dir
    else:
        drop_all_web_tables(test_mode=test_mode)
        initialize_web_tables(test_mode=test_mode)
        compositions_dir = hdf5_data_dir
    hashable_filepath = os.path.join(compositions_dir, "hashtable.shelf")
    if os.path.exists(hashable_filepath):
        os.remove(hashable_filepath)
    if remove_compositions:
        for file in os.listdir(compositions_dir):
            if file.startswith("compositions"):
                os.remove(os.path.join(compositions_dir, file))


if __name__ == '__main__':
    test_mode = True
    delete_test_database()
    initialize_tables(test_mode=test_mode)
    tables = fetch_all_tables(test_mode=test_mode)
