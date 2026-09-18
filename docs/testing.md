# Testing

The project uses `pytest` for automated testing of the Python API and cache,
and FastAPI's `TestClient` for HTTP API testing.

## Running the Tests

Run the regular test suite in `tests/` with:

```bash
uv run pytest
```

The test suite covers:

- Python API operations and synchronous persistence
- HTTP endpoint behavior
- Validation behavior
- CRUD operations
- Threads accessing a single shared cache

Each test uses an isolated temporary database so the test suite does not modify the local `.sdb` database.

The benchmark scenarios run separately using the commands below.

## Performance benchmarks

Benchmarks measure `Cache` directly, excluding HTTP. Inputs use seed 212, with
one unrecorded warmup and five measured rounds. Default datasets are 100 and 1,000
entries with 32-byte values, plus 1,000 with 1,024-byte values. `--extended` adds
10,000 and 100,000 entries with 32-byte values.

| File in `benchmarks/` | Timed work                                                                                 |
|-----------------------|--------------------------------------------------------------------------------------------|
| `test_persistence.py` | Batch insert and persist; flush; overwrite 100 keys, flushing each write or once per batch |
| `test_reads.py`       | Load and read every key; load only; reads from a loaded cache                              |
| `test_workloads.py`   | Shuffled 90% reads / 10% overwrites in memory                                              |
| `test_concurrency.py` | The same mixed workload split across 1, 2, 4 or 8 threads sharing one cache                |

Setup and correctness checks are outside timing, using temporary files. Mutating
workloads reset each round; flush rounds change a cached value before timing.
Every round's read results and persisted values are checked outside timing.
Thread timings include task submission, synchronization and joins, but exclude
pool creation.
Reads and writes target disjoint keys, so expected read values are deterministic.

From the repository root, run compact output with saved history:

```bash
uv run --locked --group benchmark -m benchmarks
```

Run just the 1,000-entry SeriousDB batch case in PowerShell:

```powershell
$case = "batch_write and 1000x32B"
uv run --locked --group benchmark -m benchmarks -k $case
```

Or on macOS/Linux (Bash or Zsh):

```bash
case_filter="batch_write and 1000x32B"
uv run --locked --group benchmark -m benchmarks -k "$case_filter"
```

Add `--extended` for larger datasets or `--engine-rounds=20` for more samples.
Compare SeriousDB's saved runs or check correctness without timing:

```bash
uv run --locked --group benchmark pytest-benchmark compare
uv run --locked --group benchmark pytest benchmarks --benchmark-disable
```

Ignored `.benchmarks/` JSON stores timings, revision, environment and workload
metadata. Compare matching cases and workload versions on the same idle machine,
Python and storage; use median and spread. Start a fresh baseline when the
workload version changes. OPS counts whole scenarios per second, not individual
reads/writes.

CI checks benchmark correctness without timing thresholds. Performance history
stays local.

Persistence timings exclude `fsync` and may benefit from OS caching; they do not
measure crash-safe commits or cold-disk performance. Concurrency benchmarks use
threads sharing one cache, not multiple processes accessing the same file.
