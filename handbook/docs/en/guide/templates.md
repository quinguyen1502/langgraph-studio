# Workflow templates

**New workflow** opens the template gallery.

![Template gallery](../images/templates.png)

| Group | Contents |
| --- | --- |
| Blank workflow | Start and End only. |
| Built-in | **Chatbot**, **RAG Q&A**, **Approval flow**, **Router**. |
| Only me | Templates you saved. |
| Organisation | Templates shared with everyone. |

Each card has a preview of the graph. Creating from a template copies it into
a new workflow you own.

## Save a template

**⋯ → Save as template** copies the **last saved version** of the workflow
(save first to include unsaved edits). Choose a name, a description and who
sees it. Organisation scope needs `org.manage`.

Templates never carry credentials, knowledge bases, MCP servers, approval
channels, subgraph links, headers or API keys. Those fields are emptied, so
pick your own after creating.

## Export and import

**Export** on a card writes a `*.template.json` file:

```json
{"format": "superstep/template", "version": 1,
 "name": "…", "description": "…", "workflow": {"state": [], "nodes": [], "edges": []}}
```

**Import template** in the gallery reads one back. A template that contains a
Code node needs `code.write` to import or use.

Deleting a template asks you to type its name. Workflows created from it are
not affected.
