#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
experiment_java="$PWD"
repo_root="$(cd ../../.. && pwd)"
solution_root="${AGENT_SOLUTION_ROOT:-$repo_root/../agent-solution}"
python - "$solution_root" <<'PY'
import hashlib, json, pathlib, sys
for name in ('source.json', 'model-client-source.json', 'assembly-source.json',
             'planning-language-source.json', 'confirmation-language-source.json'):
    pin = json.loads((pathlib.Path('patches') / name).read_text())
    source = pathlib.Path(sys.argv[1]) / pin['source']
    if hashlib.sha256(source.read_bytes()).hexdigest() != pin['sha256']:
        raise SystemExit('MOA source differs from reviewed patch base')
    destination = pathlib.Path('target/patched') / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
PY
python - "$repo_root/../agent-runtime-java" <<'PY'
import hashlib, pathlib, sys
import json
pin = json.loads(pathlib.Path('patches/orchestrator-source.json').read_text())
orchestrator = pathlib.Path(sys.argv[1]) / pin['source']
if hashlib.sha256(orchestrator.read_bytes()).hexdigest() != pin['sha256']:
    raise SystemExit('Runtime source differs from reviewed bounded wait base')
(pathlib.Path('target/patched') / orchestrator.name).write_bytes(orchestrator.read_bytes())
source = pathlib.Path(sys.argv[1]) / 'service/agent-service-app/src/main/java/com/openjiuwen/service/app/controller/a2a/client/A2ARemoteAgentClient.java'
if hashlib.sha256(source.read_bytes()).hexdigest() != 'f7bc6dd3588e20935f6189db541e02e8b2fce0b8f26afbe5da3d0dff2746e982':
    raise SystemExit('Runtime source differs from reviewed no-replay patch base')
(pathlib.Path('target/patched') / source.name).write_bytes(source.read_bytes())
PY
patch --silent target/patched/A2AEnabledServeOrchestrator.java patches/bounded-batch-wait.patch
patch --silent target/patched/A2ARemoteAgentClient.java patches/remote-no-replay.patch
patch --silent target/patched/IntentRouter.java patches/slow-only-router.patch
patch --silent target/patched/MoaModelFactory.java patches/model-client.patch
patch --silent target/patched/MoaRuntimeAutoConfiguration.java patches/english-slow-assembly.patch
patch --silent target/patched/StagePlanningRail.java patches/planning-language.patch
patch --silent target/patched/ConfirmationResponses.java patches/confirmation-language.patch
mkdir -p target/classes
javac -cp "$repo_root/shared/java/target/classes:$(cat "$repo_root/shared/java/classpath.txt")" -d target/classes \
  target/patched/*.java src/eval/*.java
java -cp "$experiment_java/target/classes:$(cat "$repo_root/shared/java/classpath.txt")" eval.SlowOnlyRoutingTest
java -cp "$experiment_java/target/classes:$(cat "$repo_root/shared/java/classpath.txt")" eval.EnglishConfirmationTest
java -cp "$experiment_java/target/classes:$(cat "$repo_root/shared/java/classpath.txt")" eval.MainModelEvidenceTest
java -cp "$experiment_java/target/classes:$(cat "$repo_root/shared/java/classpath.txt")" eval.TodoTransitionTest
java -cp "$experiment_java/target/classes:$repo_root/shared/java/target/classes:$repo_root/shared/java/target/test-classes:$(cat "$repo_root/shared/java/classpath.txt")" eval.TodoBoundaryValidationTest
