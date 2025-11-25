#!/bin/bash

# wait-for-it.sh: Wait until a host and port are available

host="$1"
port="$2"

shift 2

echo "Waiting for $host:$port..."

while ! nc -z "$host" "$port"; do
  sleep 1
  echo "Waiting for $host:$port..."
done

echo "$host:$port is available, starting service..."

exec "$@"