class UniqueViolation(ValueError):
    """Exception raised when a unique constraint is violated."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
