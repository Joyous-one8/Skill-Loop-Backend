from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, SecurityScopes
from config import get_settings


class UnauthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Requires authentication"
        )


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class VerifyToken:
    def __init__(self):
        self.config = get_settings()
        jwks_url = f'https://{self.config.auth0_domain}/.well-known/jwks.json'
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    async def verify(
        self,
        security_scopes: SecurityScopes,
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer())
    ):
        if token is None:
            raise UnauthenticatedException()

        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(
                token.credentials
            ).key
        except jwt.exceptions.PyJWKClientError as error:
            raise UnauthorizedException(str(error))
        except jwt.exceptions.DecodeError as error:
            raise UnauthorizedException(str(error))

        try:
            # Try to decode with API audience first
            payload = jwt.decode(
                token.credentials,
                signing_key,
                algorithms=self.config.auth0_algorithms,
                audience=self.config.auth0_api_audience,
                issuer=self.config.auth0_issuer,
            )
        except jwt.exceptions.InvalidAudienceError:
            # If API audience fails, try with Client ID (for id_token)
            try:
                payload = jwt.decode(
                    token.credentials,
                    signing_key,
                    algorithms=self.config.auth0_algorithms,
                    audience=self.config.auth0_client_id,
                    issuer=self.config.auth0_issuer,
                )
            except Exception as error:
                raise UnauthorizedException(f"Token validation failed: {str(error)}")
        except Exception as error:
            raise UnauthorizedException(str(error))

        return payload


auth = VerifyToken()
