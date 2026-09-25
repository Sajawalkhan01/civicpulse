# Deliberate Merge Conflict Evidence & Resolution
# Reference: Assignment Rubric Section A (150 Marks Specification)

## 1. Conflict Description
A deliberate merge conflict was staged on core domain code in `backend/app/domain/models.py` by introducing competing schema enhancements on two parallel branches:
- **`conflict/branch-a`:** Added comprehensive OpenAPI schema `description` attributes and docstrings to `ComplaintCreate`.
- **`conflict/branch-b`:** Modified `ComplaintCreate` with concise `title` tags and inline comments.

## 2. Merge Attempt & Conflict Markers
Executing `git merge conflict/branch-a` inside `conflict/branch-b` generated the following git output:
```text
Auto-merging backend/app/domain/models.py
CONFLICT (content): Merge conflict in backend/app/domain/models.py
Automatic merge failed; fix conflicts and then commit the result.
```

### Raw Conflict Markers in `backend/app/domain/models.py`:
```python
class ComplaintCreate(BaseModel):
<<<<<<< HEAD
    # Validated inbound complaint request model
    text: str = Field(..., min_length=10, max_length=2000, title="Complaint Text")
    location: str = Field(..., min_length=3, max_length=200, title="Civic Location")
    reporter_contact: str | None = Field(default=None, title="Contact Info")
=======
    """Citizen complaint payload submitted via public web intake form."""
    text: str = Field(min_length=10, max_length=2000, description="Raw complaint narrative in English or Urdu-English")
    location: str = Field(min_length=3, max_length=200, description="Civic geographic location description")
    reporter_contact: str | None = Field(default=None, description="Optional phone or email address for citizen follow-up")
>>>>>>> conflict/branch-a
```

## 3. Resolution Decision & Why the Winning Version Won
We resolved the conflict in favor of the **`conflict/branch-a`** implementation (while merging the explicit `title` attributes):
```python
class ComplaintCreate(BaseModel):
    """Citizen complaint payload submitted via public web intake form."""
    text: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        title="Complaint Text",
        description="Raw complaint narrative in English or Urdu-English"
    )
    location: str = Field(
        ...,
        min_length=3,
        max_length=200,
        title="Civic Location",
        description="Civic geographic location description"
    )
    reporter_contact: str | None = Field(
        default=None,
        title="Contact Info",
        description="Optional phone or email address for citizen follow-up"
    )
```

### Why this version won (2-4 sentences):
The `conflict/branch-a` version provided superior API contract transparency by populating detailed `description` fields, which automatically surface in FastAPI's Swagger UI (`/docs`) and client TypeScript generation. Merging the explicit `title` definitions from Branch B with Branch A's descriptive documentation produces the richest developer ergonomics without sacrificing Pydantic v2 validation strictness. This resolved version enhances both client-side form validation and OpenAPI schema compliance while maintaining backward compatibility with all unit tests.
