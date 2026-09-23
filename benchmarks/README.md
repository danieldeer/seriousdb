# Benchmarks

The benchmark suite measures database operations using isolated temporary files.
Each benchmark function's docstring describes its workload, timing boundaries and
correctness checks.

## Run benchmarks

Run commands from the repository root with `uv`:

```bash
uv run --locked --group benchmark -m benchmarks
```

The runner prints compact results and saves raw samples with revision, environment
and workload metadata in ignored `.benchmarks/` JSON files.

Use pytest's `-k` filter to select benchmarks or dataset IDs:

```bash
uv run --locked --group benchmark -m benchmarks -k "process_reads and 1000x32B"
```

| Option                    | Effect                                  |
|---------------------------|-----------------------------------------|
| `--extended`              | Include larger datasets.                |
| `--engine-rounds=20`      | Set the number of measured rounds.      |
| `--process-counts 1 4 16` | Choose process counts.                  |
| `--multiprocess-writes`   | Enable experimental shared-file writes. |

See `uv run --locked --group benchmark -m benchmarks --help` for defaults and
other pytest options, or use `--collect-only` to list available cases.

Concurrent writes are unsupported and skipped by default. To run the probe and
show expected failure reasons:

```bash
uv run --locked --group benchmark -m benchmarks -k process_writes --multiprocess-writes -rx
```

Failed write timings do not represent valid throughput, and successful rounds do
not establish general process safety.

Check correctness without timing (also run in CI), or compare saved results:

```bash
uv run --locked --group benchmark pytest benchmarks --benchmark-disable
uv run --locked --group benchmark pytest-benchmark compare
```

## Interpret results

Compare matching workloads, datasets and worker counts on the same idle machine, Python version and
storage. Check revision and persistence semantics, and start a new baseline when the workload
version changes. Use the median and spread rather than the fastest sample. OPS counts complete
scenarios per second, not individual reads or writes. OS caching and process communication can
affect results; consult the benchmark docstrings for what each timing includes. CI checks
correctness without performance thresholds; performance history stays local.
