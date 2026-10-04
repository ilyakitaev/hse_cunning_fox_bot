#!/bin/bash
set -e

# Set proxy only if PROXY_URL is set and non-empty
if [ -n "$PROXY_URL" ]; then
    export HTTP_PROXY="$PROXY_URL"
    export HTTPS_PROXY="$PROXY_URL"
    export http_proxy="$PROXY_URL"
    export https_proxy="$PROXY_URL"
fi

# Run the bot
exec python -m src.main "$@"
