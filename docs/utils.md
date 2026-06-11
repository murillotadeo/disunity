# `disunity.utils`

**Source:** [src/disunity/utils.py](src/disunity/utils.py). Exported as `disunity.utils`.

## `__version__`
`"0.1.3"` ([utils.py:3](src/disunity/utils.py:3)). ⚠️ Stale — the build version in `pyproject.toml`
is `0.1.17`. Don't trust `utils.__version__` for the installed version.

## `InteractionTypes(IntEnum)`
**Source:** [utils.py:6](src/disunity/utils.py:6)
The incoming interaction `type` discriminator.

| Member | Value |
|--------|------:|
| `PING` | 1 |
| `APPLICATION_COMMAND` | 2 |
| `MESSAGE_COMPONENT` | 3 |
| `APPLICATION_COMMAND_AUTOCOMPLETE` | 4 |
| `MODAL_SUBMIT` | 5 |

## `InteractionCallbackTypes(IntEnum)`
**Source:** [utils.py:14](src/disunity/utils.py:14)
The `type` you send back in a response. See [context.md](context.md) for which to use with
`ctx.callback`.

| Member | Value | Notes |
|--------|------:|-------|
| `PONG` | 1 | Ping ack. |
| `CHANNEL_MESSAGE_WITH_SOURCE` | 4 | New message (callback default). |
| `DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE` | 5 | Command defer (auto-sent for acked commands). |
| `DEFERRED_UPDATE_MESSAGE` | 6 | Component defer (auto-sent for acked components). |
| `UPDATE_MESSAGE` | 7 | Edit the component's source message. |
| `APPLICATION_COMMAND_AUTOCOMPLETE_RESULT` | 8 | Autocomplete choices. |
| `MODAL` | 9 | Open a modal (via `ctx.modal_response`). |
| `PREMIUM_REQUIRED` | 10 | Premium upsell. **UNVERIFIED** here. |

## `DefaultAvatars(Enum)`
**Source:** [utils.py:25](src/disunity/utils.py:25)
`blurple=0`, `grey=1`, `gray=1`, `green=2`, `orange=3`, `red=4`. `__str__` returns the member name.
Used to size the default-avatar modulo.

## `return_avatar_as_cdn(avatar, uid) -> str`
**Source:** [utils.py:37](src/disunity/utils.py:37)
Builds a Discord CDN avatar URL.
- If `avatar` is not `None`: `https://cdn.discordapp.com/avatars/{uid}/{avatar}.{gif|png}?size=1024`
  (`gif` when the hash starts with `a_`, else `png`).
- If `avatar` is `None`: a default embed avatar `…/embed/avatars/{uid % len(DefaultAvatars)}.png`.

Used by `User.avatar_url` and `Member.server_avatar_url`.
