The script template creates its workspace under TMPDIR.

  $ mkdir bin
  $ cat > bin/mktemp <<'EOF'
  > #!/bin/sh
  > [ "$1" = "-d" ] || exit 1
  > case "$2" in
  > "$TMPDIR"/template.sh.XXXXXX) printf '%s\n' "$TMPDIR/workspace" ;;
  > *) exit 1 ;;
  > esac
  > EOF
  $ chmod +x bin/mktemp
  $ TMPDIR="$CRAMTMP/custom" PATH="$PWD/bin:$PATH" bash -c '. "$TESTDIR/../template.sh"'
