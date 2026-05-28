# Manage Reservation Page — User Journeys

## Happy Paths

### Confirm a reservation

1. Admin user navigates to the Manage Reservation page
2. User selects a date and then selects a reservation from the dropdown
3. Reservation details are displayed in the form
4. User clicks the Confirm button
5. Reservation status is updated to confirmed

### Cancel a reservation

1. Admin user selects a date and reservation
2. User clicks the Cancel button
3. Reservation status is updated to cancelled

### Update reservation details

1. Admin user selects a date and reservation
2. User edits one or more editable fields (name, phone, time, location, notes)
3. Note: date and device type fields are disabled and cannot be changed
4. User clicks Submit
5. Reservation details are updated and a confirmation is shown

## Edge Cases

### Reservation already completed, picked up, or cancelled

1. User selects a reservation with a terminal status (picked up, completed, or cancelled)
2. Form fields are disabled — no edits can be made
3. Confirm and Cancel buttons are hidden or disabled

### No reservations on selected date

1. User selects a date with no reservations
2. Reservation selector is empty
3. Form does not render until a valid reservation is selected

### API error on confirm/cancel

1. User clicks Confirm or Cancel
2. API returns an error
3. Error message is displayed
4. Reservation status is unchanged

### API error on update

1. User edits fields and clicks Submit
2. API returns an error
3. Error message is displayed
4. Reservation details are unchanged

### Non-admin user

1. Non-admin authenticated user attempts to access the page
2. Page is not visible in the navigation and cannot be accessed
