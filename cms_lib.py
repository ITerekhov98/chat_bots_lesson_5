import time

import requests


class CmsAuthentication:
    def __init__(self, client_id: str, client_secret: str) -> None:
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
        token_details = response.json()
        self.token_expiration = token_details['expires']
        self._token = token_details['access_token']
        return self._token


def get_all_products(token: str):
    url = 'https://api.moltin.com/v2/products'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_cart(token: str, tg_user_id: str):
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


def get_cart(token: str, user_id: str):
    url = f'https://api.moltin.com/v2/carts/{user_id}'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_items(token: str, user_id: str):
    url = f'https://api.moltin.com/v2/carts/{user_id}/items'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def add_product_to_cart(token: str, user_id: str, product_id: str, quantity: int):
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


def get_product_by_id(token: str, product_id: str):
    url = f'https://api.moltin.com/v2/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_photo_by_id(token: str, photo_id: str):
    url = f'https://api.moltin.com/v2/files/{photo_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']


def remove_product_from_cart(token: str, user_id: str, product_id: str):
    url = f'https://api.moltin.com/v2/carts/{user_id}/items/{product_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return


def get_or_create_customer(token: str, user_id: str, user_email: str):
    url = 'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    params = {
        'filter': f'eq(email,{user_email})'
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    customer_info = response.json()
    if customer_info['data']:
        return customer_info, False

    json_data = {
        'data': {
            'type': 'customer',
            'name': user_id,
            'email': user_email
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json(), True