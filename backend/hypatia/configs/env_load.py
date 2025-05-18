import os
from getpass import getuser
from urllib.parse import quote

import dotenv

from hypatia.configs.file_paths import env_filename


# User information
current_user = getuser()

# Load the .env file
if os.path.exists(env_filename):
    dotenv.load_dotenv(env_filename)

# MongoDB Configuration
MONGO_HOST = os.environ.get('MONGO_HOST', 'mongoDB')
MONGO_USERNAME = os.environ.get('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', 'super-not-secure')
MONGO_PORT = os.environ.get('MONGO_PORT', '27017')
MONGO_DATABASE = os.environ.get('MONGO_DATABASE', 'test')
MONGO_STARNAMES_COLLECTION = os.environ.get('MONGO_STARNAMES_COLLECTION', 'stars')
INTERACTIVE_STARNAMES = os.environ.get('INTERACTIVE_STARNAMES', 'True').lower() in {'true', '1', 't', 'y', 'yes', 'on'}
CONNECTION_STRING = os.environ.get('CONNECTION_STRING', 'none')
if CONNECTION_STRING.lower() in {None, 'none', 'null', ''}:
    CONNECTION_STRING = None

def url_encode(string_to_encode: str, url_safe: str = "!~*'()") -> str:
    return quote(string_to_encode.encode('utf-8'), safe=url_safe)

def get_connection_string(user: str = MONGO_USERNAME, password: str = MONGO_PASSWORD,
                          host: str = MONGO_HOST, port: str | int = MONGO_PORT) -> str:
    return f'mongodb://{url_encode(user)}:{url_encode(password)}@{host}:{port}'

if CONNECTION_STRING is None:
    connection_string = get_connection_string()
else:
    connection_string = CONNECTION_STRING