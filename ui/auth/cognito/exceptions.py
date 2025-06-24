class TokenVerificationException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class CognitoAuthenticationError(Exception):
    """
    Custom exception for Cognito authentication errors.

    Attributes:
        message (str): The error message describing the authentication issue.
    """

    def __init__(self, message: str):
        """
        Initializes the CognitoAuthenticationError with a specific error message.

        Args:
            message (str): The error message.
        """
        super().__init__(message)
        self.message = message
