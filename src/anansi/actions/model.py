"""Model based actions."""


class DeleteRecord:
    """DeleteRecord action."""

    def __init__(self, record: 'Model'=None, context: 'Context'=None):
        self.context = context
        self.record = record


class SaveRecord:
    """SaveRecord action."""

    def __init__(
        self,
        record: 'Model'=None,
        context: 'Context'=None,
    ):
        self.context = context
        self.record = record
