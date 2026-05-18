# New Rental Page — User Journeys

## Happy Paths

### Create a walk-in rental

1. Editor user navigates to the New Rental page
2. User selects rental date, pickup time, pickup location, and device type
3. User selects "Walk-in" (no reservation)
4. Available device IDs are populated in the device dropdown
5. User selects a device ID
6. User fills in renter information (name, phone, address, city, province, postal code, country)
7. User checks the ID Verified checkbox
8. User fills in payment information (fee and deposit methods and amounts)
9. User enters staff name
10. User clicks Submit
11. Rental is created successfully and a confirmation is shown

### Create a rental linked to a reservation

1. Editor user navigates to the New Rental page
2. User selects the rental date, pickup time, pickup location, and device type
3. Existing reservations for that date/type/location are populated in the reservation dropdown
4. User selects the customer's reservation from the dropdown
5. Renter information is pre-filled from the reservation
6. User selects an available device ID
7. User checks the ID Verified checkbox and fills in payment info and staff name
8. User clicks Submit
9. Rental is created and the linked reservation status is updated

## Edge Cases

### Missing required field

1. User fills out the form but leaves a required field blank
2. Submit button is disabled or a validation error is shown
3. Rental is not created

### ID not verified

1. User fills out the form but does not check the ID Verified checkbox
2. Submit button remains disabled
3. Rental is not created until the checkbox is checked

### No available devices for selected date/type/location

1. User selects a date, device type, and location
2. All devices for that combination are already rented out
3. Device dropdown is empty
4. User cannot proceed until a device becomes available

### API error on submit

1. User completes the form and clicks Submit
2. API returns an error (e.g., device already rented)
3. An error message is displayed
4. User remains on the form and can correct the issue

### Non-editor user

1. Non-editor authenticated user attempts to access the page
2. Page is not visible in the navigation and cannot be accessed
