#!/bin/sh
VISUAL="${VISUAL:-${EDITOR:-vim}}"
case "$VISUAL" in
    codewait|code\ -w)
        # Synchronous editing via GUI, switch to async
        VISUAL=code
        ;;
    zed\ --wait)
        # Synchronous editing via GUI, switch to async
        VISUAL=zed
        ;;
esac
exec "$VISUAL" "$@"
