# Contributing to ReelKit

Contributions should make short-video creation clearer, more expressive, or easier to run on different computers. Keep the offline renderer small and treat network services as optional adapters.

## Local development

Use Python 3.9 or newer in a virtual environment. From the repository root:

```sh
python -m venv .venv
```

On macOS and Linux, activate with `source .venv/bin/activate`. In Windows PowerShell, use `.venv\Scripts\Activate.ps1`; if activation is restricted, invoke `.venv\Scripts\python.exe` directly instead. Some Unix installations name Python `python3`; Windows also provides the `py` launcher.

```sh
python -m pip install -e ".[dev]"
reelkit doctor
python -m pytest
```

Install the speech extra only when working on synthesis:

```sh
python -m pip install -e ".[voice,dev]"
```

See the README for the supported runtime and initial render commands. Keep shell-specific activation out of library code; use `pathlib` for filesystem operations and argument lists for subprocesses.

## Useful changes and checks

Keep changes focused and describe the observable behavior they improve. Add tests for meaningful invariants such as asset containment, scene timing, caption grouping, and valid rendered media. Do not add tests that merely repeat implementation details or assert documentation wording.

Run the tests relevant to your change. For renderer changes, render the offline example and inspect representative frames. Check both left-to-right and right-to-left captions when changing text layout. Changes to audio mixing or synthesis should include a short audible check when the environment supports playback. Document limitations instead of claiming an unchecked result.

If changing the project format, update [docs/schema.md](docs/schema.md), the validator, affected examples, and tests together. Preserve version 1 compatibility or clearly propose a versioned migration.

## Pull requests

Explain the problem, what users will observe after the change, and how it was verified. Include screenshots or a small preview only when they help review a visual change. Avoid committing rendered videos, temporary narration, caches, virtual environments, or large test outputs.

Before sharing a branch, inspect staged files for credentials, personal data, absolute user paths, and private source material. New sample assets must be original or licensed for redistribution, with their source and license recorded. Do not copy a private project into test fixtures.
