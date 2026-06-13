from abc import ABC, abstractmethod
from typing import Optional

import extra_streamlit_components as stx
import streamlit as st
from pydantic import ValidationError

from common.logger import initialize_logger
from ui.auth.cognito.credentials import Credentials

logger = initialize_logger()


class CognitoAuthCookieManagerBase(ABC):
    """Base class for cognito authenticator cookie managers."""

    @abstractmethod
    def set_credentials(self, credentials: Credentials) -> None:
        """Saves credentials to cookies."""

    @abstractmethod
    def load_credentials(self) -> Optional[Credentials]:
        """Loads credentials from cookies."""

    @abstractmethod
    def reset_credentials(self) -> None:
        """Clears cookie credentials."""


class CognitoAuthCookieManagerNoop(CognitoAuthCookieManagerBase):
    """Dummy cognito authenticator cookie manager to be used when the authenticator does not
    wish to save credentials to cookies."""

    def set_credentials(self, credentials: Credentials) -> None:
        pass

    def load_credentials(self) -> Optional[Credentials]:
        return None

    def reset_credentials(self) -> None:
        pass


class CognitoAuthCookieManager(CognitoAuthCookieManagerBase):
    """Cognito authenticator cookie manager that saves credentials to browser cookies."""

    def __init__(self) -> None:
        # The extra_streamlit_components widget renders a zero-height iframe (and injects
        # spacing into the page) as soon as it is constructed. Reads now use
        # st.context.cookies, so the widget is only needed to write/delete cookies. Create
        # it lazily so normal page loads and refreshes never render it -- otherwise it
        # leaves empty space at the top of every page.
        self._cookie_manager: Optional[stx.CookieManager] = None

    @property
    def cookie_manager(self) -> stx.CookieManager:
        if self._cookie_manager is None:
            self._cookie_manager = stx.CookieManager()
        return self._cookie_manager

    def set_credentials(self, credentials: Credentials) -> None:
        self.cookie_manager.set("id_token", credentials.id_token, key="set_id_token")
        self.cookie_manager.set("access_token", credentials.access_token, key="set_access_token")
        self.cookie_manager.set("refresh_token", credentials.refresh_token, key="set_refresh_token")
        self.cookie_manager.set("expires_in", credentials.expires_in, key="set_expires_in")
        self.cookie_manager.set("token_type", credentials.token_type, key="set_token_type")

    def load_credentials(self) -> Optional[Credentials]:
        # Read from the request cookies, which are available synchronously on the very
        # first script run of a session (e.g. after a page refresh). The cookie component
        # (used for set/delete) only returns its values after a browser round-trip, so
        # relying on it here would force an extra rerun and briefly flash the login page.
        cookies = dict(st.context.cookies)
        try:
            return Credentials(**cookies)
        except ValidationError:
            return None

    def reset_credentials(self) -> None:
        def delete_cookie(name: str) -> None:
            key = "delete_" + name
            if key in st.session_state:
                return
            try:
                self.cookie_manager.delete(name, key=key)
                logger.info("deleted cookie: %s", name)
            except KeyError:
                logger.warning("Requested to delete non existing cookie: %s", name)

        logger.info("reset_credentials start")
        delete_cookie("id_token")
        delete_cookie("access_token")
        delete_cookie("refresh_token")
        delete_cookie("expires_in")
        delete_cookie("token_type")
        logger.info("reset_credentials end")
