# Packages & decorators — `Package`

Defined in [src/disunity/package.py](src/disunity/package.py). A `Package` is a class that groups
handlers. You subclass it, decorate `async` methods to declare handlers, instantiate the subclass,
and register the instance with `app.register_package(...)`.

```python
from disunity import package

class MyPackage(package.Package):
    def __init__(self, app):
        self.app = app          # conventional; not required by the base class

    @package.Package.command("ping")
    async def ping(self, ctx):
        return await ctx.callback("Pong!")

def setup(app):
    app.register_package(MyPackage(app))
```

> The base `Package.__init__` sets `self.commands = []` and `self.components = []`
> ([src/disunity/package.py:9](src/disunity/package.py:9)). If you override `__init__` (the common
> case, to store `app`), you do **not** need to call `super().__init__()` — those two attributes are
> unused by routing; handler discovery happens in `unpack()` via introspection, not those lists.

All decorators are `@classmethod`s, so you always write `@Package.command(...)` /
`@package.Package.command(...)`, never `@self.command`.

All decorated methods **must** be `async def` (coroutine functions) or the decorator raises
`TypeError` at class-definition time. `staticmethod`-wrapped coroutines are unwrapped and supported.

Every decorator works by stamping marker attributes (`__command__`, `__component__`,
`__subcommand__`, `__autocomplete__`, `__data__`) onto the function, which `unpack()` later reads.

---

## `@Package.command(name, requires_ack=False, requires_ephemeral=False)`

**Source:** [src/disunity/package.py:13](src/disunity/package.py:13)

Declares a top-level slash command (no subcommands).

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `name` | `str` | — | The command name. Must match the registered Discord command name; this is the routing key. |
| `requires_ack` | `bool` | `False` | If `True`, the server immediately sends a deferred ("thinking…") response and runs the handler in the background; the handler must reply with `ctx.followup(...)`. If `False`, the handler must **return** a response dict (`return await ctx.callback(...)`). |
| `requires_ephemeral` | `bool` | `False` | Only meaningful when `requires_ack=True`: makes the deferred response ephemeral. ⚠️ **Currently crashes for commands** — see the bug note in [server.md](server.md) / [gotchas.md](gotchas.md). For non-ack commands it has no effect (use `ctx.callback(..., ephemeral=True)`). |

**Positional usage:** `@Package.command("name", True, False)` ≡
`requires_ack=True, requires_ephemeral=False`. Order is always `(name, requires_ack, requires_ephemeral)`.

**Handler signature:** `async def handler(self, ctx: Context)`. Reads command options from
`ctx.options` (a `{name: value}` dict). See [commands.md](commands.md).

```python
@Package.command("ban", True)              # acked, public
async def ban(self, ctx):
    # acked: must use followup, return value ignored
    await ctx.followup(f"Banned {ctx.options['user']}")

@Package.command("hello")                  # not acked
async def hello(self, ctx):
    return await ctx.callback("hi", ephemeral=True)
```

Internally stamps `__data__ = (name, requires_ack, requires_ephemeral)` and `unpack()` builds a
`Command(name, method, requires_ack, requires_ephemeral)`
([src/disunity/identifiers.py:143](src/disunity/identifiers.py:143)). `Command.command_type` is
hardcoded to `2`.

---

## `@Package.component(name, requires_ack=False, requires_ephemeral=False, timeout=0.0)`

**Source:** [src/disunity/package.py:51](src/disunity/package.py:51)

Declares a handler for a message component (button / select menu) **and** for modal submits — both
route by `custom_id`.

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `name` | `str` | — | The component name. **Routing key.** Discord delivers a `custom_id`; the server matches the substring **before the first `-`** against this name. So a button with `custom_id="vote-12345"` routes to the component named `"vote"`. See "custom_id rules" below and [components.md](components.md). |
| `requires_ack` | `bool` | `False` | If `True`, the server sends a deferred **update** response (type 6) and runs the handler in the background; respond with `ctx.followup(...)`. If `False`, the handler must return a response dict. |
| `requires_ephemeral` | `bool` | `False` | Only with `requires_ack=True`: makes the deferred update ephemeral (`flags: 64`). This branch is implemented correctly for components ([src/disunity/server.py:319](src/disunity/server.py:319)). |
| `timeout` | `float` | `0.0` | Seconds after the **source message's** timestamp during which the component stays valid. `0.0` (or any `<= 0.0`) means **no timeout**. When set and exceeded, a non-acked component returns a "This component has timed out." ephemeral message instead of running. See "timeout semantics". |

**Positional order:** `(name, requires_ack, requires_ephemeral, timeout)`.

**custom_id rules (critical):**
- The component **name** must not contain `-`, because routing splits on the first `-`.
- The actual `custom_id` you put on the button/menu is `f"{name}-{tag}"`, where `tag` is any
  per-instance discriminator (the docstring suggests the interaction id). Everything after the first
  `-` is ignored by routing but available to you as `ctx.custom_id`.
- A bare `custom_id` with no `-` still routes (`"vote".split("-")[0] == "vote"`).

**timeout semantics** (from [src/disunity/identifiers.py:120](src/disunity/identifiers.py:120)):
- Stored as `None` if `timeout <= 0.0`, else the float.
- On invocation, if a timeout is set, the server computes
  `now_utc - message.timestamp` from `ctx.raw["message"]["timestamp"]`. If that exceeds `timeout`
  **and** `requires_ack` is `False`, it returns `{"type": 4, "data": {"content": "This component has
  timed out.", "flags": 64}}` and your handler never runs.
- ⚠️ If `requires_ack=True`, the timeout check **does nothing** — acked components always run
  regardless of age (the timeout return is guarded by `if not self.ack`).

**Handler signature:** `async def handler(self, ctx: Context)`.

```python
@Package.component("confirm", timeout=60.0)   # button valid for 60s after its message
async def confirm(self, ctx):
    if not ctx.check_user():                   # only the original invoker may click
        return await ctx.callback("Not for you.", ephemeral=True)
    return await ctx.callback("Confirmed!", response_type=7)  # 7 = edit the message
```

Internally stamps `__data__ = (name, requires_ack, requires_ephemeral, timeout)`; `unpack()` builds
`Component(name, method, requires_ack, requires_ephemeral, timeout)`
([src/disunity/identifiers.py:105](src/disunity/identifiers.py:105)).

---

## `@Package.sub(name, sub_commands, group=None)`

**Source:** [src/disunity/package.py:97](src/disunity/package.py:97)

Declares subcommands. Covered in detail in [subcommands.md](subcommands.md).

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `name` | `str` | — | The base command name (the top-level slash command). |
| `sub_commands` | `list[str \| SubOption] \| str \| SubOption` | — | The subcommand name(s) under this base routed to this method. Use a `SubOption` to give a specific subcommand its own `requires_ack` / `requires_ephemeral`; a bare `str` means a subcommand with ack=False, ephemeral=False. |
| `group` | `str \| None` | `None` | If set, these subcommands belong to a subcommand **group** of that name. |

`unpack()` builds `TopLevelSubCommand(name, method, sub_commands, group)`. Multiple `@Package.sub`
decorations sharing the same base `name` are merged in the cache. See [subcommands.md](subcommands.md).

---

## `@Package.autocomplete(command_name)`

**Source:** [src/disunity/package.py:135](src/disunity/package.py:135)

Declares the autocomplete provider for a command's options.

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `command_name` | `str` | — | The command whose options this provides autocomplete for. Routing key (matched against the incoming autocomplete interaction's command name). |

**Handler signature:** `async def handler(self, ctx: Context)`. **Must return a `list`** of Discord
choice dicts (`{"name": <label>, "value": <value>}`). A non-list / exception yields `[]`. The server
wraps it as `{"type": 8, "data": {"choices": [...]}}`.

```python
@Package.autocomplete("color")
async def color_autocomplete(self, ctx):
    return [{"name": "Blue", "value": "blue"}, {"name": "Red", "value": "red"}]
```

Builds `Autocomplete(command_name, method)`
([src/disunity/identifiers.py:166](src/disunity/identifiers.py:166)).

---

## `Package.unpack()`

**Source:** [src/disunity/package.py:179](src/disunity/package.py:179)

Called by `register_package`. Introspects the instance for coroutine-function members whose names do
**not** start or end with `__`, reads each one's `__data__` + marker attributes, and returns a list
of `Command` / `Component` / `TopLevelSubCommand` / `Autocomplete` objects. Methods without a
`__data__` attribute (i.e. not decorated) are silently skipped (`AttributeError` → `continue`).

You normally never call this yourself.
