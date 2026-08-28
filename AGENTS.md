# ~/bin

Personal scripts and small utilities. This directory is a git repository, tracked separately from the chezmoi-managed dotfiles.

## Working here
- Probe `<script> -h` (or `--help`) before reading source.
- Apply the `shell-script-style` and `cli-design` skills when creating or substantially editing user-facing scripts.
- **New scripts: start from `template.sh`.** It provides established boilerplate — signal traps, color output helpers, dry-run/verbosity flags, and `show_help` via `sed`. Copy it, rename it, and adjust the header.
- Scripts marked **DESTRUCTIVE** mutate the filesystem, packages, or remote state without prompting; review source before invoking.
- One logical change per commit. Recent history uses "Add X" / "Add X wrapper" subjects for new scripts; describe the actual change for modifications.
- Older scripts (most `bb-*`, `brew-*`, etc.) often don't intercept help flags. Newer scripts (model wrappers, build helpers, recent additions) standardize on `-h` or `-h/--help`.
- **Keep inventory current.** Adding, removing, or materially changing a script's behavior (help handling, destructiveness, purpose) means updating its inventory entry (or adding/removing one) in the same commit — don't let this file drift from what's on disk.

## Script Inventory

See the complete script inventory in [inventory](./docs/inventory.md). Avoid
loading the entire inventory into context unless necessary.

## Cautions
- **No `--help` long-option support** outside Python scripts and a small set of bash scripts (`git-setup`, `wait-for-nas-connectivity`). When in doubt, try `-h` first.
- **Several scripts run destructive operations without `-h` check or confirmation.** Flagged inline with **DESTRUCTIVE**. Examples: `brew-clean`, `brew-reinstall-casks`, `brew-wipe-cache`, `bb-clean`, `bb-kill`, `nix-clean`, `pacman-remove-orphans`, `clean-sstate`, `bgrm`, `kkill`, `cleaneject`, `ddimage-sd`, `resolvelinks`, `remove-empty-dirs`, `safari-webapp-cache-clean`. Read source before invoking unfamiliar ones.
- **uv-script convention.** Scripts with `#!/usr/bin/env -S uv run --script` and inline `# /// script` headers manage their own deps: `cached-retool`, `csvpyrow`, `devpod-list`, `dupes-select`, `ia-parallel-download`, `reader-tools`, `strip-emoji`, `yocto-releases`.
- **Vendored Perl `ack`.** ~168 KB: a full third-party tool, not user code.
- **Many bb-* and brew-* scripts are 1-3 lines.** Reading source for those is faster than probing `-h`. Use the index to identify them by `[type, none]` and a tiny purpose blurb.
