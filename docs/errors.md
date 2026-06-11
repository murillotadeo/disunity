# Errors

Most exceptions live in [src/disunity/errors.py](src/disunity/errors.py). A few model-specific ones
live alongside the models. All are plain `Exception` subclasses (no shared base beyond `Exception`).

## `disunity.errors`

### `HTTPRequestError(status_code, error_message)`
**Source:** [src/disunity/errors.py:23](src/disunity/errors.py:23)
Raised by `DisunityServer.make_https_request` when a Discord API call returns a non-`2xx` status
(and `override_checks=False`). Message: `f"HTTP request returned with status {status_code}: {error_message}"`.
`error_message` is the parsed JSON error body. This is the error you'll most often catch around
`followup` / `Message.edit_*`.

### `InvalidMethodUse(reason)`
**Source:** [src/disunity/errors.py:1](src/disunity/errors.py:1)
Raised when an API is used incorrectly. Concretely:
- `ctx.followup(...)` before the interaction is acked ([context.py:95](src/disunity/models/context.py:95)).
- `ctx.check_user()` on a non-component interaction ([interaction.py:59](src/disunity/models/interaction.py:59)).
- Router: a command with subcommand-shaped options whose base wasn't registered via `@Package.sub`
  ([server.py:239](src/disunity/server.py:239), [server.py:250](src/disunity/server.py:250)).

### `CommandNotFound(command)`
**Source:** [src/disunity/errors.py:6](src/disunity/errors.py:6)
Router raised when an incoming command name (or subcommand) has no registered handler.

### `ComponentNotFound(component)`
**Source:** [src/disunity/errors.py:11](src/disunity/errors.py:11)
Router raised when a component/modal `custom_id` prefix matches no registered `@Package.component`.

### `AutocompleteNotFound(command_name)`
**Source:** [src/disunity/errors.py:16](src/disunity/errors.py:16)
Router raised when an autocomplete interaction's command has no registered `@Package.autocomplete`.

## Model-local exceptions

### `MissingTokenError(func_name)`
**Source:** [src/disunity/models/message.py:8](src/disunity/models/message.py:8)
Raised by `Message.edit_as_bot` / `Message.delete_as_bot` when the server has no `bot_token`.

### `ExpiredInteractionError()`
**Source:** [src/disunity/models/message.py:13](src/disunity/models/message.py:13)
Raised by `Message.edit_as_webhook` when Discord returns error code `10015` (unknown webhook) or
`50027` (invalid webhook token) — i.e. the interaction token expired.

### `EmptyEmbedError(message)`
**Source:** [src/disunity/embed.py:4](src/disunity/embed.py:4)
Raised by `Embed.add_field` when `name` or `value` is empty.

## How handler exceptions are routed

The wrapper objects (`Command`, `Component`, `SubCommand`, `Autocomplete` in
[identifiers.py](src/disunity/identifiers.py)) wrap your coroutine in `try/except Exception` and call
`context._app.error_handler(e)` on failure. The **default** `error_handler` re-raises
([server.py:67](src/disunity/server.py:67)), so by default an unhandled handler exception propagates.
Override `error_handler` in a `DisunityServer` subclass to log instead:

```python
class MyServer(disunity.DisunityServer):
    def error_handler(self, exc):
        logging.exception("handler failed", exc_info=exc)
        # swallow instead of raising
```

> Because acked handlers run inside `asyncio.create_task(...)` (background), exceptions there surface
> through `error_handler` but **not** to the HTTP response (the deferred response was already sent).
> A raising default `error_handler` in a background task becomes an unretrieved-task exception. For
> acked handlers, prefer a non-raising `error_handler`.
