# Reservation Availability Page — User Journeys

## Happy Paths

### View availability (all authenticated users)

1. Authenticated user navigates to the Reservation Availability page
2. Page loads current reservation counts and limits for each device type
3. Charts display current reservations vs. the configured limit per device type

### Update reservation limit (admin only)

1. Admin user navigates to the Reservation Availability page
2. Admin expands the collapsible section for a device type
3. Admin enters a new limit value (minimum 0) in the number input
4. Admin clicks the Update button
5. Success toast message is shown
6. Chart updates to reflect the new limit

## Edge Cases

### Non-admin user

1. Non-admin authenticated user navigates to the page
2. Availability charts are visible
3. Update controls (collapsible section and number input) are not shown

### Admin sets limit to 0

1. Admin expands the section and enters 0 as the limit
2. Admin clicks Update
3. Limit is set to 0 — no new reservations can be created for that device type

### API error fetching settings

1. User navigates to the page but the settings API call fails
2. An error or fallback state is displayed
3. Page does not crash
