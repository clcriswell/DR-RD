# Erasure Workflow

1. **Preview** – operators identify the subject (email, user id, etc.) and run a
   preview to estimate impact across stores.
2. **Grace period** – requests remain in a soft-delete state for the configured
   `soft_delete_window_days` allowing cancellation.
3. **Execute** – after the window, data is hard-deleted where permitted and
   redaction events are appended to audit and provenance logs. Receipts capture
   the files touched.
4. **Rollback** – if needed, restore from offline backups using the receipt as a
   guide.
