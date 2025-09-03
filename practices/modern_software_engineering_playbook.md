# Modern Software Engineering Playbook

This document compiles key ideas from _Modern Software Engineering_ (Dave Farley) into a **situation-based playbook** for professional software engineers. It also includes a **conceptual map** for quick reference, and team-level applications.

---

# Part I: Playbook by Situation

## 1. Starting a New Feature

- **Principles**: Short feedback cycles, incremental delivery, working software over speculation.
- **Approach**:
  - Write acceptance criteria as executable tests (BDD/TDD style).
  - Decompose feature into smallest independent increments that can run in production.
  - Automate validation early (unit tests, integration tests).
  - Merge and deploy continuously to avoid “big bang” risk.
- **Outcome**: Progress is visible, risks are surfaced quickly, and the feature evolves empirically.
- **Example**: A “dark mode” toggle delivered incrementally behind a feature flag.

---

## 2. Fixing Bugs or Production Incidents

- **Principles**: Empirical feedback, hypothesis-driven debugging.
- **Approach**:
  - Reproduce the bug in a test that fails.
  - Form hypotheses and run experiments (instrument logs, metrics, feature flags).
  - Fix only with a green test proving resolution.
  - Deploy quickly and safely (blue/green, canary).
- **Outcome**: Confidence that the issue won’t regress, improved observability for future.
- **Example**: A 500 error on image upload reproduced with failing test → fix added resizing on large files → deployed via canary.

---

## 3. Refactoring and Technical Debt

- **Principles**: Keep the system malleable through continual improvement.
- **Approach**:
  - Refactor in small steps with a green test suite.
  - Prioritize areas of highest change or risk.
  - Apply evolutionary design: keep architecture “just enough” but adaptive.
  - Use CI/CD to ensure refactors flow safely to production.
- **Outcome**: Codebase remains understandable and adaptable, reducing long-term costs.
- **Example**: Extract `EmailNotificationService` out of a 2,000-line UserService class with tests guarding behavior.

---

## 4. Design and Architecture Decisions

- **Principles**: Evolutionary architecture, defer irreversible choices, validate empirically.
- **Approach**:
  - Model decisions as hypotheses: “We believe X architecture will improve Y; we’ll know we’re right if Z metric improves.”
  - Prefer small, composable services/modules over monolith rewrites unless data proves otherwise.
  - Document decisions lightly (ADR format), revisit regularly.
- **Outcome**: System grows through validated learning, not premature optimization.
- **Example**: Spike RabbitMQ vs cron jobs → data shows RabbitMQ reduces latency 30% → adopt incrementally.

---

## 5. Collaboration and Code Review

- **Principles**: Fast feedback, knowledge sharing, collaborative problem-solving.
- **Approach**:
  - Keep PRs small and review within hours.
  - Review for learning, design alignment, and testing—not just style.
  - Use pair/mob programming for complex areas to accelerate feedback.
- **Outcome**: Shared ownership, fewer defects, consistent design practices.
- **Example**: Team enforces <200-line PRs with 24-hour SLA; rotates reviewers.

---

## 6. Continuous Delivery and Deployment

- **Principles**: Reduce batch size, automate everything, shorten cycle time.
- **Approach**:
  - Every commit triggers automated build, test, and deploy pipeline.
  - Feature flags allow incomplete features to be deployed safely.
  - Monitor deployment health with automated rollback if needed.
- **Outcome**: Safe, predictable flow of changes to production.
- **Example**: CI/CD with GitHub Actions builds Docker image, runs tests, and auto-deploys to staging/prod.

---

## 7. Testing Strategy

- **Principles**: Test pyramid, fast feedback, automate end-to-end flows.
- **Approach**:
  - High ratio of unit tests for speed, backed by integration and a thin layer of end-to-end.
  - Automate regression checks in CI.
  - Favor property-based or exploratory testing where input space is large.
- **Outcome**: Tests provide confidence and allow fearless iteration.
- **Example**: Checkout flow tested with 50+ unit tests, 10 integration, and 2 e2e tests.

---

## 8. Learning and Professional Growth

- **Principles**: Empiricism and continual learning.
- **Approach**:
  - Run retrospectives for yourself and your team.
  - Use spikes (time-boxed experiments) for new tools or tech.
  - Share learning via brown bags, documentation, or mentoring.
- **Outcome**: You evolve as fast as the system does; career growth is built on adaptability.
- **Example**: One-day spike with GraphQL → share findings in brown bag.

---

## 9. Interfacing with Product / Business

- **Principles**: Optimize for outcomes, not outputs.
- **Approach**:
  - Translate requirements into hypotheses: “If we deliver X, we expect Y behavior change.”
  - Use telemetry (analytics, A/B testing) to validate product choices.
  - Challenge scope by focusing on MVP and incremental delivery.
- **Outcome**: Engineering directly supports measurable business goals.
- **Example**: Build minimal SMS verification → track completion rate → iterate when adoption <60%.

---

## 10. Diagnosing Incidents in Untested Systems

- **Principles**: Empiricism, scientific method, short feedback loops, incremental improvement.
- **Approach**:
  1. **Observation** – Gather evidence (logs, metrics, user reports).
  2. **Hypothesis** – State a theory: “We believe X condition causes Y failure.”
  3. **Experiment** – Reproduce in a controlled environment; add logging or probes.
  4. **Validation** – Confirm or refute; fix with minimal, reversible change.
  5. **Improvement** – Capture bug as automated test; add monitoring/logging.
- **Outcome**: Incidents are diagnosed systematically, not by guesswork. Safety nets grow incrementally.
- **Example**: Cart >10 items causes crash → experiment reproduces → fix loop bounds → add integration test for 1–20 items.

---

# Part II: Conceptual Map (One-Liners)

- **Features** → Deliver in small, testable increments.
- **Bugs** → Reproduce with tests, fix empirically, deploy safely.
- **Refactoring** → Improve continuously with safety nets.
- **Architecture** → Treat decisions as experiments, evolve design.
- **Collaboration** → Feedback fast, share knowledge.
- **Delivery** → Automate, reduce batch size, deploy continuously.
- **Testing** → Layered automation, fast feedback.
- **Learning** → Reflect, experiment, share knowledge.
- **Product** → Frame work as hypotheses, measure outcomes.
- **Incidents (Untested Systems)** → Apply scientific method: observe, hypothesize, experiment, validate, improve.

---

# Part III: Team-Level Applications of Modern Software Engineering

## 1. Starting New Features as a Team

- **Practice**: Break epics into small stories; integrate with feature flags.
- **Example**: Search revamp split into slices: add UI, hook API, add filters → each deployed incrementally.

---

## 2. Fixing Bugs / Handling Incidents as a Team

- **Practice**: Blameless postmortems; rotating incident commander.
- **Example**: Checkout outage → one engineer leads, another documents hypotheses → retro adds health check.

---

## 3. Refactoring and Technical Debt

- **Practice**: Allocate “debt budget” (10–20% sprint capacity).
- **Example**: Team fixes duplicated validation while building new fields.

---

## 4. Design and Architecture Decisions

- **Practice**: Use lightweight ADRs.
- **Example**: Debate GraphQL vs REST → run 2-day spike → record in ADR → prototype one endpoint.

---

## 5. Collaboration and Code Review

- **Practice**: Small PRs, 24-hour SLA, rotate reviewers.
- **Example**: PRs average 200 lines; team enforces SLA; reviewers rotate for shared knowledge.

---

## 6. Continuous Delivery and Deployment

- **Practice**: Trunk-based development, shared CI/CD.
- **Example**: Everyone commits daily; CI deploys to staging/prod; team owns pipeline health.

---

## 7. Testing Strategy

- **Practice**: Shared test pyramid enforced in reviews.
- **Example**: Payments service with mostly unit tests, a few integration, 1–2 e2e flows.

---

## 8. Learning and Professional Growth

- **Practice**: Retros, brown bags, learning hours.
- **Example**: After adopting Docker, team shares learnings at Friday lunch; retro action item to write onboarding doc.

---

## 9. Interfacing with Product / Business

- **Practice**: Define success metrics with product.
- **Example**: Instead of “build SMS verification,” success = “70% users complete SMS.” Telemetry shows 40% → team iterates.

---

## 10. Diagnosing Incidents in Untested Systems

- **Practice**: Collaborative experiments during outages.
- **Example**: Legacy billing crash → hypotheses logged in doc → fix deployed → add first integration test for case.

---

# Team-Level Summary (Conceptual Map)

- **Features** → Slice epics, deploy behind flags.
- **Bugs** → Postmortems, rotate incident lead.
- **Refactoring** → Plan debt budget.
- **Architecture** → Use ADRs, run spikes.
- **Collaboration** → Small PRs, rotate reviewers.
- **Delivery** → Shared CI/CD, trunk-based dev.
- **Testing** → Enforce pyramid in reviews.
- **Learning** → Retros, brown bags, learning hours.
- **Product** → Define success metrics, measure outcomes.
- **Incidents** → Evidence-driven response, add safety nets.

---

# Part IV: Design Strategies

## 1. Modularity

### Strategies

- Break the system into **small, independent units** (modules, packages, services).
- Define **clear boundaries** around modules using interfaces or APIs.
- Organize modules around **business capabilities** rather than technical layers.
- Ensure modules can be **developed, tested, and deployed independently**.

### Practical Examples

- In a web application, separate modules for:
  - **User Authentication** (login, tokens).
  - **Product Catalog** (CRUD for items).
  - **Order Processing** (checkout, payment).
- Each module has its own tests and deploy pipeline. Changing “Product Catalog” doesn’t require redeploying the “User Authentication” module.

---

## 2. Cohesion

### Strategies

- Each module/class should have **one clear purpose**.
- Group related behavior and data together.
- Avoid “utility” modules that do many unrelated tasks.
- Strive for **high internal cohesion** (all parts of a module are strongly related).

### Practical Examples

- A `PaymentService` module:
  - Handles payment authorization and capture.
  - Does **not** send user emails (that belongs in `NotificationService`).
- Cohesion increases testability: unit tests for `PaymentService` focus only on payment logic.

---

## 3. Separation of Concerns

### Strategies

- Divide responsibilities into **distinct areas** to avoid overlap.
- Use layered architectures (UI, domain, data) or ports/adapters to separate logic.
- Make side-effects explicit and confined to certain modules.
- Keep core domain logic pure (without IO, frameworks, or UI code).

### Practical Examples

- In a microservice:
  - **API Layer**: Handles HTTP requests/responses.
  - **Domain Layer**: Contains business rules.
  - **Persistence Layer**: Handles database interactions.
- Adding caching only touches the **Persistence Layer**, without rewriting domain rules.

---

## 4. Information Hiding & Abstraction

### Strategies

- Hide implementation details behind stable interfaces.
- Provide abstractions that focus on **what** a module does, not **how** it does it.
- Avoid leaking private details across module boundaries.
- Use encapsulation: keep variables and internal logic private where possible.

### Practical Examples

- A `UserRepository` interface defines:
  - `getUserById(id)`
  - `saveUser(user)`
- Implementation details (SQL queries, ORMs, caching) are hidden.  
  The rest of the system depends only on the abstraction, not on whether it’s PostgreSQL or MongoDB.

---

## 5. Managing Coupling

### Strategies

- Prefer **loose coupling**: modules depend on each other’s interfaces, not implementations.
- Reduce **temporal coupling** (one module requiring another to run in a specific order).
- Use dependency inversion: higher-level modules depend on abstractions.
- Keep dependencies **explicit** and **minimized**.

### Practical Examples

- Using **message queues** (Kafka, RabbitMQ):
  - Order Service publishes “OrderPlaced” events.
  - Payment Service subscribes.  
    They are coupled only by the event schema, not direct calls.
- In code:
  - `OrderService` depends on a `PaymentGateway` interface, not on a specific Stripe or PayPal SDK.
  - Switching providers requires only updating the implementation, not the calling code.

---

# Summary Conceptual Map

- **Modularity** → Small, independent units aligned with business capabilities.
- **Cohesion** → Each unit has one clear responsibility.
- **Separation of Concerns** → Distinct layers/areas prevent overlap.
- **Information Hiding & Abstraction** → Expose “what,” hide “how.”
- **Managing Coupling** → Depend on abstractions, keep connections loose.

---

# Design Adherence Checklist

## 1) Modularity

- [ ] Does each module have a clearly defined public API (functions/classes/endpoints) documented in one place?
- [ ] Can the module be built/tested in isolation without building unrelated modules?
- [ ] Can the module be deployed (or versioned) independently from other modules?
- [ ] Do modules avoid importing each other’s internal (non-public) files or packages?
- [ ] Does a change to one module rarely require code changes in more than one other module?
- [ ] Are module boundaries aligned to business capabilities (not just technical layers)?
- [ ] Is there at most one reason to include this module as a dependency in other modules?
- [ ] Are circular dependencies between modules absent?

---

## 2) Cohesion

- [ ] Can you describe the module/class responsibility in a single sentence without “and”/“or”?
- [ ] Do all public functions of the module/class directly serve that single responsibility?
- [ ] Are data structures owned by the module used primarily by the module’s own behavior?
- [ ] Are there no “grab bag”/utility classes that mix unrelated behaviors?
- [ ] Does removing the module/class affect only features tied to its single purpose?
- [ ] Do functions in the class frequently use the same fields (high functional affinity)?
- [ ] Are workflows that span multiple responsibilities implemented across multiple modules (not crammed into one)?
- [ ] Is any “temporary” unrelated logic removed or relocated before merge?

---

## 3) Separation of Concerns

- [ ] Is UI/transport code free of domain/business rules?
- [ ] Is domain code free of IO (network, filesystem, DB) and framework annotations where practical?
- [ ] Are persistence concerns isolated behind repositories/gateways (no SQL in controllers/use-cases)?
- [ ] Are external integrations (HTTP clients/SDKs) wrapped behind interfaces/ports?
- [ ] Are cross-cutting concerns (logging, metrics, caching, auth) implemented via middleware/aspects/adapters rather than scattered?
- [ ] Does changing the database or cache layer _not_ require changes to domain logic?
- [ ] Does changing request/response shape at the edge _not_ require domain code changes?
- [ ] Are configuration and environment concerns isolated from business logic?

---

## 4) Information Hiding & Abstraction

- [ ] Are implementation details (private fields/helpers/SQL/SDK specifics) not exposed in public types or method signatures?
- [ ] Do public interfaces describe _what_ the component does, not _how_ it does it?
- [ ] Can you replace the implementation (e.g., swap DB/cache/provider) without changing callers?
- [ ] Are invariants enforced internally (cannot be violated by callers)?
- [ ] Are optional/experimental features hidden behind feature flags or internal APIs (not leaking to callers)?
- [ ] Do modules expose minimal surface area (no unused public methods/fields)?
- [ ] Are data transfer types (DTOs/events) stable and versioned when needed?
- [ ] Are error types/results abstracted (callers don’t depend on low-level exception classes)?

---

## 5) Managing Coupling

**General & Structural**

- [ ] Do modules depend on interfaces/abstractions rather than concrete implementations?
- [ ] Are there no compile-time circular dependencies between modules/packages?
- [ ] Is the dependency graph acyclic and directed “inward” toward stable domain abstractions?

**Temporal & Runtime**

- [ ] Can components start in any order without failing (no fragile startup sequencing)?
- [ ] Can services tolerate the absence or slowness of dependencies (timeouts/retries/fallbacks/circuit breakers)?
- [ ] Do background jobs/event handlers retry idempotently without duplicating side-effects?

**Data & Schema**

- [ ] Are event/message schemas backward compatible (additive changes, versioning when needed)?
- [ ] Do services avoid reaching into each other’s databases (no shared DB tables across services)?
- [ ] Are integration contracts tested (consumer/provider or end-to-end contract tests)?

**Change & Release**

- [ ] Can you release one module/service without forcing synchronized releases of others?
- [ ] Does a change in a low-level library rarely require changes in many dependents (fan-out contained)?
- [ ] Are feature toggles used to decouple code integration from feature exposure?

---

## Quick Self-Assessment

- **Excellent**: All or all but 1–2 items are **Yes** in each section.
- **Good**: Most are **Yes**, with clear tickets to address the **No** answers.
- **Risky**: Multiple **No** answers clustered in a section → prioritize refactoring there.

---
