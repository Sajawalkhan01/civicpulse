# Engineering Notes

## Data layer

- `ix_complaints_status_priority` (composite index on `status, priority`) serves the filtered listing in `ComplaintRepository.list()`, which the admin queue view uses to pull complaints by `status` and/or `priority` (e.g. all `open` + `high` priority complaints) without a sequential scan.
- `ix_complaints_created_at` serves the `ORDER BY created_at DESC` clause in `ComplaintRepository.list()`, which paginates complaints newest-first by default.
