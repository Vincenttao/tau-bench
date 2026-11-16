# Repository Guidelines

## Project Structure & Module Organization

This project evaluates openJiuwen Java against the official τ³ banking benchmark.
- `python/`: evaluation supervisors, agent adapters, diagnostics, and report generators.
- `java/`: Maven-based NativeSkillAgent stdio bridge; sources live in `src/main/java/eval/`.
- `enterprise-java/` and `replay-java/`: Runtime/MOA integration and fixed-response replay adapters.
- `tests/`: Python regression tests, including `tests/otel/` capture checks.
- `config/`: experiment definitions, non-secret gateway settings, and OTLP dependencies.
- `experiments/`: isolated variants, including `deepagent-todo-skill-mcp/`.
- `runs/`: execution evidence and generated reports. Preserve historical artifacts.

Read `README.md`, `测试执行计划-V0.2.md`, and the relevant experiment guide before changing execution behavior.

## Build, Test, and Development Commands

Use Linux/WSL, Bash, Python 3.12, and the documented JDK 21 environment. The main POM targets Java 17; JDK 17 end-to-end execution is unverified. Install matching openJiuwen dependencies locally first.

```bash
mvn -B -ntp -f java/pom.xml -DskipTests package dependency:build-classpath -Dmdep.outputFile=classpath.txt
bash enterprise-java/build.sh
bash replay-java/build.sh
python -m unittest discover -s tests -v
python -m unittest discover -s tests -p 'test_eval_config.py' -v
python python/full_run.py --output runs/new-plan --trials 5 --trial-seed-mode fixed
```

Build the main bridge before auxiliary adapters. The final command generates a plan; `--execute` enables model calls and requires the documented prerequisites.

## Coding Style & Naming Conventions

Use four-space Python indentation, `snake_case` functions/modules, and `test_*.py` test files. Use Java `PascalCase` classes under package `eval`. Follow surrounding code and keep changes focused. No repository-wide formatter or linter configuration was identified.

## Testing Guidelines

Tests use `unittest` and mocks. Add focused regressions for changed configuration, process supervision, protocol handling, and metrics. No numeric coverage threshold is documented. Check OTLP and experiment-specific suites separately using their guides. Report unit tests, Java builds, protocol checks, and live banking evaluations as separate verification results.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout, so no existing commit convention can be confirmed. Use concise imperative subjects, such as `Fix replay timeout classification`. Describe the affected adapter or experiment, behavior changes, validation commands, and evidence paths. Link applicable issues and identify untested dependencies.

## Configuration & Evidence Safety

Supply credentials through environment variables or interactive input. Never save keys in source, manifests, or reports. Use a fresh output directory when configuration or artifacts change. Preserve raw traces, record artifact hashes, and keep unscored results explicit. Follow stage gates before live runs; report benchmark scores separately from enterprise acceptance.
