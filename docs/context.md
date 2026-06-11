# `Context` (and `Interaction`)

`Context` is the object passed to every handler. It subclasses `Interaction`. You normally do not
construct it — the server builds `Context(self, received)` per interaction.

- `Context`: [src/disunity/models/context.py:8](src/disunity/models/context.py:8)
- `Interaction` (base): [src/disunity/models/interaction.py:7](src/disunity/models/interaction.py:7)

Import for type hints: `from disunity.models import Context` (not exported at top level).

---

## Responding — pick exactly one path

| Situation | How to respond |
|-----------|----------------|
| Handler decorated `requires_ack=False` (default) | **`return await ctx.callback(...)`** (or `return await ctx.modal_response(...)`, or return a raw dict). |
| Handler decorated `requires_ack=True` | Server already deferred. Use **`await ctx.followup(...)`**. Return value is ignored. |

---

## `await ctx.callback(...)`

**Source:** [src/disunity/models/context.py:19](src/disunity/models/context.py:19)

```python
async def callback(self, content=None, embeds=[], components=[],
                   ephemeral=False,
                   response_type=InteractionCallbackTypes.CHANNEL_MESSAGE_WITH_SOURCE) -> dict
```

Builds (and returns) the **first** interaction-response dict. Does **not** perform any HTTP request —
it just returns the dict your handler should `return`. Also sets `self.acked = True`.

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `content` | `str \| None` | `None` | Message text. `None` → empty string `""`. Non-str is `str()`-coerced. |
| `embeds` | `Embed \| list[Embed]` | `[]` | One embed or a list; a single `Embed` is wrapped in a list. Each is serialized via `.as_dict()`. Non-`Embed` items are filtered out. |
| `components` | `ActionRow \| list[ActionRow]` | `[]` | One `ActionRow` or a list; serialized via `.to_dict()`. **Must be `ActionRow`s** — raw `Button`/`SelectMenu` are filtered out. A `Modal` cannot be sent here (use `modal_response`). |
| `ephemeral` | `bool` | `False` | If `True`, sets `data.flags = 64` (only the invoker sees it). |
| `response_type` | `int` | `4` (`CHANNEL_MESSAGE_WITH_SOURCE`) | The interaction callback type. See table below. |

**Returns:** `dict` of shape `{"type": response_type, "data": {"content", "embeds", "components"[, "flags"]}}`.

> The docstring lists an `allowed_mentions` parameter — it does **not** exist in the signature.
> Ignore it.

### `response_type` values (`utils.InteractionCallbackTypes`, [src/disunity/utils.py:14](src/disunity/utils.py:14))

| Value | Name | Use with `callback` |
|------:|------|---------------------|
| `1` | `PONG` | Internal (ping). Not for handlers. |
| `4` | `CHANNEL_MESSAGE_WITH_SOURCE` | **Default.** Send a new message in response. |
| `5` | `DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE` | "Thinking…" defer for a command. The server emits this automatically when `requires_ack=True`; you don't pass it manually. |
| `6` | `DEFERRED_UPDATE_MESSAGE` | Component-only "defer & keep message". Emitted automatically for acked components. Acknowledges a component without changing the message yet. |
| `7` | `UPDATE_MESSAGE` | **Component-only.** Edit the message the component is attached to (replace its content/embeds/components) instead of sending a new one. Pass `response_type=7` from a non-acked component handler. |
| `8` | `APPLICATION_COMMAND_AUTOCOMPLETE_RESULT` | Autocomplete results. Emitted by the router; not via `callback`. |
| `9` | `MODAL` | Open a modal. Use `ctx.modal_response(modal)` instead of crafting this. |
| `10` | `PREMIUM_REQUIRED` | Prompt the user to buy a premium SKU. **UNVERIFIED** in practice here. |

```python
# new public message with a button
row = ActionRow([Button("vote-1", "Vote", ButtonStyles.SUCCESS)])
return await ctx.callback("Cast your vote", components=row)

# component handler editing its own message
return await ctx.callback("Updated!", response_type=7)
```

---

## `await ctx.followup(...)`

**Source:** [src/disunity/models/context.py:69](src/disunity/models/context.py:69)

```python
async def followup(self, content=None, embeds=[], components=[],
                   attachments=[], ephemeral=False) -> Message
```

Sends a webhook follow-up to an **already-acked** interaction (i.e. after a deferred response, or
after `callback` set `acked`). Performs an actual HTTP `POST` to
`webhooks/{client_id}/{interaction_token}` and returns a `Message`.

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `content` | `str \| None` | `None` | Text (`None` → `""`). |
| `embeds` | `Embed \| list[Embed]` | `[]` | As in `callback`. |
| `components` | `ActionRow \| list[ActionRow]` | `[]` | As in `callback`. |
| `attachments` | `Attachment \| list[Attachment]` | `[]` | Files to upload; sent as multipart, indexed by position. See [models.md](models.md) `Attachment`. |
| `ephemeral` | `bool` | `False` | `flags = 64` on the follow-up. |

**Raises:** `errors.InvalidMethodUse` if `self.acked` is `False` ("Cannot followup an interaction that
hasn't been acked"). **Returns:** `Message` ([src/disunity/models/message.py:20](src/disunity/models/message.py:20))
wrapping the created message, carrying the interaction token for later edit/delete.

```python
@package.Package.command("report", True)        # acked
async def report(self, ctx):
    msg = await ctx.followup("Generating…")       # returns a Message
    # ... later you can msg.edit_as_webhook(...)
```

> ⚠️ Interaction tokens expire ~15 minutes after the interaction. `followup` after that raises an
> HTTP error. The original interaction must be answered (ack or callback) within **3 seconds** or
> Discord invalidates it. See [gotchas.md](gotchas.md).

---

## `await ctx.modal_response(modal)`

**Source:** [src/disunity/models/context.py:139](src/disunity/models/context.py:139)

Returns `{"type": 9, "data": modal.to_dict()}` to open a modal. The interaction must **not** already
be acknowledged (you cannot open a modal after `callback`/defer). `modal` is a
`disunity.models.Modal` ([src/disunity/models/components.py:217](src/disunity/models/components.py:217)).

```python
from disunity.models import Modal, UserTextInput

@package.Package.command("feedback")
async def feedback(self, ctx):
    modal = Modal("Feedback", "fb-modal", [UserTextInput("fb-text", "Your thoughts")])
    return await ctx.modal_response(modal)
```

Modal submissions arrive as a separate interaction routed to a `@Package.component` whose name
matches the modal's `custom_id` prefix. Submitted values are in `ctx.modal_values` (see below).

---

## `Context` attributes

Set in `Context.__init__` and the `Interaction` base:

| Attribute | Type | Source | Meaning |
|-----------|------|--------|---------|
| `_app` | `DisunityServer` | context.py:11 | The server (used by `followup` etc.). |
| `acked` | `bool` | context.py:12 | Whether a response has been sent. Set by `callback`, the ack path, or manually. |
| `options` | `dict` | context.py:13 | `{option_name: value}` flattened from the interaction. |
| `raw` | `dict` | interaction.py:9 | The full received payload. |
| `app_permissions` | `int` | interaction.py:10 | Bot's permissions bitfield in the channel. |
| `channel_id` | `int` | interaction.py:12 | Channel id. |
| `id` | `int` | interaction.py:13 | Interaction id. |
| `locale` | `str` | interaction.py:14 | Invoker locale. |
| `token` | `str` | interaction.py:15 | Interaction token (for follow-ups). |
| `interaction_type` | `int` | interaction.py:16 | `utils.InteractionTypes` value. |
| `data` | `dict` | interaction.py:17 | `received["data"]`. |
| `resolved` | `dict \| None` | interaction.py:18 | Resolved entities (users/roles/channels/attachments) for option ids. |
| `component_type` | `int \| None` | interaction.py:19 | For components: 2=button, 3=select, etc. |
| `custom_id` | `str \| None` | interaction.py:20 | Component/modal custom id. |
| `values` | `list` | interaction.py:21 | Selected values for select menus. |
| `member` | `Member \| None` | interaction.py:22 | Guild member object (None in DMs). |
| `used_by` | `User \| None` | interaction.py:23 | For components: the user who clicked. |
| `command_name` | `str \| None` | interaction.py:24 | Command name (`data["name"]`); for subcommands this is the **base** name. |
| `modal_values` | `list[dict] \| None` | interaction.py:25/48 | For modal submits: the input components of the first action row (`data["components"][0]["components"]`). Each dict has `custom_id`, `value`, etc. |
| `invoked_by` | `User \| None` | interaction.py:28+ | The user who originally invoked. For commands: the invoker. For components: the user who triggered the *original* message's interaction (or `None` if absent). |

### `invoked_by` vs `used_by` (components)

For a **command/modal**, `invoked_by` is the acting user and `used_by` is `None`.
For a **message component**, `invoked_by` is the user tied to the original message's interaction
(the person who summoned the message), and `used_by` is the user who just clicked. This powers
`check_user()`.

### `check_user() -> bool`

**Source:** [src/disunity/models/interaction.py:52](src/disunity/models/interaction.py:52)

Component-only. Returns `True` if the clicker (`used_by`) is the same user who invoked the original
message (`invoked_by`). Raises `InvalidMethodUse` if called on a non-component interaction. Use it to
restrict buttons to their owner.

```python
@package.Package.component("confirm")
async def confirm(self, ctx):
    if not ctx.check_user():
        return await ctx.callback("This isn't your button.", ephemeral=True)
    return await ctx.callback("Done", response_type=7)
```

> If the original message has no `interaction` field, `invoked_by` is `None` and `check_user()` will
> raise `AttributeError` on `self.invoked_by.id`. Guard accordingly.
