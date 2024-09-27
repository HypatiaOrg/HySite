import string
import secrets
from getpass import getuser
from datetime import datetime

import pymongo

from hypatia.config import MONGO_HOST, MONGO_PORT, connection_string, get_connection_string

digits = set(string.digits)
letters = set(string.ascii_letters)
punctuation = set(string.punctuation)
alphabet = list(letters | digits | punctuation)


def create_user(user_name: str, password: str, roles: list[dict[str, str]]):
    client = pymongo.MongoClient(connection_string)
    db = client['admin']
    result = db.command('createUser', user_name, pwd=password, roles=roles)
    if result['ok'] == 0:
        raise ValueError(f'Failed to create user: {result}')


def make_read_only_user(user_name: str, password: str = None):
    if password is None:
        password = ''.join(secrets.choice(alphabet) for _ in range(100))
    user_name = str(user_name)
    if not user_name:
        raise ValueError('User name must be a string')
    password = str(password)
    if not password:
        raise ValueError('Password must be a string')
    create_user(
        user_name=user_name, 
        password=password, 
        roles=[{
                'role': 'readAnyDatabase',
                'db':'admin'
        }]
    )
    env_file_name = f'{user_name}.env'
    user_connection_str = get_connection_string(user=user_name, password=password, host=MONGO_HOST, port=MONGO_PORT)
    with open(env_file_name, 'w') as env_file:
        env_file.write(f'# Created on: {datetime.now()}')
        env_file.write(f'#         by: {getuser()}\n')
        env_file.write(f'MONGO_USERNAME={user_name}\n')
        env_file.write(f'MONGO_PASSWORD={password}\n')
        env_file.write(f'MONGO_HOST={MONGO_HOST}\n')
        env_file.write(f'MONGO_PORT={MONGO_PORT}\n')
        env_file.write(f'CONNECTION_STRING={user_connection_str}\n')
    print(f'Read only user created: {user_name}')


def delete_user(user_name: str):
    client = pymongo.MongoClient(connection_string)
    db = client['admin']
    result = db.command('dropUser', user_name)
    if result['ok'] == 0:
        raise ValueError(f'Failed to delete user: {result}')
    print(f'User deleted: {user_name}')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Admin tools for the Hypatia MongoDB database')
    parser.add_argument('user_name', type=str, help='The name of the user modify')
    parser.add_argument('-d', '--delete', action='store_true', dest='do_delete',
                        help='Delete the user', default=False)
    parser.add_argument('-p', '--password', dest='input_password',action='store_true',
                        help='Triggers a prompt to enter a custom password.', default=False)
    args = parser.parse_args()
    if args.input_password:
        input_password = input('Enter a password for the user: ')
    else:
        input_password = None
    if args.do_delete:
        delete_user(user_name=args.user_name)
    else:
        make_read_only_user(user_name=args.user_name, password=input_password)
