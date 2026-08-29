A supplied cask_args line normalizes the generated bundle output.

  $ mkdir bin
  $ cat > bin/brew <<'EOF'
  > #!/bin/sh
  > if [ "$1" = bundle ] && [ "$2" = dump ]; then
  >     printf '%s\n' 'cask_args appdir: "/Applications"' 'brew "ripgrep"'
  > fi
  > EOF
  $ chmod +x bin/brew
  $ printf '%s\n' 'cask_args appdir: "~/Applications"' 'brew "ripgrep"' | PATH="$PWD/bin:$PATH" "$TESTDIR/../../brewfile-diff-dump" -
