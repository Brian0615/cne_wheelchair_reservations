from typing import Dict, Any

from pydantic import BaseModel, Extra, Field


class Credentials(BaseModel, extra=Extra.allow):
    """Temporary AWS Cognito credentials."""

    id_token: str = Field(..., min_length=1)
    access_token: str = Field(..., min_length=1)
    refresh_token: str = Field(..., min_length=1)
    expires_in: int
    token_type: str = Field(..., min_length=1)

    @classmethod
    def from_tokens(cls, tokens: Dict[str, Any]) -> 'Credentials':
        """Creates credentials from AWSSRP authentication response."""
        res = tokens["AuthenticationResult"]
        return cls(
            id_token=res["IdToken"],
            access_token=res["AccessToken"],
            refresh_token=res["RefreshToken"],
            expires_in=res["ExpiresIn"],
            token_type=res["TokenType"],
        )
