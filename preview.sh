#!/usr/bin/env bash
# Build the site and open it in a browser, exactly as it will be published.
#
#   ./preview.sh
#
# Stop it with Ctrl-C. Pages rebuild as you edit, so leave it running and
# refresh. Nothing here touches the live site -- that only happens on push.

set -e
cd "$(dirname "$0")"

# The system Ruby is too old for this Gemfile; Homebrew's is what works here.
if [ -d /opt/homebrew/opt/ruby/bin ]; then
  export PATH="/opt/homebrew/opt/ruby/bin:$PATH"
fi

if ! command -v bundle >/dev/null; then
  echo "bundler not found. Install Ruby with:  brew install ruby"
  exit 1
fi

if [ ! -d .bundle ] && ! bundle check >/dev/null 2>&1; then
  echo "installing gems (first run only)…"
  bundle install
fi

PORT=4000
echo
echo "  http://127.0.0.1:$PORT"
echo "  Ctrl-C to stop"
echo

# open once the server is actually answering
( for _ in $(seq 1 40); do
    if curl -s -o /dev/null "http://127.0.0.1:$PORT/"; then open "http://127.0.0.1:$PORT/"; break; fi
    sleep 0.5
  done ) &

exec bundle exec jekyll serve --port "$PORT" --livereload
