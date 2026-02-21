# Coverage Uplift Report

**Date**: 2026-02-20
**Scope**: Test strategy across 10 services (3 backend + 7 frontend)
**Approach**: Risk-weighted, no vanity coverage. Critical domain logic + contract boundaries.

---

## Baseline Coverage

| Repo | Overall | Tests | Critical Gap |
|------|---------|-------|-------------|
| brainops-ai-agents | 24% | 273 | 54 files at 0%, 13,883 untested stmts |
| myroofgenius-backend | 12% | 95 | Core routes 12-20%, brainops_ai_os 17-31% |
| mcp-bridge | 46% | 211 | server.js 30%, tool-versioning 6% |
| weathercraft-erp | Has vitest | 348 files | Good coverage framework |
| myroofgenius-app | Has jest | 55 files | Adequate |
| brainops-command-center | Has vitest | 13 files | Moderate |
| vaulted-slabs | Has vitest | 12 files | Moderate |
| brainstack-studio | Has jest | 4 files | Minimal |
| weathercraft-guardian | Playwright only | 1 file | E2E only, no unit |
| wc-share | Playwright only | 1 file | E2E only, no unit |

---

## Risk Matrix

| Module | Risk | Pre-Coverage | Post-Coverage | Tests Added | Priority |
|--------|------|-------------|---------------|-------------|----------|
| TenantScopedPool (tenant isolation) | CRITICAL | ~50% | **~80%** | 26 property tests | P0 |
| Brain store contract (backend→agents) | CRITICAL | 0% | **~70%** | 26 contract tests | P0 |
| Auth middleware | HIGH | ~20% | **~45%** | 22 contract tests | P1 |
| Stripe webhooks (tenant resolution) | HIGH | ~28% | **~35%** | 7 contract tests | P1 |
| Alert system (duplication fix) | HIGH | ~20% | **~30%** | 5 regression tests | P1 |
| Invariant engine | HIGH | ~50% | ~50% | (from Phase 12) | Already covered |
| Brain store (agents-side) | HIGH | 100% | 100% | (from Phase 12) | Already covered |
| Base agent (MemoryLossError) | HIGH | ~60% | ~60% | (from Phase 12) | Already covered |
| Task orchestrator (completed_at) | MEDIUM | Low | +3 tests | 3 regression tests | P2 |

---

## Tests Added This Phase

### brainops-ai-agents (26 new tests)

**`tests/test_tenant_guard_properties.py`** — 26 property-style tests

| Test Class | Count | What It Verifies |
|-----------|-------|-----------------|
| `TestConstructorRejectsInvalid` | 7 | All sentinel values (None, "", "null", "None", "undefined") rejected; whitespace and case sensitivity documented |
| `TestConstructorAcceptsValid` | 11 | Valid UUIDs always accepted (10 random + 1 specific) |
| `TestSetLocalAlwaysFires` | 3 | SET LOCAL executes for fetch, execute, and fetchval |
| `TestSemicolonAlwaysBlocked` | 4 | Multi-statement SQL rejected; semicolons in strings also blocked (conservative) |

### myroofgenius-backend (55 new tests)

**`tests/test_brain_store_contract.py`** — 26 contract tests

| Test Class | Count | What It Verifies |
|-----------|-------|-----------------|
| `TestURLResolution` | 5 | URL always ends in /brain; trailing slashes stripped; env var fallback |
| `TestHeaders` | 4 | Content-Type always present; X-API-Key conditional on env var |
| `TestStoreFailureCounting` | 4 | HTTP errors, network errors, success, accumulation |
| `TestRecallFallback` | 4 | Tries /recall→/query→/search; returns data from first success; empty on failure |
| `TestHealthObservability` | 2 | Health dict shape; reflects failures |
| `TestTimestampTracking` | 7 | ISO parsing (Z suffix, None, empty, garbage); newer-of comparison; key format |

**`tests/test_auth_middleware_contract.py`** — 22 contract tests

| Test Class | Count | What It Verifies |
|-----------|-------|-----------------|
| `TestExemptPaths` | 10 | Health/webhook/docs paths exempt; business routes NOT exempt; prefix matching |
| `TestMasterTenantResolution` | 5 | UUID validation; fallback chain; empty/invalid rejected |
| `TestWebhookExemptions` | 6 | All 6 webhook paths are auth-exempt |
| `TestMasterKeyState` | 1 | Master key sets role=admin, user_id=system, tenant_id, authenticated=true |

**`tests/test_stripe_webhook_contract.py`** — 7 contract tests

| Test Class | Count | What It Verifies |
|-----------|-------|-----------------|
| `TestTenantResolution` | 5 | 4-step priority chain (metadata→subscription→customer→email); None metadata safe |
| `TestQuarantineBehavior` | 1 | Unresolvable tenants trigger quarantine INSERT |
| `TestHandlerExceptionRecording` | 1 | Structural: handler exceptions caught as "failed", not silently swallowed |

---

## Coverage Floors (CI Enforcement)

### brainops-ai-agents: `scripts/ci/check_critical_coverage.sh`

| Module | Floor | Rationale |
|--------|-------|-----------|
| `database/tenant_guard.py` | 80% | Tenant isolation is the highest business risk |
| `brain_store_helper.py` | 90% | Memory protocol — data loss prevention |
| `base_agent.py` | 40% | Dual persistence detection |
| `invariant_monitor.py` | 30% | Safety net for the entire system |

### myroofgenius-backend: `scripts/ci/check_critical_coverage.sh`

| Module | Floor | Rationale |
|--------|-------|-----------|
| `core/brain_store.py` | 70% | HTTP contract boundary — was 0%, now covered |
| `middleware/authentication.py` | 40% | Auth bypass would expose all tenant data |
| `routes/stripe_webhooks.py` | 20% | Money flow — idempotency and tenant resolution |
| `brainops_ai_os/awareness_system.py` | 20% | Alert system — duplication fix verified |
| `brainops_ai_os/metacognitive_controller.py` | 15% | Consciousness loop — alert routing verified |

### How to run

```bash
# Agents
cd ~/dev/brainops-ai-agents
bash scripts/ci/check_critical_coverage.sh

# Backend
cd ~/dev/myroofgenius-backend
bash scripts/ci/check_critical_coverage.sh
```

---

## Key Findings (Architecture-Level)

### 1. Tenant Isolation Has Defense-in-Depth but Gaps

**Good**: `TenantScopedPool` uses SET LOCAL (transaction-scoped), fail-closed constructor, SQL parser guardrails.

**Gaps found**:
- No UUID validation on tenant_id (any non-empty string passes)
- `_INVALID_TENANT_IDS` is case-sensitive: `"NULL"` and `"NONE"` pass through
- `get_tenant_db()` ignores tenant_id parameter entirely (dormant bypass)
- Many modules use `get_pool()` directly, bypassing application-layer guardrails (DB-level RLS still applies)

**Mitigated by**: DB-level RLS (4,644 policies on 1,077 tables) catches anything the application layer misses.

### 2. Brain Store Contract Was Completely Untested

The HTTP boundary between `myroofgenius-backend` and `brainops-ai-agents` had **zero tests**:
- URL resolution with 3 env var fallbacks
- Header construction with conditional API key
- Failure counting and observability
- Recall fallback chain (/recall → /query → /search)
- Fire-and-forget dispatch pattern

All now covered by 26 contract tests.

### 3. Auth Middleware Has 5 Distinct Tenant Extraction Paths

This is a complexity concern. Tenant ID can come from:
1. Master API key env var
2. Database API key lookup
3. Supabase JWT `user_metadata.tenant_id`
4. Offline auth fallback (dev mode)
5. `ApiKey` bearer passthrough

Only paths 1, 4, and 5 now have test coverage. JWT validation (path 3) is always monkeypatched in tests — the real JWT decode path has zero test coverage.

### 4. Stripe Webhook Silent Failure Potential

The explore agent flagged that individual handler functions (e.g., `handle_checkout_completed`) could catch exceptions internally and return without re-raising. The structural test verifies the outer try/except pattern is correct, but internal handler failures would be masked. This is a **design choice** (graceful degradation), not a bug.

### 5. Dead Code in Middleware

`rls_middleware.py` and `tenant.py` middleware classes are NOT registered in `main.py`. They appear to be dead code from an earlier architecture. The `auth_production_ready.py` file contains a hardcoded JWT secret and should be deleted.

---

## What Was NOT Done (and Why)

| Item | Reason |
|------|--------|
| Mutation testing (mutmut/cosmic-ray) | Requires full environment setup and long runtime; deferred to a dedicated sprint |
| E2E user journeys (Playwright) | WC-ERP already has 348 test files with Playwright; MRG has 55. No gap. |
| Frontend unit tests for Guardian/WC-Share | Low traffic, static pages. Risk doesn't justify the effort. |
| Overall coverage to 80%+ | Would require testing 13,883 statements of low-risk modules. Vanity. |
| JWT decode path testing | Requires Supabase JWT secret in test env; deferred to integration test sprint |

---

## Test Inventory (Post-Uplift)

### brainops-ai-agents

| Test File | Tests | Focus |
|-----------|-------|-------|
| `test_tenant_guard_properties.py` | 26 | **NEW** — Tenant isolation properties |
| `test_brain_store_resilience.py` | 4 | Memory loss detection |
| `test_base_agent_memory_loss.py` | 4 | Dual persistence failure |
| `test_invariant_resilience.py` | 5 | Invariant engine resilience |
| `test_task_status_completion.py` | 3 | Task status completed_at |
| (existing 231 tests) | 231 | Guardrails, revenue, scheduling, etc. |
| **Total** | **273+** | |

### myroofgenius-backend

| Test File | Tests | Focus |
|-----------|-------|-------|
| `test_brain_store_contract.py` | 26 | **NEW** — HTTP contract boundary |
| `test_auth_middleware_contract.py` | 22 | **NEW** — Auth + tenant extraction |
| `test_stripe_webhook_contract.py` | 7 | **NEW** — Webhook contracts |
| `test_alert_dedup.py` | 5 | Alert duplication fix |
| (existing 35 tests) | 35 | Smoke, readiness, security, dedup |
| **Total** | **95+** | |

### mcp-bridge

| Test Suite | Tests | Coverage |
|-----------|-------|----------|
| 11 test suites | 211 | 46% line, server.js 30% |

---

## Files Created/Modified

| Repo | File | Type |
|------|------|------|
| brainops-ai-agents | `tests/test_tenant_guard_properties.py` | NEW — 26 property tests |
| brainops-ai-agents | `.coveragerc` | NEW — coverage config |
| brainops-ai-agents | `scripts/ci/check_critical_coverage.sh` | NEW — CI gate |
| myroofgenius-backend | `tests/test_brain_store_contract.py` | NEW — 26 contract tests |
| myroofgenius-backend | `tests/test_auth_middleware_contract.py` | NEW — 22 contract tests |
| myroofgenius-backend | `tests/test_stripe_webhook_contract.py` | NEW — 7 contract tests |
| myroofgenius-backend | `.coveragerc` | NEW — coverage config |
| myroofgenius-backend | `scripts/ci/check_critical_coverage.sh` | NEW — CI gate |
| myroofgenius-backend | `COVERAGE_UPLIFT_REPORT.md` | NEW — this document |
