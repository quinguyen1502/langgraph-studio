# State and references

## The state schema

Declare the state under **State schema** in the left panel. Each field has a
name and a type:

| Type | JSON value | Reducers |
| --- | --- | --- |
| `string` | text | `replace` |
| `number` | float | `replace`, `add` |
| `integer` | whole number | `replace`, `add` |
| `boolean` | `true` / `false` | `replace` |
| `object` | JSON object | `replace`, `merge` |
| `list` | JSON array | `replace`, `append` |

The run input is the initial state.

## Reducers

A reducer decides how a write combines with the value already in the field.
`replace` (the default) overwrites it. The others matter when several nodes
write in the same superstep, or when a loop collects results:

| Reducer | Effect |
| --- | --- |
| `append` | Adds the new item (or items) to the list. |
| `merge` | Merges the new keys into the object. |
| `add` | Adds the number. |

Parallel branches that write the same field without a reducer fail
validation, because LangGraph cannot know which write wins.

## References

Prompts, Human questions, HTTP Tool URLs and bodies, Retriever queries,
Send email fields and MCP arguments are templates. A reference is
`{{state.field}}`, with an optional path and filters:

```text
{{state.order.items.0.sku}}        walk objects by key and lists by index
{{state.name | trim | upper}}      filters apply left to right
{{state.tags | join(", ")}}        filters can take one argument
{{state.note | default("none")}}   a fallback for an empty value
```

A missing step in a path gives an empty value.

| Filter | Result |
| --- | --- |
| `upper`, `lower`, `trim` | Text case and whitespace |
| `json` | The value as JSON |
| `length` | Length of a list, object or text |
| `first`, `last` | First or last item of a list |
| `default("text")` | `text` when the value is empty |
| `join(", ")` | List items joined by the separator |
| `truncate(80)` | Text cut to 80 characters |

An MCP argument (and a Decision `text`) that is exactly one reference keeps
the value's type, so `{{state.items | length}}` passes a number.

## In the editor

References show as tags. Type `{{` for state fields, and `|` inside a
reference for filters. Double-click a tag to edit it as text. A field missing
from the state, or an unknown filter, is red, and Save lists it. A run refuses
an invalid reference with `TEMPLATE_REF_INVALID`.
