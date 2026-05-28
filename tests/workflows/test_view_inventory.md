# View Inventory Page — User Journeys

## Happy Paths

### View full inventory

1. Authenticated user navigates to the View Inventory page
2. Full inventory is fetched from the API
3. Inventory summary charts are displayed for both scooters and wheelchairs
4. Detailed inventory tables show device status per location for each device type

## Edge Cases

### No devices in inventory

1. User navigates to the View Inventory page with an empty inventory
2. Charts and tables reflect zero counts or show an empty state
3. A message is shown directing the user to the Manage Inventory page (admin only)

### API error loading inventory

1. User navigates to the View Inventory page but the API is unreachable
2. An error message is displayed
3. Page does not crash
