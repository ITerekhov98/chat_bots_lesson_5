from urllib import response
import requests
from environs import Env
import time 


class CmsAuthentication:
    def __init__(self, client_id, client_secret) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_expiration = 0
        self._token = ''
    
    def get_access_token(self):
        if self.token_expiration - time.time() >= 60:
            return self._token
        url = 'https://api.moltin.com/oauth/access_token'
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        response_deserealized = response.json()
        self.token_expiration = response_deserealized['expires']
        self._token = response_deserealized['access_token']
        return self._token


def get_all_products(token):
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_cart(token, tg_user_id):
    url = 'https://api.moltin.com/v2/carts'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    json_data = {
        'data': {
            'name': f'cart for user {tg_user_id}',
            'id': tg_user_id
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


def get_cart(token, user_id):
    url = f'https://api.moltin.com/v2/carts/{user_id}'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_items(token, user_id):
    url = f'https://api.moltin.com/v2/carts/{user_id}/items'
    headers = {
        'Authorization': f'Bearer {token}'
    }    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()    



def add_product_to_cart(token, user_id, product_id, quantity):
    url = f'https://api.moltin.com/v2/carts/{user_id}/items'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    json_data = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


def get_product_by_id(token, product_id):
    url = f'https://api.moltin.com/v2/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()  

def get_photo_by_id(token, photo_id):
    url = f'https://api.moltin.com/v2/files/{photo_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']          


def remove_product_from_cart(token, user_id, product_id):
    url = f'https://api.moltin.com/v2/carts/{user_id}/items/{product_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return 


def create_customer(token, user_id, user_email):
    url = 'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    json_data = {
        'data': {
            'type': 'customer',
            'name': user_id,
            'email': user_email
        }
    }
    response = requests.post(url ,headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


def main():
    env = Env()
    env.read_env()
    client_id = env.str('ELASTIC_PATH_CLIENT_ID')
    client_secret = env.str('ELASTIC_PATH_CLIENT_SECRET')
    cms_token = get_access_token(client_id, client_secret)


