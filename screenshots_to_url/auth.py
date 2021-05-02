from json import JSONDecodeError

from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError

from screenshots_to_url.constants import CLIENT_ID, CLIENT_SECRET, IMGUR, ACCESS_TOKEN, REFRESH_TOKEN
import json

from screenshots_to_url.system_utils import is_file


def get_access_keys_dict():
    if is_file(IMGUR):
        with open(IMGUR) as json_file:
            try:
                return json.load(json_file)
            except JSONDecodeError as e:
                print(e)
                return {}
    else:
        return {}


def write_access_keys(access_keys):
    with open(IMGUR, 'w') as outfile:
        json.dump(access_keys, outfile, indent=2)


def access_keys_are_configured(access_keys):
    return CLIENT_ID in access_keys and access_keys[CLIENT_ID] is not None \
           and CLIENT_SECRET in access_keys and access_keys[CLIENT_SECRET] is not None


def tokens_are_configured(access_keys):
    return ACCESS_TOKEN in access_keys and access_keys[ACCESS_TOKEN] is not None \
           and REFRESH_TOKEN in access_keys and access_keys[REFRESH_TOKEN] is not None


def extract_client_keys(access_keys_dict, read_new_keys):
    if not read_new_keys and access_keys_are_configured(access_keys_dict):
        client_id = access_keys_dict[CLIENT_ID]
        client_secret = access_keys_dict[CLIENT_SECRET]
    else:
        print('Please provide Access Keys below:')
        client_id = input('Enter client_id:')
        client_secret = input('Enter client_secret:')

    return client_id, client_secret


def extract_tokens(access_keys_dict, client, read_new_token):
    if not read_new_token and tokens_are_configured(access_keys_dict):
        access_token = access_keys_dict[ACCESS_TOKEN]
        refresh_token = access_keys_dict[REFRESH_TOKEN]
    else:
        authorization_url = client.get_auth_url('pin')
        print("Go to the following URL: {0}".format(authorization_url))
        pin = input('Enter pin code:')

        credentials = client.authorize(pin, 'pin')
        access_token = credentials['access_token']
        refresh_token = credentials['refresh_token']

    return access_token, refresh_token


def get_imgur_client(read_new_client=False, read_new_token=False) -> ImgurClient:
    access_keys_dict = get_access_keys_dict()
    client_id, client_secret = extract_client_keys(access_keys_dict, read_new_client)

    try:
        client = ImgurClient(client_id=client_id, client_secret=client_secret)
    except ImgurClientError as e:
        print(e)
        print('Invalid credentials supplied. Let\'s try again :)')
        return get_imgur_client(read_new_client=True, read_new_token=read_new_token)

    access_token, refresh_token = extract_tokens(access_keys_dict, client, read_new_token)

    print("Authentication successful! Here are the details:")
    print("   Access token:  {0}".format(access_token))
    print("   Refresh token: {0}".format(refresh_token))
    client.set_user_auth(access_token, refresh_token)

    write_access_keys({
        CLIENT_ID: client_id,
        CLIENT_SECRET: client_secret,
        ACCESS_TOKEN: access_token,
        REFRESH_TOKEN: refresh_token
    })

    return client
