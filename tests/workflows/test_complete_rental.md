# Complete Rental Page — User Journeys

## Happy Paths

### Complete a rental (no items left behind)

1. Editor user navigates to the Complete Rental page
2. User selects an in-progress rental from the dropdown
3. User fills in return date, return time, return location, and staff name
4. User checks the "Deposit received" checkbox
5. User clicks Submit
6. Rental is marked as completed and a confirmation is shown

### Complete a rental (with items left behind)

1. Editor user navigates to the Complete Rental page
2. User selects an in-progress rental that has items left behind recorded
3. User fills in return details and staff name
4. User checks "Deposit received" and confirms the items left behind checkbox
5. User clicks Submit
6. Rental is marked as completed

## Edge Cases

### No in-progress rentals

1. Editor user navigates to the Complete Rental page
2. No rentals are currently in-progress
3. Rental selector is empty
4. User cannot proceed

### Deposit not confirmed

1. User selects a rental and fills in return details
2. User does not check the "Deposit received" checkbox
3. Submit button remains disabled
4. Rental cannot be completed until deposit is confirmed

### Items left behind not confirmed

1. User selects a rental with items left behind
2. User checks "Deposit received" but does not confirm the items left behind checkbox
3. Submit button remains disabled

### API error on submit

1. User completes the form and clicks Submit
2. API returns an error
3. Error message is displayed
4. Rental status is not changed

### Non-editor user

1. Non-editor authenticated user attempts to access the page
2. Page is not visible in the navigation and cannot be accessed
