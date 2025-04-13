from typing import Any

import streamlit as st


class BaseAuthenticator:
    """
    A base class for implementing authentication in a Streamlit application.
    Subclasses must implement specific methods to provide custom authentication logic.
    """

    def __init__(self):
        """
        Initializes the BaseAuthenticator instance.

        If an authenticator object already exists in the Streamlit session state,
        it is reused. Otherwise, a new authenticator is initialized and stored
        in the session state.
        """
        if "authenticator" in st.session_state:
            self.authenticator = st.session_state["authenticator"]
        else:
            authenticator = self._initialize_authenticator()
            st.session_state["authenticator"] = authenticator
            self.authenticator = authenticator

    def _initialize_authenticator(self) -> Any:
        """
        Abstract method to initialize the authenticator.

        Subclasses must override this method to provide their own implementation.

        Returns:
            Any: An authenticator object.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement _initialize_authenticator method")

    def _load_config(self):
        """
        Placeholder method for loading configuration.

        Subclasses can override this method to load authentication-related configurations.
        """

    def get_current_user(self) -> str:
        """
        Retrieves the username of the currently authenticated user.

        This method must be implemented by subclasses to return the username
        of the user currently logged in. If no user is authenticated, the
        method should handle this scenario appropriately.

        Returns:
            str: The username of the currently authenticated user.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement get_current_user method")

    def is_authenticated(self) -> bool:
        """
        Checks if the user is currently authenticated.

        This method must be implemented by subclasses to provide the logic
        for determining whether a user is authenticated.

        Returns:
            bool: True if the user is authenticated, False otherwise.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement is_authenticated method")

    def login(self) -> bool:
        """
        Placeholder method for handling user login.

        Subclasses must override this method to implement their own login logic.

        Returns:
            bool: A boolean indicating whether the login was successful.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement login method")

    def render_logout(self):
        """
        Placeholder method for rendering a logout button or functionality.

        Subclasses must override this method to implement their own logout logic.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement render_logout method")

    @staticmethod
    def _on_logout(*args, **kwargs):
        """
        Static method to handle logout actions.

        Can be overridden by subclasses to clear session state or perform other
        logout-related tasks.
        """
