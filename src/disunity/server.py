import asyncio
import importlib
import json
import mimetypes
import time

import aiohttp
import quart
import requests
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from quart.flask_patch.globals import request
from quart.json import jsonify

from . import cache, errors, identifiers, utils
from .models.context import Context


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

    def __init__(
        self,
        public_key: str,
        client_secret: str,
        client_id: int,
        bot_token: None | str = None,
    ):
        super().__init__(__name__)
        self.config["CLIENT_PUBLIC_KEY"] = public_key
        self.config["CLIENT_SECRET"] = client_secret
        self.config["CLIENT_ID"] = client_id
        self.config["BOT_TOKEN"] = bot_token
        self.config["CREDENTIALS_EXPIRE_IN"] = 0  # set on start up
        self.__cache: cache.ApplicationCache = cache.ApplicationCache()
        self.__packages = dict()
        self.__key = VerifyKey(bytes.fromhex(self.config["CLIENT_PUBLIC_KEY"]))
        self.add_url_rule(
            "/interactions", "interactions", self.interactions, methods=["POST"]
        )

    @property
    def cache(self) -> cache.ApplicationCache:
        return self.__cache
    
    def get_package(self, package_name):
        return self.__packages.get(package_name, None)

    def error_handler(self, exc: Exception):
        raise exc

    def verify(self, req):
        signature, timestamp = (
            req.headers["X-Signature-Ed25519"],
            req.headers["X-Signature-Timestamp"],
        )
        body = req.data.decode("utf-8")

        try:
            self.__key.verify((timestamp + body).encode(), bytes.fromhex(signature))
        except BadSignatureError:
            quart.abort(401, "Invalid request signature")

    def __generate_client_credentials(self):
        response = requests.post(
            "https://discord.com/api/" + "oauth2/token",
            data={
                "grant_type": "client_credentials",
                "scope": "applications.commands.update",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(self.config["CLIENT_ID"], self.config["CLIENT_SECRET"]),
        )
        response.raise_for_status()
        data = response.json()

        self.config["CLIENT_CREDENTIALS_TOKEN"] = data["access_token"]
        self.config["CREDENTIALS_EXPIRE_IN"] = time.time() + data["expires_in"] / 2

    def auth(self):
        if self.config["CREDENTIALS_EXPIRE_IN"] < time.time():
            self.__generate_client_credentials()
        return {"Authorization": "Bearer " + self.config["CLIENT_CREDENTIALS_TOKEN"]}

    async def make_https_request(
        self,
        method: str,
        url: str,
        headers: None | dict = None,
        payload: None | dict = None,
        files: None | dict = None,
        override_checks: bool = False,
    ):
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
        files: Optional[list]
            A list of dictionaries with 'id', 'filename' and 'content'.
        """
        if not url.startswith("https://"):
            url = "https://discord.com/api/v10/" + url

        if headers is None and self.config["BOT_TOKEN"] is not None:
            headers = {"Authorization": "Bot " + self.config["BOT_TOKEN"]}
        elif headers is None:
            headers = self.auth()

        if files:
            data = aiohttp.FormData()
            if payload:
                data.add_field(
                    "payload_json",
                    json.dumps(payload),
                    content_type="application/json",
                )
            for file in files:
                content_type, _ = mimetypes.guess_type(file["filename"])
                if content_type is None:
                    content_type = "application/octet-stream"
                data.add_field(
                    f"files[{file['id']}]",
                    file["content"],
                    filename=file["filename"],
                    content_type=content_type,
                )
            request_kwargs = {"data": data}
        else:
            request_kwargs = {"json": payload} if payload else {}

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, headers=headers, **request_kwargs
            ) as maybe_response:
                if override_checks:
                    return maybe_response

                if not str(maybe_response.status).startswith("20"):
                    raise errors.HTTPRequestError(
                        maybe_response.status, await maybe_response.json()
                    )

                if maybe_response.status != 204:  # No Content response
                    try:
                        return await maybe_response.json()
                    except Exception as e:
                        self.error_handler(e)

    def load_package(self, package_path):
        package = importlib.import_module(package_path)
        setup = getattr(package, "setup")

        setup(self)
        self.__packages[type(package).__name__] = package

    def register_package(self, package_class):
        contents = package_class.unpack()
        for item in contents:
            self.__cache.add_item(item)

    async def global_check(self, context: Context) -> bool:
        """Global check for all application commands, message components and modal submits.

        Args:
            context (Context): Application command context.

        Returns:
            bool: Command is executed only if `True` is returned.
                    `True` is returned by default.
        """
        return True
    
    async def global_before_interaction(self, context: Context):
        """Called before the execution of any application command, message components and modal submits.
        This is called after global check is handled.

        Args:
            context (Context): Application command or message component context.
        """
        pass

    async def global_after_interaction(self, context: Context):
        """Called after the execution of any application command, message components, and modal submits.

        Args:
            context (Context): Application command or message component context.
        """
        pass


    async def interactions(self):
        self.verify(request)
        received = request.json

        if received["type"] == utils.InteractionTypes.PING:
            return jsonify({"type": utils.InteractionCallbackTypes.PONG})

        elif received["type"] == utils.InteractionTypes.APPLICATION_COMMAND:
            command = self.__cache.commands[str(received["type"])].get(
                received["data"]["name"], None
            )
            if command is None:
                raise errors.CommandNotFound(received["data"]["name"])

            coroutine: identifiers.Command | identifiers.SubCommand | None = None
            match received["data"]:
                case {
                    "options": [{"name": name, "options": options, "type": 2}]
                }:  # Sub command group
                    if not isinstance(command, identifiers.CacheableSubCommand):
                        raise errors.InvalidMethodUse(
                            "Commands with sub commands must be registered using the Package.sub decorator"
                        )

                    coroutine = command.map[str(name)].get(options[0]["name"], None)
                    received["data"]["injected"] = options[0]["options"]

                case {
                    "options": [{"name": name, "options": options, "type": 1}]
                }:  # Sub command
                    if not isinstance(command, identifiers.CacheableSubCommand):
                        raise errors.InvalidMethodUse(
                            "Sub commands must be registered using the Package.sub decorator"
                        )

                    coroutine = command.map["sub_commands"].get(name, None)
                    received["data"]["injected"] = options

                case {"options": options}:  # command with options
                    coroutine = command
                    received["data"]["injected"] = options

                case _:  # default to regular
                    coroutine = command
                    received["data"]["injected"] = []

            ctx: Context = Context(self, received)
            if coroutine is None:
                raise errors.CommandNotFound(ctx.command_name)
            
            check = await self.global_check(ctx)
            if check != True:
                if isinstance(check, dict) and "type" in check:
                    return jsonify(check)
                else:
                    return jsonify({"type": utils.InteractionCallbackTypes.PONG})
            
            await self.global_before_interaction(ctx)

            if coroutine.ack:
                response = {
                    "type": utils.InteractionCallbackTypes.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
                }
                if coroutine.ephemeral:
                    response = {
                        "type": utils.InteractionCallbackTypes.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"flags": 64},
                    }

                ctx.acked = True
                async def combined_task(ctx):
                    await coroutine(ctx)
                    await self.after_interaction(ctx)

                asyncio.create_task(combined_task(ctx))
                return jsonify(response)

            response = await coroutine(ctx)
            asyncio.create_task(self.after_interaction(ctx))
            return jsonify(response)

        elif received["type"] == utils.InteractionTypes.MESSAGE_COMPONENT:
            context: Context = Context(self, received)
            component: identifiers.Component = self.__cache.components.get(
                str(context.custom_id).split("-")[0], None
            )

            if component is None:
                raise errors.ComponentNotFound(context.custom_id.split("-")[0])

            check = await self.global_check(context)
            if check != True:
                if isinstance(check, dict) and "type" in check:
                    return jsonify(check)
                else:
                    return jsonify({"type": utils.InteractionCallbackTypes.PONG})
            
            await self.global_before_interaction(context)

            if component.ack:
                response = {
                    "type": utils.InteractionCallbackTypes.DEFERRED_UPDATE_MESSAGE
                }
                if component.ephemeral:
                    response = {
                        "type": utils.InteractionCallbackTypes.DEFERRED_UPDATE_MESSAGE,
                        "data": {"flags": 64},
                    }

                context.acked = True
                async def combined_task(ctx):
                    await component(context)
                    await self.after_interaction(ctx)

                asyncio.create_task(combined_task(ctx))
                return jsonify(response)

            maybe_response = await component(context)
            asyncio.create_task(self.after_interaction(ctx))
            return jsonify(maybe_response)

        elif (
            received["type"] == utils.InteractionTypes.APPLICATION_COMMAND_AUTOCOMPLETE
        ):
            context: Context = Context(self, received)

            autocomplete: identifiers.Autocomplete = self.__cache.autocompletes.get(
                str(context.command_name), None
            )

            if autocomplete is None:
                raise errors.AutocompleteNotFound(context.command_name)

            maybe_choices = await autocomplete(context)
            response = {
                "type": utils.InteractionCallbackTypes.APPLICATION_COMMAND_AUTOCOMPLETE_RESULT,
                "data": {"choices": maybe_choices or []},
            }
            return jsonify(response)

        elif received["type"] == utils.InteractionTypes.MODAL_SUBMIT:
            context: Context = Context(self, received)
            component: identifiers.Component = self.__cache.components.get(
                str(context.custom_id).split("-")[0], None
            )

            if component is None:
                raise errors.ComponentNotFound(context.custom_id.split("-")[0])

            check = await self.global_check(context)
            if check != True:
                if isinstance(check, dict) and "type" in check:
                    return jsonify(check)
                else:
                    return jsonify({"type": utils.InteractionCallbackTypes.PONG})
            
            await self.global_before_interaction(context)

            maybe_response = await component(context)
            asyncio.create_task(self.after_interaction(ctx))
            return jsonify(maybe_response)
