from typing import Any, List, Set

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

    def get_current_user_groups(self) -> List[str]:
        """
        Retrieves the groups of the currently authenticated user.

        This method must be implemented by subclasses to return the groups
        of the user currently logged in. If no user is authenticated, the
        method should handle this scenario appropriately.

        Returns:
            List[str]: A list of groups for the currently authenticated user.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement get_current_user_groups method")

    def is_admin_user(self) -> bool:
        """
        Checks if the current user is an admin.

        This method must be implemented by subclasses to provide the logic
        for determining whether a user is an admin.

        Returns:
            bool: True if the user is an admin, False otherwise.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement is_admin_user method")

    def is_editor_user(self) -> bool:
        """
        Checks if the current user is an editor.

        This method must be implemented by subclasses to provide the logic
        for determining whether a user is an editor.

        Returns:
            bool: True if the user is an editor, False otherwise.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement is_editor_user method")

    def is_display_user(self) -> bool:
        """
        Checks if the current user is a display-only (TV/kiosk) user.

        This method must be implemented by subclasses to provide the logic
        for determining whether a user holds the display-only role.

        Returns:
            bool: True if the user is a display-only user, False otherwise.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement is_display_user method")

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

    def restore_session(self) -> bool:
        """
        Attempt to silently restore the session from persistent storage (e.g. cookies)
        without rendering any login UI.

        The default implementation performs no restoration and simply reports the current
        authentication state. Subclasses that support persistent sessions should override
        this to re-hydrate the session before any pages are rendered.

        Returns:
            bool: True if a session is active after the attempt, False otherwise.
        """
        return self.is_authenticated()

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

    def _on_logout(self):
        """
        Static method to handle logout actions.

        Can be overridden by subclasses to clear session state or perform other
        logout-related tasks.
        """

    @staticmethod
    def _clear_session_state(keep_keys: Set[str] = None):
        """
        Clears the Streamlit session state.

        This method can be used to reset the session state, typically after a user logs out.
        """
        if keep_keys is None:
            keep_keys = set()
        keep_keys.add("authenticator")

        for key, _ in st.session_state.items():
            if key not in keep_keys:
                del st.session_state[key]
