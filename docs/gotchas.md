# Gotchas & invariants

Non-obvious behaviors that can't be inferred from signatures. Each is grounded in source. Read this
before editing handlers.

---

## 1. Respond exactly once; the method depends on `requires_ack`

- **`requires_ack=False` (default):** the handler must **`return`** a dict — normally
  `return await ctx.callback(...)`. The router does `response = await coroutine(ctx); return jsonify(response)`
  ([server.py:293](src/disunity/server.py:293)). If you `return None`, `jsonify(None)` is sent and
  Discord gets a malformed/empty response (the interaction effectively fails).
- **`requires_ack=True`:** the router **immediately** returns a deferred response and runs your
  handler as a background `asyncio.create_task` ([server.py:285](src/disunity/server.py:285)). The
  handler must use **`await ctx.followup(...)`**. Its return value is **discarded**. Calling
  `ctx.callback` in an acked handler builds a dict that goes nowhere.

**When is ack mandatory?** Discord requires *some* response within **3 seconds**. If your handler
does slow work (DB, external HTTP, anything that may exceed ~3s) before it can produce a message,
you **must** set `requires_ack=True` so the framework defers immediately; otherwise the interaction
times out and the user sees "This interaction failed." If the handler always replies fast, leave
`requires_ack=False`.

---

## 2. `requires_ephemeral=True` crashes acked **commands** (real bug)

In the command ack branch:
```python
response = {"type": 5}                      # no "data" key
if coroutine.ephemeral:
    response["data"]["flags"] = 64          # KeyError: 'data'
```
([server.py:279-283](src/disunity/server.py:279)). So `@Package.command("x", True, True)` (or an
acked `SubOption(..., requires_ephemeral=True)`) raises `KeyError` at request time and never responds.

**Workaround:** use `@Package.command("x", True)` (ephemeral=False) and make the message ephemeral on
the follow-up: `await ctx.followup(..., ephemeral=True)`.

The **component** ack branch builds the `data` dict correctly
([server.py:319](src/disunity/server.py:319)), so `requires_ephemeral=True` works for components.

---

## 3. `response_type` cheat sheet

`ctx.callback(response_type=...)`:
- **`4`** (default) — send a new message.
- **`7`** (`UPDATE_MESSAGE`) — **component handlers only**: edit the message the button/select is on,
  rather than posting a new message. This is how you update a button's own message in a non-acked
  component handler.
- **`6`** (`DEFERRED_UPDATE_MESSAGE`) — the "acknowledge silently, edit later" defer for components.
  The framework emits this automatically when a component has `requires_ack=True`; you don't pass it
  to `callback` yourself.
- **`5`** — command defer; emitted automatically for acked commands.
- **`9`** — modal; use `ctx.modal_response()` instead.

Full table: [context.md](context.md).

---

## 4. Component / modal routing is by `custom_id` prefix before the first `-`

Router: `self.__cache.components.get(str(context.custom_id).split("-")[0], None)`
([server.py:299](src/disunity/server.py:299), and the same for modal submit at
[server.py:358](src/disunity/server.py:358)).

Rules:
- The `@Package.component("NAME")` registers under `NAME`.
- The `custom_id` you assign to the actual button/select/modal must be `f"{NAME}-{anything}"` (or
  exactly `NAME` with no dash). Everything after the first `-` is your free-form per-instance tag
  (interaction id, target user id, page number, etc.) and is readable as `ctx.custom_id`.
- **The component NAME must not contain `-`.** If it does, routing splits at the wrong place and the
  handler won't be found (`ComponentNotFound`).
- Modals route the same way: a `Modal(custom_id="apply-form")` is handled by `@Package.component("apply")`.

---

## 5. Component `timeout` only protects **non-acked** components

`Component.__call__` ([identifiers.py:120](src/disunity/identifiers.py:120)):
- `timeout` is the number of seconds after the **source message's** `timestamp` during which the
  component is valid. `timeout=0.0` (default) = no timeout.
- If expired and the component is **not** acked, the handler is skipped and an ephemeral "This
  component has timed out." message (type 4) is returned.
- If the component **is** acked (`requires_ack=True`), the timeout check is bypassed entirely
  (`if not self.ack:` guards the return) — the handler runs no matter how old the message is.
- The timestamp is read from `ctx.raw["message"]["timestamp"]`; this only exists for message
  components, not modal submits.

---

## 6. Interaction token & timing lifetimes

- **3 seconds:** the initial response (ack/defer or `callback`) must reach Discord within ~3s.
- **~15 minutes:** the interaction token is valid for follow-ups/edits for ~15 minutes after the
  interaction. `ctx.followup` and `Message.edit_as_webhook` use this token; after expiry they fail
  (`Message.edit_as_webhook` translates Discord codes `10015`/`50027` into `ExpiredInteractionError`,
  [message.py:75](src/disunity/models/message.py:75)).
- `ctx.followup` raises `InvalidMethodUse` if called before the interaction is acked
  ([context.py:94](src/disunity/models/context.py:94)).

---

## 7. Async / ordering assumptions

- Acked handlers run via `asyncio.create_task(...)`; the HTTP response (the defer) returns
  immediately and **concurrently**. Don't assume the handler finished before the response is sent —
  it hasn't.
- `make_https_request` opens a **new** `aiohttp.ClientSession` per call
  ([server.py:159](src/disunity/server.py:159)). There's no connection pooling across calls.
- The server uses module-level globals for credentials/config via `self.config`; client-credential
  tokens are cached until half their `expires_in` elapses ([server.py:96](src/disunity/server.py:96)).
- Handlers are plain methods on a **single shared package instance** (`register_package` stores one
  instance). Any mutable instance state is shared across all concurrent interactions — guard it if
  you mutate it.

---

## 8. `global_check` semantics are strict-`True`

`if check != True:` ([server.py:270](src/disunity/server.py:270)). Only the literal `True` proceeds.
- Return `True` → run the handler.
- Return a `dict` with a `"type"` key → that dict becomes the interaction response; handler skipped.
- Return anything else (including truthy non-`True` values like `1` or a non-`"type"` dict) → server
  responds with bare `PONG` and skips the handler. A `PONG` to a command/component interaction is not
  a valid user-visible response, so the interaction silently does nothing. Always return real `True`
  or a `{"type": ...}` dict.

`global_after_interaction` is **not** called on the autocomplete path, and for acked handlers it is
awaited inside the background task (not fire-and-forget). See [server.md](server.md).

---

## 9. Decorated methods must be `async`, and discovery skips dunders

- All four decorators raise `TypeError` at import time if the wrapped function isn't a coroutine
  function ([package.py:38](src/disunity/package.py:38) etc.). `staticmethod`-wrapped coroutines are
  supported (unwrapped automatically).
- `unpack()` only discovers coroutine members whose names don't start **or** end with `__`
  ([package.py:184](src/disunity/package.py:184)). Don't name a handler `__call__`-style.
- Non-decorated coroutine methods (no `__data__`) are silently skipped — a typo in the decorator that
  drops the marker attributes means the handler just never registers (no error).

---

## 10. Misc source quirks (don't rely on these)

- `UserTextInput` emits only one of `value` / `placeholder` / `min_length` (if/elif chain) — see
  [components.md](components.md).
- `Button` always includes a `custom_id` key even for `LINK` buttons; pass `custom_id=None` for links.
- Only CHAT_INPUT slash commands are clearly supported; USER/MESSAGE context-menu commands are
  **UNVERIFIED** (commands are all stored/looked up under type key `"2"`). See [commands.md](commands.md).
- `utils.__version__` (`0.1.3`) ≠ package version (`0.1.17`).
