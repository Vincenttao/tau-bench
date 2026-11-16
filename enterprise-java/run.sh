#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec "${JAVA_HOME:+$JAVA_HOME/bin/}java" -cp "enterprise-java/target/classes:java/target/classes:$(cat java/classpath.txt)" eval.EnterpriseBankingBridge "$@"
