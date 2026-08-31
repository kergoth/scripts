#!/usr/bin/env bash
#
# myscript - a script that does something.
#
# Usage: myscript [options] ARG.. OTHERARG [extra_args..]
#
# Do something.
#
# Options:
#     -n          Dry run, don't actually do anything
#     -v          Increase verbosity, can be specified multiple times
#     -q          Decrease verbosity, can be specified multiple times
#     -V          Show version information
#     -h          Show this help message

set -euo pipefail

# Exit with error on bash <4.0
if [ "${BASH_VERSINFO:-0}" -lt 4 ]; then
    echo "Error: Bash version 4.0 or higher is required." >&2
    exit 1
fi

tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/${BASH_SOURCE[0]##*/}.XXXXXX")
# Clean up after ourselves
trap 'rm -rf "$tmpdir"' EXIT
# Ensure we leave no child processes behind on interruption or termination
trap 'trap - INT; kill -INT $$ &>/dev/null' INT
trap 'trap - TERM; kill -TERM -- -$$ &>/dev/null; kill -TERM $$ &>/dev/null' TERM

show_help() {
    sed -n '/^# Usage:/,/^# *-h /p' "$0" | sed 's/^# *//'
}

msg() {
    fmt="$1"
    if [ $# -gt 1 ]; then
        shift
    fi
    # shellcheck disable=SC2059
    printf "$fmt\n" "$@" >&2
}

msg_color() {
    local color=$1
    shift
    local msg=$1
    shift
    # shellcheck disable=SC2059
    if [ -n "${NO_COLOR:-}" ] || { [ -z "${COLOR:-}" ] && ! [ -t 1 ]; }; then
        printf "${msg}\n" "$@" >&2
        return
    else
        printf "\033[${color}m${msg}\033[0m\n" "$@" >&2
    fi
}

msg_yellow() {
    msg_color '33' "$@"
}

msg_red() {
    msg_color '31' "$@"
}

msg_blue() {
    msg_color '34' "$@"
}

msg_green() {
    msg_color '32' "$@"
}

msg_cyan() {
    msg_color '36' "$@"
}

msg_purple() {
    msg_color '35' "$@"
}

msg_magenta() {
    msg_color '35' "$@"
}

msg_verbose() {
    if [ "${verbosity:-0}" -gt 0 ]; then
        msg_yellow "$@"
    fi
}

msg_debug() {
    if [ "${verbosity:-0}" -gt 1 ]; then
        msg "$@"
    fi
}

msg_error() {
    msg_red "$@"
}

msg_info() {
    msg_blue "$@"
}

msg_success() {
    msg_green "$@"
}


die() {
    msg_error "$@"
    exit 1
}

maybe_die() {
    local ret=$?
    local msg=${1:-}

    case $ret in
        130)
            msg_red "${msg:+$msg, }Interrupted"
            kill -INT $$
            ;;
        0) ;;
        *)
            if [ -n "${continue_on_error:-}" ]; then
                msg_yellow "Error: ${msg:+$msg, }Continuing after error with exit code $ret"
                return $ret
            else
                die "Error: ${msg:+$msg, }Failed with exit code $ret"
            fi
            ;;
    esac
}

run() {
    if [ "${dry_run:-0}" = "1" ] || [ "${verbosity:-0}" -gt 0 ]; then
        printf '❯ %s\n' "$(printcmd "$@")" >&2
    fi
    if [ "${dry_run:-0}" != "1" ]; then
        "$@" || return $?
    fi
}
