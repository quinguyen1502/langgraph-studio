# Error codes

Every error has a stable `code`. The catalogue below is included from
[`docs/api-errors.md`](https://github.com/quinguyen1502/langgraph-studio/blob/develop/docs/api-errors.md),
which is checked against `backend/app/core/errors.py` and both UI locales by
`backend/tests/test_api_envelope.py`, so it is always complete.

The response shape is described in [HTTP API](api.md#envelope).

--8<-- "docs/api-errors.md:catalog"
