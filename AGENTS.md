# ~/bin

Personal scripts and small utilities. This directory is a git repository, tracked separately from the chezmoi-managed dotfiles.

## Working here
- Probe `<script> -h` (or `--help`) before reading source. The inventory below shows which scripts respond.
- Apply the `shell-script-style` skill when creating or substantially editing user-facing scripts.
- Scripts marked **DESTRUCTIVE** mutate the filesystem, packages, or remote state without prompting; review source before invoking.
- One logical change per commit. Recent history uses "Add X" / "Add X wrapper" subjects for new scripts; describe the actual change for modifications.
- Older scripts (most `bb-*`, `brew-*`, etc.) often don't intercept help flags. Newer scripts (model wrappers, build helpers, recent additions) standardize on `-h` or `-h/--help`.

## Inventory notation
`[type, help]` per script.

- **type**: `sh` (POSIX), `bash`, `python`, `perl`, `ruby`, `zsh`, `pwsh`, `cmd`
- **help**: `-h`, `--help`, `-h/--help`, `argparse` (Python argparse: `-h/--help` standard), `none` (no detected handling, reading source is acceptable), `passthru` (forwards args to another tool)
- `none` scripts are typically one-or-two liners; reading them is cheap.

## bitbake / yocto (`bb-*`, `bitbake-*`, `yocto-*`, `oe*`, `clean-sstate`)
- **bb-buildlist** [sh, none]: Run `bitbake -g`, print resulting `pn-buildlist`.
- **bb-clean** [sh, none]: Shorthand for `bitbake -c clean "$@"`. **DESTRUCTIVE**.
- **bb-fetch** [sh, none]: Shorthand for `bitbake -c fetch "$@"`.
- **bb-getvalue** [sh, none]: `bitbake-getvar --value` filtered to the raw value only.
- **bb-getvar** [sh, none]: Wrapper that execs `bitbake-getvars`.
- **bb-getvars** [sh, none]: Wrapper that execs `bitbake-getvars`.
- **bb-grapheasy** [sh, -h]: Render bitbake dependency graph via Graph::Easy with exclusion pattern.
- **bb-kill** [bash, none]: Remove bitbake lock/socket files and `kkill -f bitbake`. **DESTRUCTIVE**.
- **bb-layers** [sh, passthru]: Wrapper for `bitbake-layers`.
- **bb-newlayer** [sh, -h]: Create a new bitbake layer at LAYERPATH and add it.
- **bb-sh-cd-builddir** [sh, none]: Print `cd $(bb getvalue ... B)` snippet for sourcing.
- **bb-sh-cd-srcdir** [sh, none]: Print `cd $(bb getvalue ... S)` snippet for sourcing.
- **bb-sh-cd-workdir** [sh, none]: Print `cd $(bb getvalue ... WORKDIR)` snippet for sourcing.
- **bitbake-getvar** [python, argparse]: Query a single bitbake variable via tinfoil.
- **bitbake-getvars** [python, argparse]: Query multiple bitbake variables via tinfoil.
- **clean-sstate** [sh, none]: Delete sstate cache files older than 7 days. Accepts `-n` for dry run. **DESTRUCTIVE**.
- **oeclone** [bash, none]: Clone an OE/Yocto layer by querying the layer index and fzf-selecting.
- **sh-cd-workdir** [sh, none]: Verbose variant of bb-sh-cd-workdir with debug output.
- **yocto-buildtools-install** [bash, -h]: Download and install Yocto buildtools nativesdk.
- **yocto-releases** [python (uv), argparse]: Fetch and display Yocto release table from upstream wiki.

## homebrew (`brew-*`, `brewa*`, `brewu`, `brewv*`, `adminbrew`, `admindo`, `install-brew`)
- **adminbrew** [sh, none]: Run brew as the admin user via `admindo`.
- **admindo** [sh, none]: Run a command as `OSX_ADMIN_LOGNAME` via `surun`/`su`.
- **brew-cask-sizes** [sh, none]: `du -s` of every Caskroom entry, sorted descending.
- **brew-clean** [sh, none]: Wipe brew cache and run `brew cleanup -sv`. **DESTRUCTIVE**.
- **brew-clean-cask-pkgs** [sh, none]: Trash `.pkg` files left in Caskroom. **DESTRUCTIVE**.
- **brew-leaves-sizes** [sh, none]: `du -s` of leaf formulae, sorted descending.
- **brew-linked-keg-only** [sh, none]: List keg-only formulae that are currently linked.
- **brew-list-keg-only** [sh, none]: List installed keg-only formulae.
- **brew-reinstall-casks** [sh, none]: Uninstall and reinstall every cask. **DESTRUCTIVE**.
- **brew-search-casks-for-apps** [sh, none]: Look up every macOS app via mdfind in cask search.
- **brew-sizes** [sh, none]: `du -s` of every Cellar entry, sorted descending.
- **brew-unlinked-normal** [sh, none]: List installed non-keg-only formulae missing a linked keg.
- **brew-wipe-cache** [sh, none]: Trash everything in `brew --cache`. **DESTRUCTIVE**.
- **brewau** [sh, none]: Update brew, upgrade outdated (with HEAD), reinstall ignored deps. **DESTRUCTIVE**.
- **brewu** [sh, none]: `brew upgrade --fetch-HEAD && brew clean`. **DESTRUCTIVE**.
- **brewv** [sh, -h]: Manage isolated brew installations under `$HOMEBREWS_HOME` (analogous to virtualenvs).
- **brewv-update** [sh, -h]: Upgrade packages in one or all brewv environments.
- **install-brew** [sh, -h]: Install homebrew to a custom prefix, optionally split prefix/repo.

## chezmoi (`edot*`, `list-chezmoi-repos`)
- **edot** [bash, none]: Fuzzy-match chezmoi-managed files via fzf, edit with `chezmoi edit --watch --apply`.
- **edot.ps1** [pwsh, none]: Windows port of `edot` using PSFzf.
- **list-chezmoi-repos** [bash, none]: Search GitHub for top dotfiles+chezmoi repos by stars.

## git wrappers (`git-*`, `ghq-*`, `gitignore`, `find_forks`, `github-*`)
- **find_forks** [sh, none]: Run frost-nzcr4/find_forks against current repo via venv.
- **ghq-clone** [sh, none]: Clone via ghq cache, then re-point remote upstream.
- **ghq-fetch** [sh, none]: Fetch into ghq mirror in parallel for all remotes.
- **ghq-prune-duped-objects** [sh, none]: Hardlink duplicate objects across all ghq repos.
- **ghq-repo-path** [sh, none]: Resolve a URL to its ghq local path.
- **ghstar-to-pinboard** [sh, none]: Push GitHub stars to Pinboard via `pinboard-add`.
- **git-checkout-date** [sh, none]: Check out the last commit before a given DATE.
- **git-cherry-tree-all** [sh, -h]: Cherry-style listing across all branches.
- **git-clone-muos** [bash, none]: Clone all MustardOS repos via ghq + register with mr.
- **git-clone-org** [bash, none]: Clone all repos for a GitHub org via ghq + register with mr.
- **git-clone-retrodeck** [bash, none]: Clone all RetroDECK repos via ghq + register with mr.
- **git-clone-via** [bash, -h]: Clone through a local mirror, repointed to upstream.
- **git-config-topic-branch** [sh, -h]: Configure upstream/pushremote/simple for a topic branch.
- **git-cp** [sh, -h]: `cp` + `git add`, creating leading directories.
- **git-create-ref** [sh, none]: Create a new ref pointing at the null SHA.
- **git-credential-manager** [sh, passthru]: Locate and exec git-credential-manager.exe (WSL).
- **git-detached-clone** [sh, -h]: Create a "fake bare" clone with separate gitdir/worktree.
- **git-diff-filter** [sh, none]: Color-only diff filter (delta > diff-highlight > cat).
- **git-im** [sh, none]: Start a git-imerge with derived merge name.
- **git-list-root-commits** [sh, none]: List root commits across all refs.
- **git-ls-files-ever** [sh, none]: Every file ever touched in the rev range.
- **git-ls-objects** [sh, none]: Every object reachable, with type, in current repo.
- **git-ls-tree-ever** [sh, none]: Every tree entry across history.
- **git-make-shallow** [python, argparse]: Make repository shallow at given revisions.
- **git-merge-into** [sh, -h]: Non-fast-forward merge HEAD into a branch without checkout.
- **git-mergetool-wrapper** [sh, none]: git-mergetool wrapper avoiding double check_unchanged.
- **git-mstash** [sh, none]: Stash but exit 100 if nothing was stashed.
- **git-mvd** [sh, passthru]: Source mvd as `git mv` variant.
- **git-pager** [sh, none]: Diff pager: delta > diff-so-fancy > diff-highlight > bat > less.
- **git-parallel-fetch** [sh, none]: Fetch all remotes in parallel using ncpu jobs.
- **git-prune-merged** [bash, -h]: Delete branches fully merged into upstream.
- **git-prune-remote** [sh, -h]: Prune branches of named remote(s) relative to origin.
- **git-prune-tracking** [sh, -h]: Prune tracking branches only (local).
- **git-recent** [sh, none]: `for-each-ref` formatted by committerdate.
- **git-remote-urls** [sh, none]: List remote.*.url config values raw (no insteadOf).
- **git-resurrect** [sh, none]: Restore deleted files via git-attic.
- **git-resurrect-attic** [sh, none]: Restore all attic-deleted files matching prefix.
- **git-save** [sh, none]: `git add -u && git empty && git push origin --quiet`.
- **git-series-tbdiff** [python, argparse]: Apply tbdiff across git-series revisions.
- **git-setup** [sh, -h/--help]: Init repo with empty root commit and an initial commit.
- **git-subtrac-fetch-historical** [sh, none]: Fetch historical refs for git-subtrac submodules.
- **git-subtrac-fetch-upstream** [sh, none]: Fetch from `.gitmodules_upstream` URLs into submodules.
- **git-subtrac-init** [sh, none]: Convert .gitmodules to subtrac, redirect URLs.
- **git-tags** [sh, none]: Tag list with annotation subjects, sorted by taggerdate.
- **git-touch** [sh, none]: `touch && git add` for each path.
- **git-uncommit** [sh, -h]: Soft-reset to COMMIT preserving local modifications.
- **git-xbranch** [sh, -h]: Branch listing with relation to upstream/target.
- **git-xclean** [sh, passthru]: `git clean` honoring `.git/info/noclean` excludes.
- **github-fetch-forks** [bash, -h]: Add forks of repo as remotes.
- **github-forked-parents** [bash, none]: List parents of a user's forked repos.
- **github-list-forks** [bash, -h]: List forks of a repo (cached).
- **gitignore** [sh, none]: `curl gitignore.io/api/...` to fetch a template.

## AI agent CLI wrappers (`agp`, `cdxp`, `clp`)
- **agp** [bash, -h]: Wrapper for `agent -p --trust` with stdin/markdown formatting.
- **cdxp** [bash, -h]: Wrapper for `codex exec --full-auto` with stdin/markdown formatting.
- **clp** [bash, -h]: Wrapper for `claude -p` with stdin/markdown formatting.

## Jira (`jira-*`)
- **jira-to-notes** [bash, none]: Format jira-cli view output as markdown notes.
- **jira-to-project** [bash, -h]: Render Jira data into a project directory.
- **jira-view** [sh, none]: Tput-colored formatter for jira issue lists.

## env / venv managers (`pipv*`, `pipx-install`, `cpanmv*`, `gemv`, `npmv`, `luav`, `kpipsi*`, `nixrun`, `nixshell`)
- **cpanmv** [sh, none]: Install Perl modules into named env at `$CPANM_HOME/<env>`.
- **cpanmv-use** [sh, none]: Activate (eval) a cpanmv env in the current shell.
- **gemv** [sh, none]: Install Ruby gems into a named env at `$GEMENV_HOME`.
- **kpipsi** [sh, passthru]: pipsi wrapper accepting extra packages and shorter list option.
- **kpipsi-upgrade** [sh, none]: Upgrade every kpipsi-managed env.
- **luav** [bash, none]: Provision an isolated Lua sandbox via vert and luarocks.
- **npmv** [sh, none]: Install npm packages into named env at `$NPMENV_HOME`.
- **nix-clean** [sh, none]: Expire generations, GC, and optimize Nix store. **DESTRUCTIVE**.
- **nixrun** [bash, passthru]: `nix run nixpkgs#<pkg>` shortcut.
- **nixshell** [bash, none]: `nix-shell --run` wrapper that quotes args correctly.
- **pipv** [sh, none]: Install Python packages into named virtualenv (Python 2 fallback).
- **pipv-for-each** [sh, none]: Run a command in every virtualenv under `$WORKON_HOME`.
- **pipv-upgrade** [sh, none]: Upgrade every pipv env.
- **pipv3** [sh, none]: Like `pipv` but Python 3 only.
- **pipx-install** [sh, -h]: pipx install with implicit-package and force flags.

## CSV utilities (`csv*`)
- **csvaddrow** [python, argparse]: Append a CSV row with values defined by Python expressions.
- **csvcurrencyformat** [sh, none]: Format CSV columns as currency via csvpyrow.
- **csvdelcol** [python, none]: Delete named column(s) from CSV.
- **csvdelcolifsame** [python, none]: Delete column(s) only if every row has identical value.
- **csvgrep-any** [sh, passthru]: `csvgrep -ac -` with reminder defaults.
- **csvpycol** [python, argparse]: Set/filter a CSV column with Python expression.
- **csvpyrow** [python (uv), --help]: Filter CSV rows with a Python expression (kcompile-based).
- **csvsum** [sh, none]: Sum the first column of a CSV.

## comm/diff/dupe utilities (`comm-*`, `dirdiff-*`, `fdupes-*`, `fclones-*`, `jdupes-*`, `kdedup`, `dedup-foreach`, `same-file`, `fgroups-format`)
- **comm-cmd** [sh, none]: Run two commands and `comm` their stdout.
- **comm-files** [sh, -h]: Compare two directories' file listings via comm.
- **comm-to-difflike** [sh, none]: Convert comm output to diff-like ±/space prefixes.
- **comm-unsorted** [sh, none]: Run comm on unsorted inputs (sort first).
- **comm-words** [sh, -h]: Compare two strings as space-separated word sets.
- **dedup-foreach** [bash, none]: Run a command per group of duplicates from jdupes-oneline.
- **dirdiff-to-difflike** [sh, none]: Convert dirdiff output to diff-like prefixes.
- **dirdiff-to-gitstatus** [sh, none]: Convert dirdiff output to git-status-like prefixes.
- **fclones-decompress** [bash, -h]: fclones transformation that extracts archives.
- **fclones-to-fdupes** [sh, none]: Reformat fclones output as fdupes oneline.
- **fclones-unzip** [bash, none]: fclones transform: extract single-file zips.
- **fdupes-select** [python (uv), --help]: Filter dupe blocks (keep/remove/first/existing).
- **fdupes-xargs** [bash, none]: Run a command on each dupe in jdupes-oneline output.
- **fgroups-format** [sh, none]: Reformat findgroups output as plain paths.
- **jdupes-multiline** [python, none]: Convert jdupes oneline output to multi-line blocks.
- **jdupes-oneline** [python, none]: Convert jdupes blocks to one tab-separated line each.
- **jdupes-remove-missing** [python, none]: Drop missing files from multi-line dupe output.
- **jdupes-remove-nondupes** [python, none]: Drop dupe groups with only one entry.
- **kdedup** [sh, -h]: Group stdin paths by stdout of an identifier command.
- **same-file** [bash, none]: Exit 0 iff all paths share inode+device.

## fd / fzf / vim helpers (`fd*`, `fde`, `fdv`, `fv`, `gv`, `gvf`, `vim*`, `editin`)
- **e** [sh, none]: Edit via `$VISUAL`/`$EDITOR`, swapping sync GUIs to async.
- **editin** [sh, none]: Edit files listed on stdin via `$VISUAL`.
- **fde** [bash, none]: `fd -p -t f "$@" | editin`.
- **fdftree** [sh, none]: `fdtree -t f` shorthand.
- **fdfv** [sh, none]: `fdv ""` shorthand.
- **fdll** [bash, none]: `fd ... -X eza -lgd`.
- **fdlr** [bash, none]: `fd ... -X eza -lgd -s modified`.
- **fdtree** [bash, none]: `fd | as-tree` with optional pager.
- **fdv** [bash, none]: `fd -p -t f "$@" | vimin`.
- **fv** [bash, none]: Open recent fasd files in vim via fzf.
- **g** [sh, -h]: Smart recursive grep (batgrep > rg > pt > ag > ack > grep -r).
- **gv** [sh, none]: `g -V "$@" | vimerrors`.
- **gvf** [bash, none]: Interactive file-search edit: g + fzf + vimerrors.
- **vimerrors** [bash, none]: Read stdin as quickfix errors and edit first match.
- **vimin** [sh, none]: Edit files listed on stdin via vim.
- **vimsession** [sh, none]: Open `Session.vim` (walking up from CWD).

## tmux / dvtm (`tmux-*`, `tmx`, `att*`, `dvtm-*`, `peek`)
- **att** [sh, -h]: Attach abduco/dvtm session, importing env vars.
- **att-env** [sh, none]: `cat $ATT_ENV` (helper for att session env reattach).
- **dvtm-editor-copy** [sh, none]: Run dvtm-editor and copy result via pbcopy.
- **dvtm-kergoth-status** [sh, none]: Per-id dvtm status fifo loop.
- **dvtm-print-status** [bash, -h]: Format dvtm status string from {key} placeholders.
- **peek** [sh, none]: Open `$EDITOR` in a tmux split-window pane (33% size).
- **tmux-kill-session-group** [sh, none]: Kill all sessions in a tmux session_group.
- **tmux-link** [sh, none]: Spawn unique session linked to a base, kill on detach.
- **tmux-ls-group-sessions** [sh, none]: List sessions in a session_group.
- **tmux-ls-groups** [sh, none]: List unique tmux session_groups.
- **tmux-run-cmds** [sh, -h]: Run each arg in a separate tmux pane.
- **tmux-select-each** [sh, none]: Visit every window to clear activity flags.
- **tmux-toggle-float** [sh, none]: Toggle a tmux floating window via the float plugin.
- **tmx** [sh, -h]: Create/list/kill tmux session groups.

## macOS-only (`osx-*`, `darkmode`, `cleaneject`, `mkalias`, `mdfind-all`, `cd-rip`, `cdr2iso`, `cue-rip`, `bin2iso`, `bmaptool-sd`, `ddimage-sd`, `download-ted-talk`, `duti-*`, `firefox-*`, `get-webloc-url`, `icns-to-png`, `list-mac-apps`, `metadate`, `new-webloc`, `recreate-iso`, `safari-webapp-cache-clean`, `setfiledate`, `creationdate`)
- **bmaptool-sd** [sh, none]: Run bmaptool against macOS internal SD card reader.
- **bin2iso** [sh, none]: Convert .bin/.cue or .toc to ISO via bchunk.
- **cd-rip** [sh, -h]: Rip a CD using diskutil-detected device.
- **cdr2iso** [sh, none]: Convert .cdr to .iso via hdiutil.
- **cleaneject** [bash, none]: Clean macOS metadata and unmount a volume. **DESTRUCTIVE**.
- **creationdate** [python, argparse]: Set mtime from creation date for matching files.
- **cue-rip** [sh, -h]: Rip CD via cdrdao to bin/cue, with diskutil unmount.
- **darkmode** [sh, none]: Toggle macOS dark mode via osascript.
- **ddimage-sd** [sh, none]: `dd` an image against macOS internal SD card. **DESTRUCTIVE**.
- **download-ted-talk** [sh, none]: Scrape TED video URL and download mp4.
- **duti-all** [sh, -n]: Set duti defaults for every UTI in app's Info.plist.
- **duti-switch** [bash, -h]: Reassign UTIs from one app to another via duti.
- **firefox-addons** [sh, none]: Tab-separated list of addons in default Firefox profile.
- **firefox-addons-md** [sh, none]: Markdown rendering of firefox addon list.
- **firefox-get-ini-profiledir** [python, none]: Print path of default Firefox profile from profiles.ini.
- **get-webloc-url** [sh, none]: Print URL stored in `.webloc` files.
- **icns-to-png** [sh, none]: Convert .icns to .png via sips.
- **list-mac-apps** [bash, -h]: List macOS apps in standard locations with filters.
- **mdfind-all** [sh, none]: `mdfind ... kMDItemDisplayName == *` (force show all).
- **metadate** [bash, -h]: Set file dates from PDF/MSI/PE/exiftool/etc. metadata.
- **mkalias** [sh, none]: Create Finder aliases (macOS) via osascript.
- **new-webloc** [sh, -h]: Create a `.webloc` from URL (filename autoderived from page title).
- **osx-lib-paths-to-relative** [bash, none]: Rewrite dylib install_names to `@loader_path` relatives.
- **osx-list-app-categories** [sh, none]: List app bundles by LSApplicationCategoryType.
- **osx-list-app-store-apps** [sh, none]: `mdfind kMDItemAppStoreHasReceipt=1`.
- **osx-print-rpaths** [sh, none]: Print LC_RPATH entries from Mach-O via otool.
- **osx-rebuild-lsdb** [sh, none]: `lsregister -kill -r` (rebuild Launch Services database).
- **osx-reset-launchpad** [sh, none]: Reset Launchpad layout and restart Dock.
- **recreate-iso** [python, argparse]: Recreate ISO from extracted contents preserving metadata.
- **safari-webapp-cache-clean** [bash, -h]: Clean Safari web app caches. **DESTRUCTIVE**.
- **setfiledate** [bash, -h]: Set file dates from a unix timestamp argument.

## Linux/Debian/Arch/FreeBSD pkg utilities (`pacman-*`, `dpkg-sizes`, `pkg-sizes`, `ipk*`)
- **dpkg-sizes** [sh, none]: Top 25 largest installed dpkg packages.
- **ipkcontents** [sh, none]: List contents of an `.ipk` file.
- **ipkinfo** [sh, none]: Print control metadata of an `.ipk` file.
- **ipkunpack** [sh, none]: Extract `.ipk` to `<basename>/` with CONTROL/ subdir.
- **pacman-disowned** [sh, none]: Files on disk not owned by any pacman package.
- **pacman-orphans** [sh, none]: `pacman -Qtdq`.
- **pacman-remove-orphans** [sh, none]: `pacman -Rs $(pacman -Qtdq)`. **DESTRUCTIVE**.
- **pacman-sizes** [sh, none]: Pacman packages sorted by installed size.
- **pkg-sizes** [sh, none]: FreeBSD `pkg info -as` top 20 by size.

## SteamOS / handheld / retro (`build-allium`, `build-onion`, `decky-linux`, `flips-linux`, `install-decky-plugin`, `scrappy-community-convert`)
- **build-allium** [bash, none]: Build Allium for handheld via Docker (auto-starts colima on macOS).
- **build-onion** [bash, -h]: Build OnionUI for Miyoo Mini Flip via Docker.
- **decky-linux** [bash, none]: Decky Loader install/control script (Linux).
- **flips-linux** [bash, none]: flips ROM patcher wrapper for Linux.
- **install-decky-plugin** [bash, -h]: Install Decky Loader plugin from a tarball/URL.
- **scrappy-community-convert** [bash, none]: Convert Scrappy templates to muxzip format.

## DevPod / containers (`devpod-*`, `cached-retool`, `distrobox-create-chimera`)
- **cached-retool** [python (uv), --help]: Caching wrapper for retool that hashes inputs.
- **devpod-list** [python (uv), argparse]: List DevPod workspaces with rich-formatted tables.
- **devpod-stop** [bash, -h]: Parallel-stop DevPod workspaces with escalating fallback.
- **distrobox-create-chimera** [bash, none]: Create a chimera distrobox with mount/doas pre-init.

## Path / filesystem helpers (`abs_readlink`, `abspath`, `normpath`, `relpath`, `path_join`, `dead-symlinks`, `dirinfo`, `find-newest`, `find-oldest`, `lstree`, `newest`, `oldest`, `remove-empty-dirs`, `resolve-alias`, `resolvelink`, `resolvelinks`, `datefind`)
- **abs_readlink** [sh, none]: Print absolute path of symlink target(s).
- **abspath** [sh, -h]: Print absolute version of each PATH (relative-to override).
- **datefind** [bash, -h]: List files (find arguments) annotated with dates.
- **dead-symlinks** [sh, -h]: Recursively find broken symlinks.
- **dirinfo** [bash, -h]: Print summary info for a directory.
- **find-newest** [bash, none]: Walk find tree printing newest file by mtime.
- **find-oldest** [bash, none]: Walk find tree printing oldest file by mtime.
- **lstree** [sh, none]: Indented tree-like listing without box-drawing characters.
- **newest** [bash, none]: Newest file via `datefind -r | head -n1`.
- **normpath** [sh, none]: Print canonical form of a path (no symlinks resolved).
- **oldest** [bash, none]: Oldest file via `datefind | head -n1`.
- **path_join** [python, none]: `os.path.join(*sys.argv[1:])`.
- **relpath** [python, none]: `os.path.relpath(path, start)`.
- **remove-empty-dirs** [bash, none]: Remove empty dirs and stray .DS_Store files. **DESTRUCTIVE**.
- **resolve-alias** [sh, -h]: Resolve macOS Finder aliases to their target.
- **resolvelink** [sh, -h]: Replace a symlink with copy of its target.
- **resolvelinks** [sh, none]: Recursively resolve every symlink in a tree. **DESTRUCTIVE**.

## rsync / sync / library (`chunked-rsync`, `library-sync`, `libsync`, `rsync-images`, `rsync-reflink`)
- **chunked-rsync** [bash, none]: Run rsync in alphabetical-prefix chunks for huge trees.
- **library-sync** [bash, -h]: Sync game library to device using config-driven libsync.
- **libsync** [bash, -h]: rsync wrapper with archive extraction at destination.
- **rsync-images** [bash, -h]: Wait for build images and rsync them to a destination.
- **rsync-reflink** [bash, -h]: Reflink-copy local rsync transfers for speed.

## Process / wait helpers (`kkill`, `psgrep`, `ppsgrep`, `wait-for-*`, `detach`, `time-stats`, `test-sequence-time`, `rusage-readable`)
- **detach** [sh, none]: `nohup` background with quick exit-code on early failure.
- **kkill** [sh, none]: Kill processes matching pattern with escalating signals/delays. **DESTRUCTIVE**.
- **ppsgrep** [sh, none]: `ps` showing pgrep-matching processes with sids.
- **psgrep** [sh, none]: `ps fu -p <matching-pids>` (Linux/macOS).
- **rusage-readable** [python, none]: Wrap `rusage` to make units human-readable.
- **test-sequence-time** [zsh, none]: Compare runtime of a command against previous saved value.
- **time-stats** [sh, none]: Run command N times, summarize via `stats --trim-outliers`.
- **wait-for-build** [sh, -h]: Block until a Yocto build directory finishes.
- **wait-for-images** [sh, -h]: Block until image build artifacts of a type appear.
- **wait-for-nas-connectivity** [bash, -h/--help]: Wait for NAS connectivity (Tailscale-aware).
- **wait-for-process** [sh, -h]: Wait for a process to exit (and optionally to start).

## Clipboard / WSL / Windows interop (`pbcopy`, `pbpaste`, `mklink`, `wslpath`, `wsl-nativefier`, `wsl-notify`, `codewait*`)
- **codewait** [sh, passthru]: `code -w "$@"` shorthand.
- **codewait.cmd** [cmd, none]: Windows variant: `code --new-window --wait %*`.
- **mklink** [sh, none]: `cmd.exe /c mklink` with WSL path translation.
- **pbcopy** [sh, none]: Cross-platform copy (reattach-to-user-namespace, win32yank, xsel, etc.).
- **pbpaste** [sh, none]: Cross-platform paste counterpart.
- **wsl-nativefier** [sh, none]: Run nativefier in Docker from within WSL with Windows paths.
- **wsl-notify** [sh, none]: Send a Windows BurntToast notification from WSL.
- **wslpath** [sh, none]: Print WSL `/bin/wslpath` usage and forward args.

## Text / line helpers (`first-to-last`, `group-by-column`, `nlxargs`, `printargs`, `printcmd`, `quote-args`, `select-random`, `sponge`, `startswith`, `strip-color-codes`, `strip-emoji`, `sum`, `uniq-seen`, `uniq-seen-last`, `xargs-paste`, `glob-to-regex`, `urljoin`, `extract-md-links`, `pup-links`, `grab-links`)
- **extract-md-links** [sh, -h]: Extract links from markdown via cmark + pup.
- **first-to-last** [bash, none]: Move arg1 to end (xargs convenience).
- **glob-to-regex** [python, argparse]: Translate glob patterns to regex.
- **grab-links** [sh, -h]: Pull links from a URL via http + pup with options.
- **group-by-column** [sh, none]: Insert blank lines between groups of sorted column input.
- **nlxargs** [sh, passthru]: `tr '\n' '\0' | xargs -0 "$@"` shorthand.
- **printargs** [sh, none]: Print each arg on its own line.
- **printcmd** [python, none]: `shlex.quote`-joined argv.
- **pup-links** [sh, -h]: Fetch URL and pull anchors via pup.
- **quote-args** [python, none]: Same as printcmd (alias).
- **select-random** [bash, none]: Print a random line from stdin/files.
- **sponge** [sh, none]: moreutils-like sponge: collect stdin, write atomically.
- **startswith** [sh, -h]: Filter lines starting with literal prefix (no regex).
- **strip-color-codes** [sh, none]: Strip ANSI escape codes from input.
- **strip-emoji** [python (uv), none]: Strip emoji from stdin.
- **sum** [sh, none]: `awk '{s+=$1}END{print s}'`.
- **uniq-seen** [sh, none]: `huniq` if available, else `awk !visited[$0]++`.
- **uniq-seen-last** [sh, none]: uniq-seen reversed (keep last occurrence).
- **urljoin** [python, none]: `urllib.parse.urljoin(base, url)`.
- **xargs-paste** [sh, none]: Run command per stdin line, paste output as second column.

## HTTP / web / archive.org (`cmdfu`, `download-webofstories`, `httpless`, `gist-cmd`, `update-gist-generic`, `ia-info`, `ia-parallel-download`, `phantomget`, `pinboard-add`)
- **cmdfu** [bash, none]: Query commandlinefu by pattern.
- **download-webofstories** [sh, none]: Scrape webofstories.com videos by speaker.
- **gist-cmd** [sh, none]: Run command and post command+output as a gh gist.
- **httpless** [sh, none]: `httpie | less -R` with colors and headers preserved.
- **ia-info** [bash, none]: Internet Archive metadata with file size summary (jq formatted).
- **ia-parallel-download** [python (uv), --help]: Parallel `ia download` via aria2c.
- **phantomget** [sh, none]: Render page via phantomjs and print HTML.
- **pinboard-add** [bash, -h]: Add URL to Pinboard with tags/title/description options.
- **update-gist-generic** [bash, -h]: Update a github gist file from stdin or file.

## Reading / personal info (`reader-views`, `ssa-total-earnings`, `ofxdate`)
- **ofxdate** [python, none]: Print end_date of OFX/QFX statement file as Unix epoch.
- **reader-views** [bash, none]: List of personal reader-tag categories (data file as script).
- **ssa-total-earnings** [sh, none]: Sum MedicareEarnings from SSA XML statement.

## Miscellaneous (one-offs)
- **ack** [perl, --help]: Vendored `ack` 3.8.1 grep tool (full Perl distribution).
- **beep** [sh, none]: `printf '\a'`.
- **bgrm** [sh, -h]: Move-aside then background-rm of paths. **DESTRUCTIVE**.
- **cargo-install** [sh, none]: `cargo install` wrapper using cargo-update if present.
- **drop** [sh, none]: Cross-platform "trash this file" wrapper.
- **dump-pickled** [python, none]: Pretty-print a serialized Python object file (uses pprint/pprintpp).
- **getch** [python, none]: Read one char with `readchar`.
- **link-xcode-sdks** [sh, -h]: Symlink old SDKs into Xcode after upgrade.
- **kcompile.py** [python, none]: Helpers for compiling Python from strings (used by csvpyrow).
- **llm-server** [bash, -h]: Manage SwiftLM-backed local LLM model servers (start/stop/status).
- **parse_zsh_startup** [python (py2), none]: Parse zsh startup profile log.
- **repo-outgoing** [sh, none]: `repo forall` showing outgoing commits per project.
- **repo-uncontrolled** [sh, none]: Show directories not present in `repo list`.
- **sherlock** [sh, none]: Run sherlock-project via pipenv from a ghq clone.
- **surun** [bash, none]: Run command as different user using `su` instead of `sudo`.
- **zed-selectenv** [bash, none]: Search common venv locations for Zed Python env selection.
- **zed-sync-autoinstall** [bash, -h]: Sync installed Zed extensions to `auto_install_extensions`.

## Cautions
- **No `--help` long-option support** outside Python scripts and a small set of bash scripts (`git-setup`, `wait-for-nas-connectivity`). When in doubt, try `-h` first.
- **Several scripts run destructive operations without `-h` check or confirmation.** Flagged inline with **DESTRUCTIVE**. Examples: `brew-clean`, `brew-reinstall-casks`, `brew-wipe-cache`, `bb-clean`, `bb-kill`, `nix-clean`, `pacman-remove-orphans`, `clean-sstate`, `bgrm`, `kkill`, `cleaneject`, `ddimage-sd`, `resolvelinks`, `remove-empty-dirs`, `safari-webapp-cache-clean`. Read source before invoking unfamiliar ones.
- **uv-script convention.** Scripts with `#!/usr/bin/env -S uv run --script` and inline `# /// script` headers manage their own deps: `cached-retool`, `csvpyrow`, `devpod-list`, `fdupes-select`, `ia-parallel-download`, `strip-emoji`, `yocto-releases`.
- **Vendored Perl `ack`.** ~168 KB: a full third-party tool, not user code.
- **Many bb-* and brew-* scripts are 1-3 lines.** Reading source for those is faster than probing `-h`. Use the index to identify them by `[type, none]` and a tiny purpose blurb.
