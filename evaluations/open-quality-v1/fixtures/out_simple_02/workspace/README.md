# Typed response DTO fixture

Add one optional `nickname` field to `UserResponse`.

Frozen semantics:

- The Python type is `str | None` and the default is `None`.
- If the field is absent or `None`, `serialize_user` must return the exact same
  UTF-8 bytes as before.
- If present, `nickname` is serialized after `name`.
- `user_from_mapping` continues to ignore unknown input fields.
- Add the most relevant test to the existing test module.

Use only the standard library. Do not add files, dependencies, layers, process
documents, or unrelated API behavior. Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Agent count, network activity, and WCU are evaluated outside this repository;
they cannot be established by a self-authored file or test.
