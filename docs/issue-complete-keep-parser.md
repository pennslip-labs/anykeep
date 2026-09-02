# Complete Google Keep Takeout Parsing

## Context

The current parser handles basic note fields from Google Takeout JSON, but does not yet cover the full Keep export format described in the project documentation.

## Missing behavior

- Parse checklist items, including item text and checked state.
- Parse rich text, annotations, and other supported content metadata.
- Discover and associate image, drawing, and audio attachments with notes.
- Extract or expose media files for downstream Anytype uploads.
- Preserve relevant unknown/raw Keep fields so data is not silently discarded.
- Validate malformed JSON and report which file failed.
- Handle partially written or incomplete ZIP archives safely.
- Make ZIP path matching robust for alternate Takeout directory layouts.
- Calculate stable SHA256 hashes from the source JSON files for deduplication, rather than hashing the normalized note dictionary.

## Watcher integration

The directory watcher currently processes an archive on its `created` event. Downloads may still be writing at that point. The watcher should wait for the file to become stable or retry on subsequent modifications before parsing, while retaining failed archives for later retry.

## Acceptance criteria

- Complete Keep notes round-trip through parsing without losing supported fields.
- Attachments are discoverable and mapped to their owning notes.
- Invalid or incomplete input produces actionable errors and does not delete the source archive.
- Re-importing an unchanged source file is skipped using its source-content hash.
- Tests cover checklists, metadata, attachments, malformed input, alternate ZIP layouts, and incomplete downloads.
- The watcher processes only stable archives and cleans them up only after the full ingestion pipeline succeeds.
