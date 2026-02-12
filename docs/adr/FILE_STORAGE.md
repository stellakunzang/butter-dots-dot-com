# ADR-015: File Storage Strategy

**Date**: 2026-02-09  
**Status**: Decided

## Context

Need to store:

1. User-uploaded PDF files (input)
2. Annotated PDF files with errors marked (output)

Options: Database BLOBs, Local filesystem, Cloud storage (S3/R2)

## Decision

**MVP**: Local filesystem with Docker volumes  
**Production**: Migrate to S3/Cloudflare R2

## Implementation

**File Structure**:

```
uploads/
  {job_id}/
    original.pdf
results/
  {job_id}_annotated.pdf
```

**Database Schema** (stores paths, not files):

```sql
file_path TEXT        -- /app/uploads/{job_id}/original.pdf
result_path TEXT      -- /app/results/{job_id}_annotated.pdf
```

**Docker Volumes**:

```yaml
volumes:
  - ./uploads:/app/uploads
  - ./results:/app/results
```

## Rationale

**Why Local for MVP**:

- Zero external dependencies (works offline in demo)
- Fast iteration (no cloud SDK/auth setup)
- Reliable demo (no network/API issues)
- Focus on core spell-checking algorithm
- Shows pragmatic MVP thinking

**Why NOT Database BLOBs**:

- Poor performance for large files
- Bloats database and backups
- Harder to serve files directly
- Generally an anti-pattern

**Why NOT S3/R2 Now**:

- Adds setup time
- Requires cloud account and credentials
- Adds failure points during demo
- Can abstract and migrate later

## Migration Path to Production

When ready for production, implement storage abstraction:

```python
# app/storage/base.py
class FileStorage(ABC):
    @abstractmethod
    async def save(self, file, path): pass

    @abstractmethod
    async def get(self, path): pass

# app/storage/local.py
class LocalFileStorage(FileStorage):
    # Current implementation
    ...

# app/storage/s3.py
class S3FileStorage(FileStorage):
    # S3/R2 implementation
    ...
```

Swap via config:

```python
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")  # or "s3"
```

**Benefits of S3/R2 in Production**:

- Unlimited scalability
- CDN integration (fast downloads globally)
- Automatic backups and versioning
- No disk space management
- Multi-region replication

## Interview Talking Points

> "For the MVP, I used local filesystem storage with Docker volumes. This let me
> focus on the spell-checking algorithm without cloud setup overhead. The file
> operations are abstracted behind a service layer with a clear interface, so
> migrating to S3 or Cloudflare R2 in production would be straightforward—just
> swap the implementation without touching the API layer. This demonstrates MVP
> thinking: defer infrastructure optimization, focus on core value first."

**Shows**:

- MVP vs production trade-offs
- Knowing when to defer optimization
- Design for future migration (abstraction)
- Pragmatic engineering decisions
- Interview-focused priorities
