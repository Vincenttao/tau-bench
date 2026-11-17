#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p enterprise-java/target/classes
"${JAVA_HOME:+$JAVA_HOME/bin/}javac" -parameters -cp "java/target/classes:$(cat java/classpath.txt)" -d enterprise-java/target/classes enterprise-java/src/eval/*.java
