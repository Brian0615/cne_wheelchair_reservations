# View Rentals Page — User Journeys

## Happy Paths

### View rentals for today (default)

1. Authenticated user navigates to the View Rentals page
2. Page defaults to today's date
3. Rentals for today are fetched and displayed in a table

### View rentals for a specific date

1. User selects a different date using the date picker
2. Page fetches rentals for the selected date
3. Rental table updates to show results for the new date

## Edge Cases

### No rentals on selected date

1. User selects a date with no rental records
2. Empty state is displayed (no table rows or a "no rentals" message)
3. No error is thrown

### API unavailable

1. User selects a date but the API is unreachable
2. An error message is displayed
3. Page does not crash
