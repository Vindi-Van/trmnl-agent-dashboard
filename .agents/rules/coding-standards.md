---
trigger: always_on
---

> **STRICTNESS LEVEL: MUST** — All rules are mandatory.

---

## 1. Code Quality

### Modularity
- **MUST** create new functionality in separate files, never in entry points
- **MUST** keep functions small and focused (single responsibility)
- **MUST** design code to be unit testable (dependency injection)
- **MUST** separate business logic from I/O
- **MUST** remove dead code and duplication

### Readability
- **MUST** prefer maintainability over cleverness
- **MUST** use descriptive variable/function names
- **MUST** follow PEP 8 (Python) / ESLint rules (TypeScript)
- **MUST** run formatter and linter before committing
- **MUST** add comments for complex logic

**Naming Conventions:**
- Python: `snake_case` functions/variables, `PascalCase` classes
- TypeScript: `camelCase` functions/variables, `PascalCase` classes/types

### Type Safety
- **MUST** use type hints for all Python functions
- **MUST** use TypeScript (not JavaScript)
- **MUST** use `Decimal` for financial calculations
- **MUST** use Pydantic schemas for API bodies

### Error Handling
- **MUST** handle errors explicitly
- **MUST** add contextual logging for errors
- **MUST** validate all inputs

---

## 2. Documentation Comments

**MUST** include docstrings for all public functions, classes, modules.

**Python:**
```python
def calculate_amount(income: Decimal, rate: Decimal) -> Decimal:
    """
    Calculate savings amount.

    Args:
        income: Gross income amount.
        rate: Savings rate as decimal (0.10 = 10%).

    Returns:
        Calculated savings amount.

    Raises:
        ValueError: If inputs are negative.
    """
```

**TypeScript:**
```typescript
/**
 * Calculate savings amount.
 * @param income - Gross income amount
 * @param rate - Savings rate as decimal
 * @returns Calculated savings amount
 * @throws {Error} If inputs are negative
 */
```

---

## 3. Testing

### Requirements
- **MUST** write unit tests for all business logic
- **MUST** write tests for all API handlers
- **MUST** achieve 80% coverage for business logic
- **MUST** run tests before committing

### Bug Fixes
- **MUST** add failing regression test first
- **MUST** then implement the fix

### Design
- **MUST** use dependency injection for mocking
- **MUST** mock external APIs in tests
- **MUST** test edge cases and error conditions

**Naming:** `test_<function>_<scenario>_<expected_result>`

---

## 4. Security

### Secrets
- **MUST** never commit secrets to code
- **MUST** use environment variables
- **MUST** use GCP Secret Manager in production
- **MUST** add `.env` to `.gitignore`

### Data Protection
- **MUST** store only reference IDs (Stripe, Clerk)
- **MUST** never log sensitive data
- **MUST** mask account numbers (show last 4 only)

### Webhooks
- **MUST** verify signatures before processing
- **MUST** implement idempotency
- **MUST** reject invalid signatures

---

## 5. Logging

- **MUST** use structured JSON logging (structlog)
- **MUST** include context IDs: `user_id`, `goal_id`, `transaction_id`
- **MUST** use appropriate levels: ERROR, WARNING, INFO, DEBUG

```python
logger.info(
    "transfer_completed",
    user_id=str(user.id),
    goal_id=str(goal.id),
    amount=float(amount)
)
```

---

## 6. Architecture

### Project Structure
- **MUST** follow: `/apps/mobile`, `/apps/api`, `/packages/shared`
- **MUST** place shared code in `/packages/shared`

### Financial Rules
- **MUST** use `Decimal` for all monetary values
- **MUST** round to 2 decimals for display only
- **MUST** validate financial inputs

### API Design
- **MUST** version endpoints (`/api/v1/...`)
- **MUST** use consistent error format
- **MUST** validate with Pydantic

---

## Quick Checklist

- [ ] Docstrings with Args, Returns, Raises
- [ ] Descriptive variable names
- [ ] Type hints on all functions
- [ ] Unit tests for new code
- [ ] No secrets in code
- [ ] Structured logging with context
- [ ] Decimal for financial calculations
- [ ] CONTEXT.md change log updated