# Data models — `User`, `Member`, `Message`, `Attachment`, `Embed`

These wrap Discord payload data and/or build outgoing JSON. `User`, `Member`, `Message`,
`Attachment` are re-exported from `disunity.models`; `Embed`, `Message`, `Attachment` are also at the
top level (`disunity.Embed`, `disunity.Message`, `disunity.Attachment`).

---

## `User(received)`
**Source:** [src/disunity/models/user.py:4](src/disunity/models/user.py:4)

Constructed by the framework from a Discord user object. Attributes:

| Attribute | Type | Meaning |
|-----------|------|---------|
| `raw` | `dict` | Original payload. |
| `id` | `int` | User id. |
| `name` | `str` | `username`. |
| `global_name` | `str` | Display name (new username system). |
| `discriminator` | `int` | Legacy discriminator (`0` for migrated accounts). |
| `avatar_decoration` | `str` | `avatar_decoration` or `""`. |
| `public_flags` | `int` | Public flags bitfield (default `0`). |

Properties:
- `avatar_url` → CDN avatar URL via `utils.return_avatar_as_cdn(raw["avatar"], id)`. ⚠️ Reads
  `self.raw["avatar"]` directly; raises `KeyError` if the payload had no `avatar` key.
- `username` → `f"{name}#{discriminator}"` (legacy format).
- `mention` → `f"<@!{id}>"`.

> Requires `username`, `global_name`, `discriminator` keys present, or `__init__` raises `KeyError`.

---

## `Member(received)`
**Source:** [src/disunity/models/member.py:5](src/disunity/models/member.py:5)

Guild member wrapper. Attributes: `raw`, `deaf` (bool), `pending` (bool, default `False`),
`joined_at` (raw str), `mute` (bool), `nick` (str), `permissions` (int, default `0`),
`roles` (`list[int]`), `user` (`User`), `flags` (int).

Property `server_avatar_url` → guild-specific avatar CDN URL, or `None` when the member has no guild
avatar. ⚠️ It checks `self.raw["avatar"] != "None"` (string comparison), so behavior depends on the
exact payload value.

> `__init__` requires `deaf`, `joined_at`, `mute`, `nick`, `roles`, `user`, `flags` keys — missing
> any raises `KeyError`.

---

## `Attachment(filename, content, description=None)`
**Source:** [src/disunity/models/attachment.py:1](src/disunity/models/attachment.py:1)

Outgoing file for `ctx.followup(attachments=...)`.

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `filename` | `str` | — | File name (content type guessed from this). |
| `content` | `bytes` | — | Raw file bytes. |
| `description` | `str` | `None` | Alt text / description. |

Properties (`filename`, `content`, `description`) are read/write. `as_dict()` →
`{"filename", "description", "content"}`.

> In `followup`, attachments are sent as multipart `files[<index>]` with the JSON `attachments`
> array referencing the same indices ([src/disunity/models/context.py:112](src/disunity/models/context.py:112)).

```python
from disunity import Attachment
att = Attachment("report.txt", b"hello world", description="A report")
await ctx.followup("Here you go", attachments=att)   # acked handler
```

---

## `Message(raw_message, server, token=None)`
**Source:** [src/disunity/models/message.py:20](src/disunity/models/message.py:20)

Returned by `ctx.followup(...)`. Wraps a created/fetched message and offers edit/delete helpers.
You normally receive one rather than construct it.

Attributes: `server`, `raw`, `id` (int), `author` (`User | None`), `channel_id`,
`components` (list), `embeds` (list), `attachments`, `content` (str),
`interaction_token` (str | None — the token used for webhook edits).

> ⚠️ `attachments` reads `raw_message.get("attachements")` — **misspelled** key, so it's almost
> always `None` regardless of actual attachments. Treat `Message.attachments` as unreliable.

### `await message.edit_as_webhook(content=None, embeds=None, components=None) -> Message`
**Source:** [src/disunity/models/message.py:42](src/disunity/models/message.py:42)
PATCHes the message via the interaction webhook
(`webhooks/{client_id}/{interaction_token}/messages/{id}`). `None` args keep the existing value.
Single `Embed`/`ActionRow` are wrapped in a list. On a non-2xx with Discord error code `10015`/`50027`
raises `ExpiredInteractionError`. Mutates the object (`remake`) and returns `self`.

### `await message.edit_as_bot(content=None, embeds=None, components=None) -> Message`
**Source:** [src/disunity/models/message.py:81](src/disunity/models/message.py:81)
PATCHes via the bot API (`channels/{channel_id}/messages/{id}`). **Raises `MissingTokenError`** if no
`bot_token` is configured. Returns `self`.

### `await message.delete_as_webhook()`
**Source:** [src/disunity/models/message.py:117](src/disunity/models/message.py:117)
DELETEs via the interaction webhook.

### `await message.delete_as_bot()`
**Source:** [src/disunity/models/message.py:123](src/disunity/models/message.py:123)
DELETEs via the bot API. **Raises `MissingTokenError`** without a bot token.

`MissingTokenError` / `ExpiredInteractionError` are defined in
[src/disunity/models/message.py:8](src/disunity/models/message.py:8).

---

## `Embed(title=None, description=None, color=None)`
**Source:** [src/disunity/embed.py:9](src/disunity/embed.py:9)

Builder for rich embeds. The internal JSON always starts as `{"type": "rich", "color": color}`.
Exported as `disunity.Embed`.

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `title` | `str \| None` | `None` | Title (str-coerced via setter). |
| `description` | `str \| None` | `None` | Description (str-coerced). |
| `color` | `int \| None` | `None` | Integer color (e.g. `0x5865F2`). |

Read/write properties: `title`, `description`, `color`. Read-only: `fields`, `footer`, `image`,
`thumbnail`, `author` (return the stored dicts/list or `None`).

Builder methods (each returns `self` for chaining):

| Method | Source | Effect |
|--------|--------|--------|
| `add_field(name, value, inline=False)` | embed.py:60 | Appends a field. **Raises `EmptyEmbedError`** if `name` or `value` is empty/falsy. |
| `set_footer(text=None, icon_url=None)` | embed.py:74 | Sets footer text/icon. |
| `set_image(image_url)` | embed.py:90 | Sets the main image url. |
| `set_thumbnail(thumbnail_url)` | embed.py:101 | Sets the thumbnail url. |
| `set_author(name, url=None, icon_url=None)` | embed.py:112 | Sets the author block. |

`as_dict()` ([src/disunity/embed.py:126](src/disunity/embed.py:126)) returns the JSON. `callback`,
`followup`, and `Message.edit_*` call this for you when you pass `Embed` objects.

> Minor source quirks (don't rely on these properties for logic): the `image` property reads
> `self.__json.get("url")` (wrong key — it should be `"image"`), and `EmptyEmbedError` is defined in
> `embed.py`, not `errors.py`.

```python
from disunity import Embed
emb = (Embed("Status", "All systems go", color=0x57F287)
       .add_field("Region", "us-east", inline=True)
       .set_footer("updated just now"))
return await ctx.callback(embeds=emb)
```
