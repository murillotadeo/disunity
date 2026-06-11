# Components — buttons, selects, action rows, modals

All component model classes live in
[src/disunity/models/components.py](src/disunity/models/components.py) and are re-exported from
`disunity.models`. Each has a `to_dict()` that produces the Discord JSON. You put components into an
`ActionRow`, then pass rows to `ctx.callback(components=...)` / `ctx.followup(components=...)`.

Handling component clicks is done with `@Package.component("name", ...)` (see
[packages.md](packages.md)); routing is by `custom_id` prefix (see "custom_id rules" there).

---

## `ButtonStyles`
**Source:** [src/disunity/models/components.py:4](src/disunity/models/components.py:4)

Integer constants: `PRIMARY=1`, `SECONDARY=2`, `SUCCESS=3`, `DANGER=4`, `LINK=5`.

## `TextInputStyles`
**Source:** [src/disunity/models/components.py:12](src/disunity/models/components.py:12)

`SHORT=1`, `PARAGRAPH=2`.

---

## `ActionRow(components)`
**Source:** [src/disunity/models/components.py:17](src/disunity/models/components.py:17)

| Param | Type | Meaning |
|-------|------|---------|
| `components` | `list[Button \| SelectMenu \| UserTextInput]` | Children. Discord limits: ≤5 buttons per row, or exactly 1 select menu per row. `UserTextInput` only valid inside a `Modal`. |

Eagerly calls `to_dict()` on each child at construction. `to_dict()` → `{"type": 1, "components": [...]}`.
No validation of the 5-button / 1-select limits is performed by disunity.

```python
from disunity.models import ActionRow, Button, ButtonStyles
row = ActionRow([
    Button("approve-42", "Approve", ButtonStyles.SUCCESS),
    Button("deny-42", "Deny", ButtonStyles.DANGER),
])
```

---

## `Button(custom_id, label, style=ButtonStyles.PRIMARY, emoji=None, url=None, disabled=False)`
**Source:** [src/disunity/models/components.py:38](src/disunity/models/components.py:38)

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `custom_id` | `str \| None` | — (positional) | Routing id. For `LINK` buttons set to `None`. Convention: `f"{component_name}-{tag}"` — the substring before the first `-` selects the `@Package.component` handler. |
| `label` | `str` | — (positional) | Button text. |
| `style` | `int` | `ButtonStyles.PRIMARY` (1) | One of `ButtonStyles`. |
| `emoji` | `dict \| None` | `None` | Partial emoji object, e.g. `{"name": "🔥"}` or `{"id": "123", "name": "x"}`. Only added if a non-empty `dict`. |
| `url` | `str \| None` | `None` | Only used when `style == LINK`. Added only if `style == LINK` **and** `url is not None`. |
| `disabled` | `bool` | `False` | Greys out the button. |

`to_dict()` → `{"type": 2, "custom_id", "label", "style", "disabled"[, "emoji"][, "url"]}`.

> ⚠️ A `LINK` button still includes the passed `custom_id` key in the dict (the constructor always
> sets `custom_id`). Discord forbids `custom_id` on link buttons — pass `custom_id=None` for link
> buttons to send `"custom_id": null`. **UNVERIFIED** whether Discord rejects `null` here; safest is
> to only use link buttons with `custom_id=None` and a valid `url`.

```python
Button("vote-1", "Vote", ButtonStyles.PRIMARY)
Button(None, "Docs", ButtonStyles.LINK, url="https://example.com")
```

---

## `SelectMenuOption(label, value, description="", emoji=None)`
**Source:** [src/disunity/models/components.py:84](src/disunity/models/components.py:84)

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `label` | `str` | — | Display text. |
| `value` | `str \| int` | — | Value returned in `ctx.values` when chosen. |
| `description` | `str` | `""` | Sub-text. |
| `emoji` | `dict \| None` | `None` | Partial emoji; added only if non-empty dict. |

`to_dict()` → `{"label", "value", "description"[, "emoji"]}`.

### `MenuOption(...)` — alias
**Source:** [src/disunity/models/components.py:116](src/disunity/models/components.py:116)
Subclass of `SelectMenuOption` (identical fields; `emoji` defaults to `{}`). Use either.

---

## `SelectMenu(custom_id, options, placeholder="", disabled=False)`
**Source:** [src/disunity/models/components.py:125](src/disunity/models/components.py:125)

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `custom_id` | `str` | — | Routing id (same prefix rule as buttons). |
| `options` | `list[SelectMenuOption \| MenuOption]` | — | Choices. **Raises `ValueError`** if more than 25. |
| `placeholder` | `str` | `""` | Placeholder text. |
| `disabled` | `bool` | `False` | Disable the menu. |

`to_dict()` → `{"type": 3, "custom_id", "options", "placeholder", "disabled"}`.

> This is a **string** select (type 3) only. No native user/role/channel/mentionable select
> (types 5–8) wrapper is provided. The chosen option `value`s arrive in `ctx.values`.

```python
from disunity.models import SelectMenu, SelectMenuOption, ActionRow
menu = SelectMenu("pick-color", [
    SelectMenuOption("Blue", "blue"),
    SelectMenuOption("Red", "red", description="warm"),
], placeholder="Choose a color")
row = ActionRow([menu])
```

---

## `UserTextInput(custom_id, label, style=SHORT, min_length=None, max_length=4000, required=False, value=None, placeholder=None)`
**Source:** [src/disunity/models/components.py:163](src/disunity/models/components.py:163)

A modal text field (component type 4). Only valid inside a `Modal`.

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `custom_id` | `str` | — | Field id; appears as `custom_id` in `ctx.modal_values`. |
| `label` | `str` | — | Field label. |
| `style` | `int` | `TextInputStyles.SHORT` (1) | `1`=short, `2`=paragraph. |
| `min_length` | `int \| None` | `None` | Minimum length. **See quirk below.** |
| `max_length` | `int` | `4000` | Maximum length (always included in the dict). |
| `required` | `bool` | `False` | Whether the field is required. |
| `value` | `str \| None` | `None` | Pre-filled value. |
| `placeholder` | `str \| None` | `None` | Placeholder. |

`to_dict()` base → `{"type": 4, "custom_id", "style", "label", "required", "max_length"}`.

> ⚠️ **Quirk — only one of `value` / `placeholder` / `min_length` is emitted.** The constructor uses
> an `if/elif/elif` chain ([src/disunity/models/components.py:206](src/disunity/models/components.py:206)):
> if `value` is set, `placeholder` and `min_length` are dropped; if `value` is `None` but
> `placeholder` is set, `min_length` is dropped. To send `min_length`, leave both `value` and
> `placeholder` as `None`. You generally cannot combine a placeholder with a min length here.

---

## `Modal(title, custom_id, components)`
**Source:** [src/disunity/models/components.py:217](src/disunity/models/components.py:217)

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `title` | `str` | — | Modal title. |
| `custom_id` | `str` | — | Modal id. On submit, routed to the `@Package.component` whose name matches `custom_id.split("-")[0]`. |
| `components` | `list[UserTextInput]` | — | Inputs. **Raises `ValueError` if empty.** Each input is automatically wrapped in its **own** `ActionRow` (one input per row, as Discord requires). |

`to_dict()` → `{"title", "custom_id", "components": [ActionRow([input]).to_dict(), ...]}`.

Open a modal with `return await ctx.modal_response(modal)` (see [context.md](context.md)). Read
submitted values from `ctx.modal_values` in the routed component handler.

```python
from disunity.models import Modal, UserTextInput, TextInputStyles

modal = Modal("Apply", "apply-form", [
    UserTextInput("name", "Name", required=True),
    UserTextInput("why", "Why you?", style=TextInputStyles.PARAGRAPH),
])
# in the command handler:
return await ctx.modal_response(modal)

# separate handler for the submit (name "apply" matches "apply-form".split("-")[0]):
@package.Package.component("apply")
async def on_apply(self, ctx):
    answers = {c["custom_id"]: c["value"] for c in ctx.modal_values}
    return await ctx.callback(f"Thanks {answers['name']}", ephemeral=True)
```

> Note: the modal `custom_id` prefix (before the first `-`) must equal the component handler name.
> Here `"apply-form"` → handler `"apply"`.
