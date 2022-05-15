from quart.flask_patch.globals import request
from quart.json import jsonify
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

import time
import requests
import quart
import aiohttp
import importlib

from typing import Optional
from .. import identifiers, warehouse
from ..web.models import WebCommandContext, WebComponentContext


class DisunityServer(quart.Quart):
    def __init__(self, public_key: str, secret: str, client_id: int, bot_token: Optional[str] = None):
        super().__init__(__name__)
        self.config['CLIENT_SECRET'] = secret
        self.config['CLIENT_PUBLIC_KEY'] = public_key
        self.config['CLIENT_ID'] = client_id
        self.config['CREDENTIALS_EXPIRE_IN'] = 0
        self.config['BOT_TOKEN'] = bot_token
        self.add_url_rule("/interactions", "interactions", self.interactions, methods=['POST'])
        self._warehouse = warehouse.Warehouse()


    def verify_request(self, request):
        """Verifies the incoming request using PyNaCl"""

        verifkey = VerifyKey(bytes.fromhex(self.config['PUBLIC_KEY']))

        try:
            signature, timestamp = request.headers['X-Signature-Ed25519'], request.headers['X-Signature-Timestamp']
        except KeyError:
            quart.abort(401, "Malformed client headers.")

        body = request.data.decode('utf-8')

        try:
            verifkey.verify((timestamp + body).encode(), bytes.fromhex(signature))
        except BadSignatureError:
            quart.abort(401, "Invalid request signature")    


    async def interactions(self):
        """Server endpoint to handle interactions sent by Discord"""
        
        self.verify_request(request)
        
        if request.json['type'] == 1:
            return jsonify({"type": 1})

        elif request.json['type'] == 2:
            _context = WebCommandContext(self, request.json)
            _c = self._warehouse.commands[str(_context.type)].get(request.json['data']['name'], None)
            if _c is None:
                return jsonify({"type": 4, "data": {"flags": 64, "content": "This command could not be found."}})
            await _c(_context)
            
            if _c.requires_ack:
                resp = {"type": 5}
                if _c.requires_ephemeral:
                    resp['data'] = {"flags": 64}

                return jsonify(resp)

        elif request.json['type'] == 3:
            _context = WebComponentContext(self, request.json)
            _c = self._warehouse.components.get(_context.custom_id, None)
            if _c is None:
                return jsonify({"type": 4, "data": {"content": "This component could not be found.", "flags": 64}})
            await _c(_context)

            if _c.requires_ack:

                resp = {"type": 5}
                if _c.requires_ephemeral:
                    resp['data'] = {"flags": 64}

                return jsonify(resp)
    

    async def make_http_request(self, method: str, url: str, headers: dict = {}, payload: dict = {}):
        """

            Performs a HTTP request

            Parameters
            ----------
            method : str
                HTTP method
            url : str
                URL to send request to
            headers : dict
                Request headers, if none are given they will be generated using a Bearer token
            payload : dict
                JSON data being sent to the URL

        """
        
        _headers = self.auth() if headers == {} else headers

        if not url.startswith('https://'): # Assume it is a Discord request
            url = "https://discord.com/api/v10/" + url

        async with aiohttp.request(method, url, headers=_headers, json=payload) as maybe_response:
            if not str(maybe_response.status).startswith('20'):
                pass

            try:
                return await maybe_response.json()
            except Exception as e:
                raise e


    def generate_client_credentials(self):
        """Generates a client credentials Bearer token"""

        response = requests.post(
            "https://discord.com/api/" + "oauth2/token",
            data={
                "grant_type": "client_credentials",
                "scope": "applications.commands.update"
                },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(self.config['CLIENT_ID'], self.config['CLIENT_SECRET'])
            )
        response.raise_for_status()
        data = response.json()
        self.config['CLIENT_CREDENTIALS_TOKEN'] = data['access_token']
        self.config['CREDENTIALS_EXPIRE_IN'] = (time.time() + data['expires_in'] / 2)


    def auth(self):
        """Returns the client credentials Bearer token to use as headers"""
        if self.config['CREDENTIALS_EXPIRE_IN'] < time.time():
            self.generate_client_credentials()
        return {"Authorization": "Bot " + self.config['CLIENT_CREDENTIALS_TOKEN']}


    def register_package(self, package):
        contents = package._open()
        for item in contents:
            if isinstance(item, identifiers.Command):
                self._warehouse.deliver_command(item)
            elif isinstance(item, identifiers.Component):
                self._warehouse.deliver_component(item)


    def load_packae(self, package_path):
        package = importlib.import_module(package_path)
        try:
            setup_func = getattr(package, 'setup')
            setup_func(self)
        except Exception:
            pass 


    def register_component(self, parent_ctx, custom_id, coroutine, timeout: float = 0.0, is_single_use: bool = True, requires_ephemeral: bool = False, requires_ack: bool = True):
        self._warehouse.deliver_component(identifiers.Component(parent_ctx, custom_id, coroutine, timeout, is_single_use, requires_ack, requires_ephemeral))
