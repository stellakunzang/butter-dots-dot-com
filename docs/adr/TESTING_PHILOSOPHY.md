# ADR-014: Testing Philosophy and Strategy

**Date**: 2026-02-09  
**Status**: Decided

## Context

Need to establish testing practices for Tibetan Spellchecker MVP that:
- Demonstrates senior engineering discipline
- Supports TDD workflow
- Provides confidence for refactoring
- Doesn't over-engineer or slow down development

## Decision

**Approach**: Test-Driven Development (TDD) with pragmatic coverage

**Coverage Target**: 60-70% overall
- Core spell check logic: 90%+ (rules, engine, parser)
- API endpoints: 80%+
- UI components: 50%+ (critical paths only)

**Test Types**:
1. Unit Tests: Individual functions, classes, utilities
2. Integration Tests: API endpoints, database operations
3. E2E Tests: Critical user flows (defer to Phase 2)

**Tools**:
- Backend: pytest, httpx (test client), pytest-asyncio
- Frontend: Jest, React Testing Library

**CI**: GitHub Actions runs all tests on push/PR

## TDD Workflow

For each feature:
1. Write test first (red)
2. Implement minimal code to pass (green)
3. Refactor for quality (refactor)
4. Commit with test

## What to Test

**High Priority** (write tests first):
- Tibetan text normalization
- Syllable parsing
- Spelling rule validation
- Spell check engine
- API endpoints

**Medium Priority** (test alongside):
- Database models/queries
- PDF text extraction
- Error handling

**Low Priority** (test if time):
- UI components (critical flows only)
- Config/setup code
- Utility functions

## What NOT to Test

- Third-party libraries (trust pytest, FastAPI, etc.)
- Framework boilerplate
- Trivial getters/setters
- Mock-heavy tests with low value

## Rationale

TDD enforces design thinking upfront and provides regression safety for rapid iteration. Pragmatic coverage balances quality with delivery speed - appropriate for MVP.
