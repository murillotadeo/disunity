# disunity — Agent Reference

> **Audience:** an AI coding agent grounding edits in a project that uses `disunity`.
> Every entry is sourced from the repo at the pinned commit. Anything not verifiable
> from source is marked **UNVERIFIED**.

## Version / pin

- **Git commit:** `61d0767e4c9a21db4141143b56d0c4d30bcb9ba9` (2024-09-08)
- **Branch:** `main`
- **`pyproject.toml` version:** `0.1.17` ([pyproject.toml:13](pyproject.toml:13))
- **`disunity.utils.__version__`:** `"0.1.3"` ([src/disunity/utils.py:3](src/disunity/utils.py:3))
  - ⚠️ The two version strings disagree. `__version__` is stale; the package build version is `0.1.17`.
- **Python:** requires `>=3.10.0` (uses PEP 604 `X | Y` unions and `match`/`case`).
- **Runtime deps:** `aiohttp>=3.6.0,<3.8.0`, `PyNaCl>=1.5.0`, `requests>=2.26.0`, `quart>=0.17.0`.

## What disunity is

`disunity` is a Discord **interactions** framework built on a [Quart](https://quart.palletsprojects.com/)
(async Flask) web server. It does **not** use a gateway/websocket. Discord POSTs interaction
payloads to a single `/interactions` HTTP endpoint; the server verifies the Ed25519 signature,
routes the payload to a handler you registered, and returns a JSON response. Handlers are grouped
into **Packages** (classes) and declared with decorators (`@Package.command`, `@Package.component`,
`@Package.sub`, `@Package.autocomplete`). A `Context` object wraps each interaction and is how you
respond (`ctx.callback`, `ctx.followup`, `ctx.modal_response`).

## Doc map

| File | Covers |
|------|--------|
| [server.md](server.md) | `DisunityServer` — construction, `register_package`, `load_package` / `setup(app)` convention, `make_https_request`, the `global_*` hooks, the `/interactions` router, ack/defer behavior. |
| [packages.md](packages.md) | `Package` base class, `unpack()`, and the four decorators with **every** parameter (incl. positional booleans, `timeout`). |
| [commands.md](commands.md) | Declaring slash commands, reading options via `ctx.options`, autocomplete. |
| [subcommands.md](subcommands.md) | `SubOption`, `@Package.sub`, groups, and how subcommands route. |
| [components.md](components.md) | Buttons, select menus, action rows, modals, text inputs, styles. `custom_id` matching + timeout. |
| [context.md](context.md) | `Context` / `Interaction` — `callback`, `followup`, `modal_response`, all attributes, `check_user`. |
| [models.md](models.md) | `User`, `Member`, `Message`, `Attachment`, `Embed`. |
| [errors.md](errors.md) | Exception types and when they raise. |
| [utils.md](utils.md) | `InteractionTypes`, `InteractionCallbackTypes`, avatar helpers. |
| [gotchas.md](gotchas.md) | **Read this.** Non-obvious invariants: when ack is mandatory, the `requires_ephemeral` command crash, `response_type` meanings, `custom_id` naming rules, timeout semantics, token lifetimes, async footguns. |

## Public import surface

Top-level (`disunity/__init__.py`): `utils`, `Embed`, `SubOption`, `Message`, `Attachment`,
`Package`, `DisunityServer`. ([src/disunity/__init__.py:1](src/disunity/__init__.py:1))

`disunity.models` re-exports: `ActionRow`, `Button`, `ButtonStyles`, `MenuOption`, `Modal`,
`SelectMenu`, `SelectMenuOption`, `TextInputStyles`, `UserTextInput`, `Context`, `Member`,
`Message`, `User`, `Attachment`. ([src/disunity/models/__init__.py:1](src/disunity/models/__init__.py:1))

Note: `Context` is **not** exported from the top-level `disunity` package; import it from
`disunity.models` or `disunity.models.context`. It is rarely constructed by user code (the server
builds it) — you typically only need it as a type hint.

## Quick start

A minimal bot is two pieces: the server, and one or more packages loaded into it.

### `main.py`

```python
import pathlib
import disunity

# All three args are REQUIRED (the README's no-arg DisunityServer() example is outdated).
server = disunity.DisunityServer(
    public_key="<APPLICATION_PUBLIC_KEY>",   # hex string from the Discord dev portal
    client_secret="<CLIENT_SECRET>",
    client_id=123456789012345678,            # int
    bot_token=None,                          # optional; only needed for non-interaction API calls
)

@server.before_serving
async def load_packages():
    for module in [f"{f.parent}.{f.stem}"
                   for f in pathlib.Path("packages").glob("*.py")]:
        server.load_package(module)          # imports the module and calls its setup(server)

if __name__ == "__main__":
    server.run()  # Quart's run(); for production use an ASGI server (gunicorn/uvicorn/hypercorn)
```

### `packages/general.py`

```python
from disunity import package          # disunity.package module
from disunity.models import Context    # for type hints only

class General(package.Package):
    def __init__(self, app):
        self.app = app

    @package.Package.command("ping")     # requires_ack=False, requires_ephemeral=False
    async def ping(self, ctx: Context):
        return await ctx.callback("Pong!")

def setup(app):                          # REQUIRED entry point; called by load_package
    app.register_package(General(app))
```

Discord must be configured to POST to `https://<your-host>/interactions`. The server only listens
on that one route. See [server.md](server.md) for the request lifecycle.

## The single most important invariant

A handler responds in **exactly one** of two ways, decided by the decorator's `requires_ack`:

- **`requires_ack=False` (default):** the handler must **`return`** a response dict, almost always
  by `return await ctx.callback(...)` (or `return await ctx.modal_response(...)`, or a raw dict).
  The returned dict is what the server sends back to Discord. Do **not** call `ctx.followup`.
- **`requires_ack=True`:** the server **immediately** sends a "deferred" (thinking…) response and
  runs your handler as a background `asyncio` task. Inside the handler you must use
  **`await ctx.followup(...)`** to send the real message. The handler's return value is **discarded**.
  Calling `ctx.callback` here does nothing useful.

Getting this wrong is the most common failure. Full details in [gotchas.md](gotchas.md).
