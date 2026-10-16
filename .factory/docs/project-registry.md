# Project Registry

One factory installation can manage many project repositories. The registry records the
projects you work with so they can be listed and opened by name.

## Location

The registry is a YAML file resolved in this order:

1. `$FACTORY_HOME/registry.yaml` when `FACTORY_HOME` is set.
2. `$XDG_CONFIG_HOME/factory/registry.yaml` when `XDG_CONFIG_HOME` is set.
3. `~/.factory/registry.yaml` otherwise.

Each entry stores the project `name`, absolute `path`, and the time it was added.

## Commands

```text
factory projects list
factory projects add [path] [--name NAME]
factory projects remove <name>
factory projects            # interactive picker (terminal only)
```

- `factory init` registers each new project automatically. Registration is best-effort:
  if it fails (for example a duplicate name), initialization still succeeds and prints a
  warning.
- `add` validates that the path is a factory project (it has `.factory-state/` and
  `.factory-state/factory.yaml`). Re-adding the same path is idempotent.
- A name may only map to one path. Use `--name` to register a second project that shares a
  directory name.
- `remove` unregisters by name; it never deletes project files.

## Opening A Project By Name

Commands that operate on a single project accept `--project <name>` as an alternative to
`-C <path>`; the name is resolved through the registry. This currently applies to
`factory board` and `factory dashboard`. Running `factory projects` with no subcommand in a
terminal lists the registered projects and opens the board for the one you select.
