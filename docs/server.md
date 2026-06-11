# Server & app lifecycle — `DisunityServer`

Defined in [src/disunity/server.py](src/disunity/server.py). `DisunityServer` subclasses
`quart.Quart`, so every Quart method/decorator (`before_serving`, `run`, `route`, the ASGI app
itself, etc.) is available on the instance.

---

## `DisunityServer(public_key, client_secret, client_id, bot_token=None)`

**Source:** [src/disunity/server.py:37](src/disunity/server.py:37)

Constructs the interactions web server and registers the `POST /interactions` route.

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `public_key` | `str` | — (required) | Application public key (hex) from the Discord developer portal. Used to build a `nacl.signing.VerifyKey` for request-signature verification. |
| `client_secret` | `str` | — (required) | Client secret; used to mint OAuth2 `client_credentials` bearer tokens for outgoing API calls when no `bot_token` is set. |
| `client_id` | `int` | — (required) | Application ID; used in webhook URLs and as the OAuth2 client id. |
| `bot_token` | `str \| None` | `None` | Bot token. If provided, outgoing requests authenticate as `Bot <token>` instead of bearer credentials. Required only for non-interaction API usage (e.g. `Message.edit_as_bot`). |

**Returns:** a `DisunityServer` (a `Quart` app).

Internally sets `self.config["CLIENT_PUBLIC_KEY" | "CLIENT_SECRET" | "CLIENT_ID" | "BOT_TOKEN"]`,
creates a private `ApplicationCache`, an empty packages dict, and adds the `/interactions` URL rule.

> ⚠️ The README shows `disunity.DisunityServer()` with no arguments — that is **wrong** for this
> version; all three positional args are mandatory.

```python
server = disunity.DisunityServer(
    public_key="abc123...",
    client_secret="shhh",
    client_id=123456789012345678,
)
```

---

## Package loading

### `load_package(package_path)`

**Source:** [src/disunity/server.py:177](src/disunity/server.py:177)

`importlib.import_module(package_path)`, then fetches the module-level `setup` attribute and calls
`setup(self)`. The module **must** define a top-level `setup(app)` function or this raises
`AttributeError`.

- `package_path` (`str`): a dotted import path, e.g. `"packages.general"`.
- Returns `None`.

```python
server.load_package("packages.general")  # imports packages/general.py, calls its setup(server)
```

### `register_package(package_class)`

**Source:** [src/disunity/server.py:183](src/disunity/server.py:183)

Registers an **instantiated** package. Stores it keyed by the instance's class name
(`package_class.__class__.__name__`), calls `package_class.unpack()` to extract decorated handlers,
and adds each into the cache.

- `package_class`: an **instance** of a `Package` subclass (not the class itself).
- Returns `None`.

```python
def setup(app):
    app.register_package(General(app))   # pass an instance
```

> The dict key is the class name, so two packages with the same class name overwrite each other in
> `get_package`. Handler routing is unaffected (it goes through the cache by command/component name).

### `setup(app)` convention

`load_package` requires each package module to expose `def setup(app): ...`. The conventional body
is `app.register_package(YourPackage(app))`. This is the only supported package entry point.

### `get_package(package_name)` / `get_package_names()`

**Source:** [src/disunity/server.py:61](src/disunity/server.py:61), [src/disunity/server.py:64](src/disunity/server.py:64)

- `get_package(package_name: str)` → the stored package instance or `None`. `package_name` is the
  **class name** string.
- `get_package_names()` → `list[str]` of registered class names.

---

## `cache` property

**Source:** [src/disunity/server.py:57](src/disunity/server.py:57)

Read-only access to the internal `ApplicationCache`
([src/disunity/cache.py:10](src/disunity/cache.py:10)), which holds three dicts: `commands`,
`components`, `autocompletes`. You rarely touch this directly. Routing details:

- `commands` is keyed by the **string** of the command type (`"2"`), then by command name. Both
  plain commands (`Command.command_type == 2`) and subcommand bases are stored under `"2"`.
- `components` is keyed by component **name** (the part of `custom_id` before the first `-`).
- `autocompletes` is keyed by command name.

---

## Outgoing HTTP — `make_https_request(...)`

**Source:** [src/disunity/server.py:103](src/disunity/server.py:103)

```python
async def make_https_request(self, method, url, headers=None, payload=None,
                             files=None, override_checks=False)
```

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `method` | `str` | — | `GET` / `PUT` / `PATCH` / `DELETE` / `POST`. |
| `url` | `str` | — | If it does **not** start with `https://`, it is prefixed with `https://discord.com/api/v10/`. So pass Discord paths relative, e.g. `"webhooks/{id}/{token}"`. |
| `headers` | `dict \| None` | `None` | If `None` and a `bot_token` is configured → `Authorization: Bot <token>`. If `None` and no bot token → bearer client credentials via `auth()`. |
| `payload` | `dict \| None` | `None` | JSON body (POST/PUT/PATCH). When `files` is given, sent as a `payload_json` multipart field. |
| `files` | `list[dict] \| None` | `None` | List of `{"id", "filename", "content"}`; sent as multipart `files[<id>]`. Content type guessed from filename, defaulting to `application/octet-stream`. |
| `override_checks` | `bool` | `False` | If `True`, returns the raw `aiohttp` response object **without** status checking or JSON parsing (caller inspects `.status` / `await .json()`). |

**Behavior / returns:**
- On non-`2xx` (and `override_checks=False`), raises `errors.HTTPRequestError(status, json_body)`
  ([src/disunity/errors.py:23](src/disunity/errors.py:23)).
- On `204 No Content`, returns `None`.
- Otherwise returns parsed JSON (`dict`). JSON-parse failures are routed to `error_handler`.

Used internally by `Context.followup` and the `Message.edit_*` / `delete_*` methods.

---

## Global hooks (override in a subclass)

Override these by subclassing `DisunityServer`. They are called by the `/interactions` router.

### `global_check(context) -> bool`
**Source:** [src/disunity/server.py:189](src/disunity/server.py:189)
Runs **before** every command, component, and modal-submit handler. Return value controls routing:
- Returns `True` → proceed to the handler. **(Default returns `True`.)**
- Returns a `dict` containing a `"type"` key → that dict is `jsonify`'d and returned to Discord as
  the interaction response; the handler is **skipped**.
- Returns anything else falsy/non-`True` → server responds with a bare `PONG` (`{"type": 1}`) and
  skips the handler.

> Note the check is `if check != True`, so only the literal `True` proceeds; truthy non-`True`
> values are treated as "blocked".

### `global_before_interaction(context)`
**Source:** [src/disunity/server.py:201](src/disunity/server.py:201)
`async`, called after a passing `global_check`, before the handler. Default no-op.

### `global_after_interaction(context)`
**Source:** [src/disunity/server.py:210](src/disunity/server.py:210)
`async`, called after the handler. Default no-op. **Scheduling differs by path:**
- **Non-ack handlers:** scheduled via `asyncio.create_task(...)` *after* the handler returns (fire-and-forget; runs concurrently with the response being returned).
- **Ack handlers (commands & components):** awaited *inside* the same background task, immediately after the handler coroutine (`await coroutine(ctx); await global_after_interaction(ctx)`).
- **Autocomplete:** `global_after_interaction` is **not** called at all on the autocomplete path.

### `error_handler(exc)`
**Source:** [src/disunity/server.py:67](src/disunity/server.py:67)
Default implementation simply `raise exc`. All handler wrappers (`Command`, `Component`,
`SubCommand`, `Autocomplete` in [identifiers.py](src/disunity/identifiers.py)) catch exceptions
from your coroutine and forward them here. Override to log instead of raising.

---

## The `/interactions` router — `interactions()`

**Source:** [src/disunity/server.py:219](src/disunity/server.py:219)

The single POST handler. Sequence:

1. `verify(request)` — checks `X-Signature-Ed25519` / `X-Signature-Timestamp` against the public
   key; aborts `401` on `BadSignatureError`. ([src/disunity/server.py:70](src/disunity/server.py:70))
2. Branch on `received["type"]` (`utils.InteractionTypes`):
   - **`PING` (1):** returns `{"type": 1}` (PONG).
   - **`APPLICATION_COMMAND` (2):** looks up the command by name; `match`es on `data.options` to
     detect subcommand-group / subcommand / options / bare; builds `Context`; runs `global_check`
     and `global_before_interaction`; then ack-or-respond (below). See [subcommands.md](subcommands.md).
   - **`MESSAGE_COMPONENT` (3):** looks up component by `custom_id.split("-")[0]`; ack-or-respond.
   - **`APPLICATION_COMMAND_AUTOCOMPLETE` (4):** looks up autocomplete by command name; returns
     `{"type": 8, "data": {"choices": [...]}}`.
   - **`MODAL_SUBMIT` (5):** looks up component by `custom_id.split("-")[0]`; runs the handler and
     returns its dict. (Modal submit is **never** ack-deferred by this router.)

### Ack / defer mechanics

For commands and components, after the hooks:

```text
if handler.ack:                         # decorator requires_ack=True
    send a deferred response NOW, run handler as a background task, return the defer
else:
    response = await handler(ctx)       # handler returns the real response dict
    return jsonify(response)
```

- **Command defer type:** `5` `DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE`
  ([src/disunity/server.py:280](src/disunity/server.py:280)).
- **Component defer type:** `6` `DEFERRED_UPDATE_MESSAGE`
  ([src/disunity/server.py:317](src/disunity/server.py:317)).
- After deferring, the handler must respond with `ctx.followup(...)` (a webhook send). Its return
  value is ignored.

> ⚠️ **Known bug — `requires_ephemeral=True` on a command crashes.** In the command ack branch the
> code does `response["data"]["flags"] = 64` but `response` was built as `{"type": 5}` with **no**
> `"data"` key, so this raises `KeyError: 'data'`
> ([src/disunity/server.py:282-283](src/disunity/server.py:282)). Ephemeral deferral works for
> **components** (the component branch builds the `data` dict correctly,
> [src/disunity/server.py:319](src/disunity/server.py:319)) but **not** for commands. To get an
> ephemeral acked command response, leave `requires_ephemeral=False` and pass `ephemeral=True` to
> `ctx.followup(...)` instead. See [gotchas.md](gotchas.md).

---

## Running

`DisunityServer` is an ASGI app (Quart). `server.run()` starts Quart's dev server. For production,
serve the app object with an ASGI server (hypercorn/uvicorn) or Gunicorn with an ASGI worker.
Use `@server.before_serving` to load packages once at startup (see [index.md](index.md) quick start).
