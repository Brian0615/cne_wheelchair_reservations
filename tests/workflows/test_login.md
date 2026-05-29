# Login Page — User Journeys

## Happy Paths

### Successful login

1. User opens the app and is presented with the login page
2. User enters valid username and password
3. User clicks Login
4. Authentication succeeds → user is redirected to the Home page

### Already logged in

1. User navigates to the login page while already authenticated
2. Page shows current username and a Logout button
3. User can navigate to other pages via the sidebar

### Log out

1. Authenticated user is on any page
2. User clicks Logout
3. Session is cleared → user is redirected back to the login page

## Edge Cases

### Wrong password

1. User enters a valid username but incorrect password
2. User clicks Login
3. Error message is displayed on the login page
4. User remains on the login page

### Wrong username

1. User enters a username that does not exist
2. User clicks Login
3. Error message is displayed on the login page
4. User remains on the login page

### Empty credentials

1. User clicks Login without entering a username or password
2. Validation prevents submission or an error message is shown
3. User remains on the login page
