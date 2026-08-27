# Common Pitfalls — Knowledge Base

## Database Pitfalls

### N+1 Query Problem
**Problem**: Loading a list of entities, then making one DB call per entity to fetch related data.

```python
# Bad — N+1
users = User.query.all()  # 1 query
for user in users:
    print(user.orders)    # N queries (one per user)

# Good — eager loading
users = User.query.options(joinedload(User.orders)).all()  # 1 query
```

**Detection**: Logging shows many identical queries with different IDs.
**Tags**: #database #performance #orm

---

### Missing Database Indexes
**Problem**: Queries on non-indexed columns do full table scans. Acceptable on small tables, catastrophic at scale.

**Rule**: Any column used in WHERE, ORDER BY, or JOIN ON clauses is a candidate for an index.

**Check for missing indexes:**
```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;
-- Look for "Seq Scan" on large tables — that's a signal
```

**When NOT to add an index**: Every index slows down writes. Don't index rarely-queried columns or columns with very low cardinality (e.g., boolean columns).

**Tags**: #database #performance #indexes

---

### Non-Backward-Compatible Migrations
**Problem**: Running a migration that breaks the old version of the application causes zero-downtime deployments to fail.

**Safe migration pattern (expand/contract):**
1. **Expand**: Add new column (nullable), deploy new code that writes to both
2. **Migrate**: Backfill old rows
3. **Contract**: Make column required, remove old column, deploy cleanup

**Tags**: #database #migrations #deployment #zero-downtime

---

## Async / Concurrency Pitfalls

### Race Condition on Shared State
**Problem**: Two concurrent operations read-modify-write the same state. One update is lost.

```
Thread A reads balance: $100
Thread B reads balance: $100
Thread A adds $50, writes: $150
Thread B adds $30, writes: $130  ← Thread A's update is lost
```

**Fix**: Use database-level atomic operations or optimistic locking.
```sql
UPDATE accounts SET balance = balance + 50 WHERE id = 1;
-- instead of: read, add in app code, write
```

**Tags**: #concurrency #race-condition #database

---

### Async Waterfall vs. Parallel
**Problem**: Running independent async operations sequentially.

```javascript
// Bad: 3s total (sequential)
const user = await fetchUser(id);       // 1s
const orders = await fetchOrders(id);   // 1s
const profile = await fetchProfile(id); // 1s

// Good: ~1s total (parallel)
const [user, orders, profile] = await Promise.all([
  fetchUser(id),
  fetchOrders(id),
  fetchProfile(id)
]);
```

**Rule**: When async operations are independent, run them in parallel.

**Tags**: #async #performance #javascript

---

## Security Pitfalls

### JWT "None" Algorithm Attack
**Problem**: JWT libraries that accept `alg: none` allow signature bypass.

**Fix**: Explicitly specify the allowed algorithm when verifying:
```javascript
// Bad: accepts whatever alg the token claims
jwt.verify(token, secret);

// Good: only accept the expected algorithm
jwt.verify(token, secret, { algorithms: ['HS256'] });
```

**Tags**: #security #jwt #auth

---

### Timing Attack on Token Comparison
**Problem**: String comparison short-circuits on the first mismatch, leaking information about how many characters match.

**Fix**: Use constant-time comparison:
```python
import hmac
# Bad
if token == expected_token:  # timing attack

# Good
if hmac.compare_digest(token, expected_token):  # constant-time
```

**Tags**: #security #timing-attack #auth

---

### IDOR (Insecure Direct Object Reference)
**Problem**: Using a user-supplied ID to fetch data without verifying the authenticated user owns it.

```javascript
// Bad — any user can view any order by changing the ID
app.get('/orders/:id', (req, res) => {
  const order = await Order.findById(req.params.id);
  res.json(order);
});

// Good — verify ownership
app.get('/orders/:id', authenticate, async (req, res) => {
  const order = await Order.findOne({
    id: req.params.id,
    userId: req.user.id   // ← ownership check
  });
  if (!order) return res.status(404).json({ error: 'Not found' });
  res.json(order);
});
```

**Tags**: #security #authorization #IDOR

---

## API Design Pitfalls

### Leaking Internal Structure
**Problem**: Exposing internal database IDs, column names, or implementation details in the API response.

**Fix**: Use DTOs/serializers that explicitly map what is exposed.
```
Internal: { id: 847, user_id: 3, created_at: ... }
External: { orderId: "ord_847", customerId: "cus_3", createdAt: ... }
```

**Tags**: #api #design #security

---

### Inconsistent Error Responses
**Problem**: Some endpoints return `{ error: "..." }`, others return `{ message: "..." }`, others return HTML.

**Fix**: Standardize error shape at the framework level:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [{ "field": "email", "message": "Invalid format" }]
  }
}
```

**Tags**: #api #design #consistency

---

## Deployment Pitfalls

### Deploying Without a Rollback Plan
**Problem**: A deploy fails and restoring the previous version requires manual steps that take 30+ minutes.

**Fix**: Know the rollback command before deploying:
```
- Git: git revert HEAD && git push
- Docker: kubectl rollout undo deployment/app
- Feature flags: flip the flag, no redeploy needed
```

**Tags**: #deployment #reliability #rollback

---

### Deployment at the Wrong Time
**Principle**: Never deploy:
- Friday afternoon (leaves the team no time to respond before the weekend)
- Monday morning (high traffic, high stakes)
- During a high-traffic event

**Good deploy windows**: Tuesday-Thursday, mid-morning (team is fully available, traffic is normal).

**Tags**: #deployment #operations #reliability
