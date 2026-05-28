# View Reservations Page — User Journeys

## Happy Paths

### View reservations for today (default)

1. Authenticated user navigates to the View Reservations page
2. Page defaults to today's date
3. Reservations for today are fetched and displayed in a table
4. PDF download button is enabled

### View reservations for a specific date

1. User selects a different date using the date picker
2. Page fetches reservations for the selected date
3. Table updates with results for the new date

### Download reservations as PDF

1. User selects a date that has reservations
2. PDF download button is enabled
3. User clicks the download button
4. A PDF file is downloaded with a date-stamped filename (YYYY-MM-DD format)

## Edge Cases

### No reservations on selected date

1. User selects a date with no reservations
2. Empty state is displayed
3. PDF download button is disabled

### API unavailable

1. User selects a date but the API is unreachable
2. An error message is displayed
3. PDF download button is disabled or hidden
4. Page does not crash
