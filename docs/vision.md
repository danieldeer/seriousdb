# seriousdb: Updated Vision

**Core idea unchanged:** seriousdb stays a lightweight key-value store.

**What's changing:** the project has been treating the FastAPI HTTP layer as the product; designing a clean `get`/`put` API was the main effort. The team now sees that as too limited and, frankly, less interesting to build. The new focus is the **database engine itself**, real database mechanics (concurrency, persistence, storage), with the HTTP layer demoted to an example consumer rather than the thing driving the design.

## Target architecture

```
Application / API  →  seriousdb (public Python interface)  →  database engine  →  storage
```

- **seriousdb becomes an importable Python package.** Other projects (`pip install seriousdb`) depend on it directly and build their own use-case-specific APIs on top, the way `seriousdb-gameshelf` already does as a first real consumer.
- **The public Python interface** (get/set/delete, transactions, concurrency semantics) is defined independently of HTTP. It's the actual contract seriousdb offers.
- **The FastAPI layer stays**, but only as a reference/example of consuming seriousdb (and possibly, later, as a separate concern: a distributed/remote interface). It should not dictate what the engine looks like.
- **Value/storage format is an implementation detail** of the engine, decided after the engine's interface is defined, not something the API layer should force (this resolves the earlier "what value types to support" debate).

## Concrete engineering goals

- **Concurrency target:** support **100 concurrent processes** reading/writing at once (reframed from "100 concurrent users," which is a much lighter load, about 10 req/s, to "100 parallel operations," a real stress test).
- **Durability:** writes should block until actually persisted, rather than returning early while data still sits in a cache/queue. This makes benchmark and correctness results meaningful.
- **Performance baseline:** benchmark the engine directly through the Python interface (not through HTTP, to avoid measuring network/framework overhead). Start simple: bulk insert/read/delete of N entries, then extend to varying DB sizes and concurrent workers.
- **Reference bar:** the practical target is to **beat TinyDB** (same language/stack, same embedded-KV concept) rather than compete with SQLite/Redis/LMDB/Postgres, which aren't realistic comparisons.

## Immediate priorities (in order)

1. **Define the minimal public Python interface** (get/set/delete first), a prerequisite for meaningful benchmarking.
2. **Stand up performance tests** against that interface (tracked in issue #212), starting basic, growing to cover concurrency.
3. **Formalize a roadmap** that states these guarantees explicitly, so contributors outside the core team understand the direction (not just the maintainers).
4. **Communicate the pivot publicly**, then triage existing issues/PRs into: still relevant to the engine → review normally; useful but needs rework → discuss/adapt; API-only under the old direction → close with an explanation. The team explicitly wants to avoid silently discarding contributors' work.
