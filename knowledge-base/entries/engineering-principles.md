# Engineering Principles — Knowledge Base

## Code Clarity

### Naming Rules
**Principle**: Names are the primary documentation. If you need a comment to explain a name, the name is wrong.

| Anti-pattern | Better |
|-------------|--------|
| `data`, `info`, `obj` | `userProfile`, `orderSummary` |
| `flag`, `bool`, `check` | `isAuthenticated`, `hasPermission` |
| `process()`, `handle()`, `do()` | `validatePayment()`, `sendWelcomeEmail()` |
| `x`, `i`, `temp` (in non-obvious context) | `retryCount`, `currentUser` |

**Rule for booleans**: Always prefix with `is`, `has`, `can`, `should`, `was`.
**Rule for functions**: Start with a verb that describes what it does.

**Tags**: #code-quality #naming #readability

---

## Error Handling

### The Explicit Error Contract
**Principle**: Every function that can fail should make failure explicit in its signature.

```typescript
// Bad: caller doesn't know this can fail
function findUser(id: string): User { ... }

// Good: failure is part of the interface
function findUser(id: string): User | null { ... }

// Good (Result type pattern):
function findUser(id: string): Result<User, NotFoundError | DatabaseError> { ... }
```

**Rule**: Never catch an exception and return `null`/`undefined` silently. The caller loses the ability to distinguish between "not found" and "database error".

**Tags**: #error-handling #code-quality

---

### Error Levels
**Principle**: Match the error response to the error severity.

| Error type | Correct response |
|-----------|-----------------|
| Programming error (bug) | Throw/panic — don't hide it |
| Expected failure (not found, validation) | Return error value / typed error |
| System failure (network, disk) | Log + return error to caller |
| Unrecoverable state | Log + restart/shutdown process |

**Tags**: #error-handling #reliability

---

## Single Responsibility Principle

**Principle**: A function/class should have one reason to change. If you can describe what it does using "and", split it.

**Practical test**: Can you write a name for this function without "and", "or", or "also"?

```typescript
// Bad: fetchAndTransformAndStoreUser()
// Good: fetchUser(), transformUserData(), storeUser()
```

**Tags**: #code-quality #SRP #design-principles

---

## Composition over Inheritance

**Principle**: Prefer building from small, composable pieces over deep inheritance hierarchies.

```typescript
// Inheritance (fragile):
class AnimalDog extends Animal { ... }
class ServiceDog extends AnimalDog { ... }

// Composition (flexible):
const dog = createAnimal({ name: "Rex", sounds: bark, hasLegs: true });
const serviceDog = withServiceTraining(dog);
```

**When inheritance is OK**: 
- Framework extension points that are designed for it
- True "is-a" relationships with stable, well-understood hierarchies (rarely)

**Tags**: #code-quality #composition #inheritance #design-principles

---

## Fail Fast

**Principle**: Validate inputs at the system boundary and reject invalid data immediately. Do not let bad data propagate deep into the system.

```typescript
function createOrder(userId: string, items: OrderItem[], total: number) {
  // Fail fast — validate at entry point
  if (!userId) throw new ValidationError("userId is required");
  if (!items.length) throw new ValidationError("order must have at least one item");
  if (total <= 0) throw new ValidationError("total must be positive");
  
  // If we reach here, we can trust the data
  return new Order(userId, items, total);
}
```

**Tags**: #code-quality #validation #fail-fast

---

## DRY (Don't Repeat Yourself) — Applied Correctly

**Principle**: DRY is about knowledge, not code. Two pieces of code that look similar but represent different concepts should NOT be merged.

**Dangerous DRY**: abstracting two pieces of similar code that will diverge in the future creates coupling between unrelated things.

**Test before abstracting**: Wait until you have the same logic in 3+ places, and verify the logic truly represents the same concept. Then abstract.

**Tags**: #code-quality #DRY #abstraction

---

## Immutability by Default

**Principle**: Prefer immutable data structures. Mutate only when there is a clear performance or API reason.

```typescript
// Bad: mutates input
function addItem(cart: Cart, item: Item) {
  cart.items.push(item); // side effect!
  return cart;
}

// Good: returns new value
function addItem(cart: Cart, item: Item): Cart {
  return { ...cart, items: [...cart.items, item] };
}
```

**Benefits**: Predictable behavior, easier debugging, safe to share across threads.

**Tags**: #code-quality #immutability #functional

---

## Defense in Depth (Security)

**Principle**: Never rely on a single security control. Layer defenses.

```
Layer 1: Input validation (reject bad data at the boundary)
Layer 2: Parameterized queries (prevent SQL injection even if validation fails)
Layer 3: Least privilege (limit what a compromised component can access)
Layer 4: Logging and alerting (detect when something bad happened)
```

Even if one layer fails, the others limit the damage.

**Tags**: #security #defense-in-depth
