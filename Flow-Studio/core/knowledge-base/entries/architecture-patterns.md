# Architecture Patterns — Knowledge Base

## Monolith vs. Microservices

### Decision Rule
**Principle**: Default to a monolith. Extract microservices only when a specific team or scaling boundary is proven to be needed.

**Context**: Applies to any new system design or team starting from scratch.

**Rationale**: Microservices add network latency, distributed transactions, operational complexity, and service discovery costs. A well-structured monolith serves teams of 2-15 engineers effectively. The cost of a premature microservice extraction is 3-10x the cost of a later extraction.

**Signs you actually need microservices:**
- Different services need to be deployed and scaled independently, frequently
- Multiple teams own different business domains and need release autonomy
- Services have fundamentally different technology requirements (ML vs. web API)

**Tags**: #architecture #monolith #microservices

---

## Modular Monolith Pattern

### Decision Rule
**Principle**: When the team is 5-20 engineers working on a single product, use a modular monolith with strict module boundaries enforced by tooling.

**Structure:**
```
src/
  modules/
    auth/
      api.ts       ← only export this to other modules
      service.ts   ← internal
      repository.ts ← internal
    billing/
      api.ts
      ...
  shared/
    types/
    utils/
```

**Rule**: Modules communicate only through each other's `api.ts`. No module imports another module's internal files.

**Tags**: #architecture #modular-monolith #team-structure

---

## Database Per Service (for true microservices)

**Principle**: Each microservice owns its data. No shared database between services.

**Rationale**: Shared databases create implicit coupling that defeats the purpose of service separation. Schema changes in one service break others.

**Consequence**: Cross-service data queries require:
- API calls between services, or
- Event-driven data duplication, or
- Read-side denormalized projections (CQRS)

**Tags**: #architecture #microservices #database #coupling

---

## Event-Driven Architecture

### When to use
**Principle**: Use event-driven architecture when components need to be temporally decoupled — they cannot or should not wait for each other synchronously.

**Good use cases:**
- Notification sending after order placement (order service doesn't wait for email)
- Audit logging (main flow doesn't wait for audit entry)
- Data pipeline processing (events trigger downstream transformations)

**Bad use cases:**
- User login (synchronous request-response is clearer)
- Database reads (events don't help with reads)
- When eventual consistency is not acceptable

**Event schema requirements:**
- Events should be immutable and append-only
- Include: eventType, eventId, timestamp, version, payload
- Never include internal DB IDs that would create coupling

**Tags**: #architecture #event-driven #async #coupling

---

## CQRS (Command Query Responsibility Segregation)

**Principle**: Separate the write model (commands) from the read model (queries) when they have fundamentally different requirements.

**Apply when:**
- Read and write loads are significantly different (reads 100x more frequent)
- Read queries require denormalized data that doesn't match write structure
- Different consistency requirements for reads and writes

**Do NOT apply when:**
- Simple CRUD applications with uniform access patterns
- Team is not experienced with the pattern (high learning curve)

**Tags**: #architecture #CQRS #performance #complexity

---

## Repository Pattern

**Principle**: Abstract data access behind an interface. Business logic never directly calls the database driver.

```typescript
// Good
interface UserRepository {
  findById(id: string): Promise<User | null>;
  save(user: User): Promise<void>;
}

// Bad: business logic with direct DB calls
async function processUser(db: Database, id: string) {
  const row = await db.query("SELECT * FROM users WHERE id = $1", [id]);
  ...
}
```

**Benefits:**
- Testability: swap real repo for in-memory repo in tests
- Flexibility: change ORM/database without touching business logic

**Tags**: #architecture #patterns #repository #testability

---

## Hexagonal Architecture (Ports and Adapters)

**Principle**: Business logic at the center, external concerns (HTTP, database, queues) as adapters on the outside.

```
┌────────────────────────────────────┐
│           Application Core         │
│  ┌──────────────────────────────┐  │
│  │        Domain Logic           │  │
│  └──────────────────────────────┘  │
│  Ports (interfaces)                │
└────────────┬──────────────┬────────┘
             │              │
     ┌───────┴─────┐  ┌────┴──────────┐
     │  HTTP Adapter│  │  DB Adapter   │
     └─────────────┘  └───────────────┘
```

**Apply when:** Complex domain logic that must be independent of delivery mechanism (HTTP today, CLI tomorrow, gRPC next quarter).

**Tags**: #architecture #hexagonal #dependency-inversion
