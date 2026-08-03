class AnytypeBuilder:
    """Placeholder builder for converting parsed notes into Anytype-ready objects."""

    def __init__(self, note=None):
        self.note = note

    def build(self, note=None):
        note = note or self.note
        if note is None:
            return {}

        return {
            "id": getattr(note, "id", ""),
            "title": getattr(note, "title", ""),
            "content": getattr(note, "body", ""),
            "labels": [label.name for label in getattr(note, "labels", [])],
        }
