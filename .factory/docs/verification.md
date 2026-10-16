# Project Verification

`factory verify` turns repository evidence into an explicit, reviewable validation plan. It does not execute free-text commands entered during project intake and does not use AI to invent commands.

## Flow

```text
factory verify plan -C <project-dir> --profile quick
factory verify run -C <project-dir> --profile full
factory verify validate -C <project-dir>
```

`plan` is read-only. It discovers commands, displays exact arguments and working directories, and hashes the relevant manifests and source inputs. `run` rejects a changed input hash, then executes every reviewed check. An interactive terminal shows a Markdown review before execution. `validate` inspects the latest recorded result and reports later source drift.

Use repeated `--check` flags to narrow a plan to `check`, `test`, `lint`, `typecheck`, or `build`. The `quick` profile excludes builds; `full` includes them.

## Discovery

| Evidence | Checks |
| --- | --- |
| Node `package.json` scripts | `test`, `lint`, `typecheck`/`type-check`, `build` |
| Django `manage.py` with a project-local Python environment | `check`, `test` |
| Python test/lint/typecheck dependencies | pytest or unittest, Ruff, mypy, or Pyright |
| Flutter `pubspec.yaml` | `flutter analyze`, `flutter test` |
| Maven `pom.xml` | test and package build |
| .NET project files | test and build |
| Go module | vet, test, and build |

Node package-manager selection uses manifest declarations, lockfiles, or managed scaffold provenance. Python checks require the project-local `.venv`; Factory does not fall back to the system interpreter.

## Evidence And Safety

The latest record is `.factory-state/verification/latest.yaml`; timestamped run records are kept below `.factory-state/verification/runs/`. Evidence includes the plan hash, check IDs, exact arguments, duration, exit code, status, and an output hash. Raw command output may contain secrets or excessive logs, so it is displayed for diagnosis but never stored in Factory state.

Verification commands are expected to be non-mutating, but build and test tools may create ordinary caches or build outputs. Known generated directories are excluded from source hashing. `factory validate` includes verification only after verification state exists; `factory verify validate` requires that state explicitly.
