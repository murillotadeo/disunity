import asyncio
from quart.flask_patch.globals import request
from quart.json import jsonify
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

import aiohttp
import requests
import time
import quart
import importlib

from typing import Optional

from . import identifiers, cache, errors
from .models.context import DisunityCommandContext, DisunityComponentContext

class DisunityServer(quart.Quart):
    """
        Disunity interactions web server
        
        Parameters
        ----------
        public_key: str
            The application's public key that can be found in the Discord developer portal
        
        client_secret: str
            The client secret which can be found in the Discord developer portal. It is used
            to generate the Bearer client credentials for HTTPS headers.
        
        client_id: int
            The id of the application. Used to generate Bearer client credentials for HTTPS headers.

        bot_token: Optional[str]
            The bot token tied to this application if applicable. Only pass in token if you expect
            to use any other part of the Discord API that is not interactions based. 
    """

    def __init__(self, public_key: str, client_secret: str, client_id: int, bot_token: Optional[str] = None):
        super().__init__(__name__)
        self.config['CLIENT_PUBLIC_KEY'] = public_key
        self.config['CLIENT_SECRET'] = client_secret
        self.config['CLIENT_ID'] = client_id
        self.config['BOT_TOKEN'] = bot_token
        self.config['CREDENTIALS_EXPIRE_IN'] = 0 # Set to 0 to initiate credentials later on
        self._cache: cache.ApplicationCache = cache.ApplicationCache()
        self.add_url_rule('/interactions', 'interactions', self.interactions, methods=['POST'])

    def verify_request(self, request):
        """Verifies the incoming request using PyNaCl"""

        _key = VerifyKey(bytes.fromhex(self.config['CLIENT_PUBLIC_KEY']))

        try:
            signature, timestamp = request.headers['X-Signature-Ed25519'], request.headers['X-Signature-Timestamp']
        except KeyError:
            quart.abort(401, "Invalid request headers")

        body = request.data.decode('utf-8')

        try:
            _key.verify((timestamp + body).encode(), bytes.fromhex(signature))
        except BadSignatureError:
            quart.abort(401, "Invalid request signature")



    async def interactions(self):
        """The interactions handler. All interactions are sent here"""

        self.verify_request(request)
        rjson = request.json

        if rjson['type'] == 1:
            return jsonify({"type": 1})

        elif rjson['type'] == 2:

            context = DisunityCommandContext(self, rjson)
            command: identifiers.DisunityCommand = self._cache.commands[str(context.type)].get(context.command_name, None)
            if command is None:
                return jsonify({"type": 4, "data": {"content": "This command was not found within the bot", "flags": 64}})
            
            if command.requires_ack:
                resp = {"type": 5}
                if command.requires_ephemeral:
                    resp['data'] = {"flags": 64}
                
                asyncio.create_task(command(context=context))
                return jsonify(resp)

            maybe_json = await command(context)
            return jsonify(maybe_json)

        elif rjson['type'] == 3:

            context = DisunityComponentContext(self, rjson)
            component: identifiers.DisunityComponent = self._cache.components.get(str(context.custom_id).split('-')[0], None)

            if component is None:
                return jsonify({"type": 4, "data": {"content": "This component does not exist", "flags": 64}})

            if component.requires_ack:
                resp = {"type": 6}
                if component.requires_ephemeral:
                    resp['data'] = {"flags": 64}
                
                context.acked = True
                asyncio.create_task(component(context=context))
                return jsonify(resp)

            maybe_json = await component(context)
            return jsonify(maybe_json)


    def __generate_client_credentials(self):
        """Called when Bearer client credentials need to be generated"""

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
        """Returns the application's headers"""

        if self.config['CREDENTIALS_EXPIRE_IN'] < time.time():
            self.__generate_client_credentials()
        return {"Authorization": "Bot " + self.config['CLIENT_CREDENTIALS_TOKEN']}


    async def make_http_request(self, method: str, url: str, headers: Optional[dict] = None, payload: Optional[dict] = None):
        """
            Performs a HTTP request using the given parameters

            Parameters
            ----------
            method: str
                The method to use. Can be either: GET, PUT, PATCH, DELETE, POST
        
            url: str
                The url to make the request to. If performing a request to discord, do not include
                'https://discord.com/api/v10', it will be automatically added.

            headers: Optional[dict]
                The headers to use for the request. If none are given, the application's Bearer 
                client credentials will be used.

            payload: Optional[dict]
                The payload to send to the url. Only applicable for POST, PUT, and PATCH requests.
        """

        if not url.startswith('https://'): 
            url = "https://discord.com/api/v10/" + url

        if headers is not None:
            _headers = headers
        elif headers is None and self.config['BOT_TOKEN'] is not None:
            _headers = {"Authorization": "Bot " + self.config['BOT_TOKEN']}
        else:
            _headers = self.auth()


        async with aiohttp.request(method, url, headers=_headers, json=payload) as maybe_response:
            if not str(maybe_response.status).startswith('20'):
                raise errors.HTTPRequestError(maybe_response.status, await maybe_response.json())

            try:
                return await maybe_response.json()
            except Exception as e:
                return e

    def load_package(self, package_path):
        package = importlib.import_module(package_path)
        setup_func = getattr(package, 'setup')

        setup_func(self)

    def register_package(self, package_class):
        contents = package_class._open()
        for item in contents:
            if isinstance(item, identifiers.DisunityCommand):
                self._cache.cache_command(item)
            elif isinstance(item, identifiers.DisunityComponent):
                self._cache.cache_component(item)

    async def register_component(self, ctx, custom_id, coroutine, timeout: float = 0.0, is_single_use: bool = True, requires_ack: bool = False, requires_ephemeral: bool = False):
        self._cache.cache_component(identifiers.DisunityComponent(ctx, custom_id, coroutine, timeout, is_single_use, requires_ack, requires_ephemeral))
