# Commands & autocomplete

This covers plain slash commands (no subcommands). For subcommands see
[subcommands.md](subcommands.md); for the decorator parameter table see [packages.md](packages.md).

## Declaring a command

```python
from disunity import package

class Misc(package.Package):
    def __init__(self, app):
        self.app = app

    @package.Package.command("echo")
    async def echo(self, ctx):
        text = ctx.options.get("text", "")
        return await ctx.callback(text)
```

The handler is `async def (self, ctx: Context)`. It either **returns** a response dict (non-ack) or
uses `ctx.followup` (ack). See the ack invariant in [index.md](index.md) and [gotchas.md](gotchas.md).

## Reading options — `ctx.options`

**Source:** [src/disunity/models/context.py:13](src/disunity/models/context.py:13)

When the server routes a command it copies the interaction's option list into
`received["data"]["injected"]`, and `Context.__init__` flattens that into a plain dict:

```python
self.options = {}
for option in received["data"].get("injected", []):
    self.options[option["name"]] = option["value"]
```

So `ctx.options` is `{ option_name: option_value }`. Values are whatever Discord sent (string / int /
bool / snowflake-as-string, depending on the option type). For resolved entities (users, channels,
roles, attachments) you get the **id**; the full objects are in `ctx.resolved`
([src/disunity/models/interaction.py:18](src/disunity/models/interaction.py:18)).

```python
@package.Package.command("ban", True)     # acked
async def ban(self, ctx):
    user_id = ctx.options["target"]        # snowflake string for a USER option
    reason  = ctx.options.get("reason", "No reason")
    await ctx.followup(f"Banned <@{user_id}> — {reason}")
```

> There is **no** typed option-parsing layer. `ctx.options` gives raw values; resolve ids against
> `ctx.resolved` yourself if you need objects.

## Command type caveat

`Command.command_type` is hardcoded to `2` ([src/disunity/identifiers.py:152](src/disunity/identifiers.py:152)),
and commands are cached under the key `"2"`. The router looks commands up under
`str(received["type"])`, and the interaction type for application commands is also `2`. These two
distinct meanings of "2" coincide, so **CHAT_INPUT slash commands work**. The framework does **not**
distinguish USER (type 2) or MESSAGE (type 3) context-menu commands — treat it as slash-commands-only
unless you verify otherwise. **UNVERIFIED** that context-menu commands route correctly.

## Autocomplete

Declared with `@Package.autocomplete("command_name")`
([src/disunity/package.py:135](src/disunity/package.py:135)). The handler must return a `list` of
choice dicts. The autocomplete interaction has its own `Context`; the option the user is typing is in
`ctx.options` / `ctx.raw` like any command. The router responds with type `8`
(`APPLICATION_COMMAND_AUTOCOMPLETE_RESULT`).

```python
COLORS = ["blue", "red", "green"]

@package.Package.command("color")
async def color(self, ctx):
    return await ctx.callback(f"You picked {ctx.options['name']}")

@package.Package.autocomplete("color")
async def color_ac(self, ctx):
    typed = ctx.options.get("name", "")
    return [{"name": c.title(), "value": c} for c in COLORS if c.startswith(typed)]
```

Notes:
- Autocomplete handlers are **never** acked/deferred and `global_after_interaction` is not invoked
  for them.
- Returning a non-list (or raising) yields an empty choice list.
- A registered autocomplete for an unknown command name raises `AutocompleteNotFound` at request
  time ([src/disunity/errors.py:16](src/disunity/errors.py:16)).
