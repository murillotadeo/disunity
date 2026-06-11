# Subcommands & subcommand groups

Subcommands are declared with `@Package.sub` and a `SubOption`. The relevant source is
[src/disunity/package.py:97](src/disunity/package.py:97) (decorator),
[src/disunity/identifiers.py:5](src/disunity/identifiers.py:5) (`SubOption`, `SubCommand`,
`TopLevelSubCommand`, `CacheableSubCommand`), and the router `match` block at
[src/disunity/server.py:234](src/disunity/server.py:234).

---

## `SubOption(name, requires_ack=False, requires_ephemeral=False)`

**Source:** [src/disunity/identifiers.py:5](src/disunity/identifiers.py:5)

A lightweight descriptor that lets one subcommand carry its own ack/ephemeral settings. Exported at
top level as `disunity.SubOption`.

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `name` | `str` | — | The subcommand name (as registered with Discord). |
| `requires_ack` | `bool` | `False` | Defer this subcommand (respond via `ctx.followup`). Stored on `SubOption.ack`. |
| `requires_ephemeral` | `bool` | `False` | Only with ack: ephemeral deferred response. Stored on `SubOption.ephemeral`. |

```python
from disunity import SubOption
SubOption("delete", requires_ack=True, requires_ephemeral=True)
```

A bare `str` used in place of a `SubOption` is equivalent to `SubOption(name, False, False)`.

---

## `@Package.sub(name, sub_commands, group=None)`

**Source:** [src/disunity/package.py:97](src/disunity/package.py:97)

One decorated method handles one or more subcommands of the base command `name`. The **same**
handler coroutine is invoked for every subcommand it lists; branch on `ctx.command_name` or the
options to tell them apart (see "routing & dispatch" below).

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `name` | `str` | — | Base (top-level) command name. |
| `sub_commands` | `str \| SubOption \| list[str \| SubOption]` | — | Subcommand(s) this method handles. |
| `group` | `str \| None` | `None` | The subcommand-group name these belong to, or `None` for direct subcommands of the base. |

### How `sub_commands` is normalized

`TopLevelSubCommand.__init__` ([src/disunity/identifiers.py:50](src/disunity/identifiers.py:50))
turns the argument into a list of `SubCommand` objects, all bound to the **same** coroutine:
- `str` → `SubCommand(name, coroutine, False, False)`
- `SubOption` → `SubCommand(opt.name, coroutine, opt.ack, opt.ephemeral)`
- `list` → each element handled as above (a list may mix `str` and `SubOption`).

### Cache merge

`ApplicationCache.add_item` ([src/disunity/cache.py:19](src/disunity/cache.py:19)) stores subcommand
bases under `commands["2"][base_name]` as a `CacheableSubCommand`. Multiple `@Package.sub`
decorations with the **same base `name`** are merged (`.add(incoming)`), so you can split a base
command's subcommands across several methods.

`CacheableSubCommand.map` ([src/disunity/identifiers.py:88](src/disunity/identifiers.py:88)) layout:
- Direct subcommands (`group is None`) → `map["sub_commands"][sub_name] = SubCommand`.
- Grouped subcommands → `map[group_name][sub_name] = SubCommand`.

---

## Routing & dispatch

The router `match`es the incoming command's `data.options`
([src/disunity/server.py:234](src/disunity/server.py:234)):

1. **Subcommand group** — `options == [{"name": <group>, "options": [...], "type": 2}]`:
   `coroutine = command.map[group].get(sub_name)`, where `sub_name = options[0]["name"]`. The
   subcommand's own options are injected as `data["injected"] = options[0]["options"]`.
2. **Direct subcommand** — `options == [{"name": <sub>, "options": [...], "type": 1}]`:
   `coroutine = command.map["sub_commands"].get(sub_name)`; injected options = `options`.
3. **Plain command with options** / **bare command** — falls through to non-subcommand handling.

If the matched base command is not a `CacheableSubCommand`, the router raises `InvalidMethodUse`
("…must be registered using the `Package.sub` decorator"). If the specific subcommand isn't found,
`CommandNotFound` is raised.

A subcommand's ack/ephemeral come from its `SubCommand` (i.e. from the `SubOption` you supplied),
**not** from the base. The deferred-command ephemeral bug (see [server.md](server.md)) applies here
too — `requires_ephemeral=True` on an acked subcommand will hit the same `KeyError`.

---

## Examples

### Direct subcommands

```python
from disunity import package, SubOption

class Settings(package.Package):
    def __init__(self, app):
        self.app = app

    # one method handles both `/config get` and `/config set`
    @package.Package.sub("config", ["get", SubOption("set", requires_ack=True)])
    async def config(self, ctx):
        if ctx.command_name == "config":          # base name; dispatch on the sub
            ...
        sub = ctx.raw["data"]["options"][0]["name"]   # the chosen subcommand name
        if sub == "get":
            return await ctx.callback("current value …")
        else:  # "set" — acked
            await ctx.followup("updated")
```

> Distinguishing which subcommand fired: `ctx.command_name` holds the **base** name. The chosen
> subcommand name is in the raw payload (`ctx.raw["data"]["options"][0]["name"]`), and that
> subcommand's options have been flattened into `ctx.options`.

### Subcommand group

```python
@package.Package.sub("mod", ["ban", "kick"], group="punish")
async def punish(self, ctx):
    # routed for `/mod punish ban` and `/mod punish kick`
    ...
```

You can add more subcommands to the same `mod` base from another method, e.g.
`@Package.sub("mod", ["info"])` for `/mod info`.
