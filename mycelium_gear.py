import base64
import hashlib
import hmac
import time
import urllib.parse
from datetime import datetime

import requests

from requests import RequestException


def datetime2timestamp(date_time: datetime) -> int:
    return int(time.mktime(date_time.timetuple()))


class MyCeliumGearException(Exception):
    """Base exception for MyCelium Gear API errors"""


class AddressAlreadyInUse(MyCeliumGearException):
    """Raises for creating order when wallet address is in use"""


class MyCeliumGear:
    """MyCelium gear API python implementation

        Order statuses:
            0 - pending;
            1 — unconfirmed; transaction was received, but does not have enough confirmations yet
            2 — paid in full
            3 — underpaid; not enough money received
            4 — overpaid; too much has been received
            5 — expired; customer did not pay in time
            6 — canceled; customer has canceled the order
    """
    CONNECT_TIMEOUT = 60
    API_URL = 'https://gateway.gear.mycelium.com'

    STATUS_PENDING = 0
    STATUS_UNCONFIRMED = 1
    STATUS_PAID = 2
    STATUS_UNDERPAID = 3
    STATUS_OVERPAID = 4
    STATUS_EXPIRED = 5
    STATUS_CANCELED = 6

    def __init__(self, gateway_id, gateway_secret):
        self.gateway_id = gateway_id
        self.gateway_secret = gateway_secret

    def create_order(self, amount, keychain_id=None, callback_data=None):
        """Creates order in Gear

        :param amount: float Amount determines the amount to be paid for this
                             order. The amount should be in the currency you
                             have previously set for the gateway. If the
                             gateway currency is BTC, then the amount is
                             normally in satoshis
        :param keychain_id: int Keychain id is used to generate an address for
                                the next order.
        :param callback_data:
        :return: A server json response
        :rtype: dict
        """
        request_uri = self._endpoint('orders')
        params = {
            'amount': amount,
        }
        if keychain_id:
            params['keychain_id'] = keychain_id
        if callback_data:
            params['callback_data'] = callback_data

        data = {
            'request_uri': request_uri,
            'request_method': 'POST',
            'params': params
        }

        return self._send_signed_request(data)

    def cancel_order(self, payment_id):
        """Cancel order in Gear

        :param payment_id: int Id is an existing order ID or payment ID
        :return: None 200 response is OK status
        :rtype: None
        """
        request_uri = self._endpoint('orders')

        data = {
            'request_uri': request_uri,
            'request_method': 'POST',
            'params': '{}/cancel'.format(payment_id)
        }

        return self._send_signed_request(data)

    def check_order(self, payment_id):
        """Retrieve current payment or order data

        :param payment_id: int Id is an existing order ID or payment ID
        :return: A server json response
        :rtype: dict
        """
        request_uri = self._endpoint('orders')

        data = {
            'request_uri': request_uri,
            'request_method': 'GET',
            'params': payment_id
        }

        return self._send_signed_request(data)

    def is_order_callback_valid(self, request_method, request_path, request_signature):
        """Return is valid status for request from Gear

        :param request_method: str
        :param request_path: str
        :param request_signature: str
        :return: Is request valid
        :rtype: bool
        """
        secret = self.gateway_secret.encode('utf-8')

        sha512 = hashlib.sha512()
        sha512.update(b'')
        nonce = sha512.digest()

        request_str = (request_method + request_path).encode('utf-8') + nonce
        raw_signature = hmac.new(secret, request_str, hashlib.sha512).digest()
        signature = base64.standard_b64encode(raw_signature)
        if not isinstance(request_signature, bytes):
            signature = signature.decode('utf-8')

        return request_signature == signature

    @staticmethod
    def get_order_payment_link(payment_id):
        """Get an order link to payment gateway

        :param payment_id:
        :return: An order link
        :rtype: bool
        """
        return 'https://gateway.gear.mycelium.com/pay/{}'.format(payment_id)

    def order_websocket_link(self, payment_id):
        """Get an order link for status monitoring via websocket

        :param payment_id:
        :return: An order link for status monitoring via websocket
        :rtype: bool
        """
        return 'wss://gateway.gear.mycelium.com/gateways/{gateway_id}/orders/{id}/websocket'.format(
            gateway_id=self.gateway_id,
            id=payment_id
        )

    def get_last_keychain_id(self):
        """Get Last Keychain Id

        :return: Get a last keychain id for a specific gateway
        :rtype: dict
        """
        request_uri = self._endpoint('last_keychain_id')

        data = {
            'request_uri': request_uri,
            'request_method': 'GET',
            'params': None
        }

        return self._send_signed_request(data)

    def _endpoint(self, method):
        """Construct an endpoint URL

        :param method: API method
        :return: URL
        :rtype: string
        """
        return '/gateways/{gateway_id}/{method}'.format(
            gateway_id=self.gateway_id,
            method=method
        )

    @staticmethod
    def _get_query_params(params):
        """Generate a string with query params

        :param params: dict Query params
        :return: String
        :rtype: str
        """
        if isinstance(params, dict):
            return '?' + urllib.parse.urlencode(params)
        elif params:
            return '/' + params
        else:
            return ''

    def _get_headers(self, request_method, request_url, query_params):
        """Returns headers for signed request

        :param request_method: str GET or POST
        :param request_url: str Url = endpoint
        :param query_params: str Query params
        :return: Headers for Gear API request
        :rtype: dict
        """
        nonce = datetime2timestamp(datetime.now())
        signature = self._create_signature(request_method, request_url, query_params, nonce)
        return {
            'X-Nonce': nonce,
            'X-Signature': signature
        }

    def _create_signature(self, request_method, request_url, query_params, nonce):
        sha512 = hashlib.sha512()

        secret = self.gateway_secret.encode('utf-8')
        body = ''

        str_obj = str(nonce) + body
        str_obj = str_obj.encode('utf-8')
        sha512.update(str_obj)
        nonce_body_hash = sha512.digest()
        payload = (request_method + request_url + query_params).encode('utf-8') + nonce_body_hash
        raw_signature = hmac.new(secret, payload, hashlib.sha512).digest()
        signature = base64.standard_b64encode(raw_signature)
        return signature

    def _send_signed_request(self, data):
        """Sends signed request

        :param data: dict
        :return: Headers for Gear API request
        :rtype: dict
        """
        method = data['request_method']
        params = self._get_query_params(data['params'])
        headers = self._get_headers(method, data['request_uri'], params)
        url = self.API_URL + data['request_uri'] + params

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.CONNECT_TIMEOUT
            )
        except RequestException as e:
            msg = 'An error in request to Mycelium gear: {}'.format(str(e))
            print(msg)
        else:
            if response.status_code == requests.codes.ok:
                return response.json()
            elif response.text == 'Invalid order: address already in use':
                raise AddressAlreadyInUse
            else:
                if response.text:
                    msg = 'Fetch error response from Mycelium gear: {}'.format(str(response.text))
                    print(msg)
