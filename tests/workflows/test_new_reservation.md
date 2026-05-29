# New Reservation Page — User Journeys

## Happy Paths

### Create a reservation under capacity

1. Admin user navigates to the New Reservation page
2. User optionally expands the availability chart to check current counts vs. limits
3. User selects reservation date, device type, and location
4. User enters renter name and phone number
5. User enters reservation time
6. User optionally adds notes
7. User clicks Submit
8. Reservation is created with a pending or confirmed status

### Create a reservation at or over capacity (waitlist)

1. Admin user fills out the reservation form for a date/device type that is at or over the limit
2. User clicks Submit
3. Reservation is created with a waitlisted status
4. A notification or label indicates the reservation is waitlisted

### View availability before creating

1. Admin user opens the availability expander at the top of the page
2. Chart displays current reservation counts vs. configured limit for each device type
3. User uses this information to decide whether to proceed

## Edge Cases

### Missing required field

1. User fills out the form but leaves a required field blank (e.g., name, phone, date)
2. Submit button is disabled or a validation error is shown
3. Reservation is not created

### API error on submit

1. User completes the form and clicks Submit
2. API returns an error
3. Error message is displayed
4. Reservation is not created

### Non-admin user

1. Non-admin authenticated user attempts to access the page
2. Page is not visible in the navigation and cannot be accessed
