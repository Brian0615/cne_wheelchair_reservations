# Manage Rental Page — User Journeys

## Happy Paths

### Download rental form PDF

1. Editor user navigates to the Manage Rental page
2. User selects a rental from the dropdown (any status)
3. Rental details are displayed
4. User clicks the Download button
5. PDF rental form is downloaded

### Change assigned device

1. Editor user selects a rental from the dropdown
2. User opens the Change Device section
3. User selects the new location from the location dropdown
4. Available device IDs at that location are populated
5. User selects a new device ID
6. User enters staff name
7. User clicks Submit
8. Device is reassigned and a confirmation is shown

## Edge Cases

### No available devices at selected location

1. User selects a rental and opens the Change Device section
2. User selects a location where no devices are available
3. Device ID dropdown is empty
4. User cannot submit until a device becomes available at another location

### API error downloading PDF

1. User clicks Download
2. API returns an error
3. Error message is displayed
4. No file is downloaded

### API error changing device

1. User fills in change device form and clicks Submit
2. API returns an error
3. Error message is displayed
4. Device assignment is unchanged

### Non-editor user

1. Non-editor authenticated user attempts to access the page
2. Page is not visible in the navigation and cannot be accessed
