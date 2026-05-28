# Home Page — User Journeys

## Happy Paths

### View today's activity (rentals and reservations exist)

1. Authenticated user navigates to the Home page
2. Page loads today's reservations and rentals from the API
3. User sees indicator charts per location for both device types (wheelchair and scooter)
4. User sees tabbed tables of today's reservations and rentals, separated by device type

### Filter by device type

1. User is on the Home page with data loaded
2. User selects a specific device type filter (Scooter or Wheelchair)
3. Charts and tables update to show only the selected device type

## Edge Cases

### No rentals or reservations today

1. User navigates to the Home page on a day with no activity
2. Charts and tables reflect zero counts
3. Empty state or zero-value indicators are displayed without errors

### API unavailable

1. User navigates to the Home page but the API is unreachable
2. An error message or empty state is displayed
3. Page does not crash
