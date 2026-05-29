# Manage Inventory Page — User Journeys

## Happy Paths

### Add devices

1. Admin user navigates to the Manage Inventory page
2. User clicks the Add button for a device type (scooter or wheelchair)
3. Add dialog opens
4. User enters the number of devices and relevant details
5. User confirms the dialog
6. Devices are added and the inventory table updates

### Update device status

1. Admin user clicks the Update button for a device type
2. Update dialog opens
3. User selects one or more devices
4. User chooses a new status (e.g., available, maintenance, broken)
5. User confirms the dialog
6. Device statuses are updated and the inventory table reflects the changes

### Transfer devices to another location

1. Admin user clicks the Transfer button for a device type
2. Transfer dialog opens
3. User selects one or more devices to transfer
4. User selects the destination location
5. User confirms the dialog
6. Devices are moved to the new location and the inventory table updates

### Remove devices

1. Admin user clicks the Remove button for a device type
2. Remove dialog opens
3. User selects one or more devices to remove
4. User confirms the dialog
5. Devices are removed and the inventory table updates

## Edge Cases

### No devices in inventory

1. Admin user navigates to the Manage Inventory page with an empty inventory
2. Inventory tables are empty
3. Add button is the only meaningful action available
4. Update, Transfer, and Remove dialogs have no devices to select

### API error on any inventory action

1. User completes a dialog and confirms
2. API returns an error
3. Error message is displayed
4. Inventory state is unchanged

### Non-admin user

1. Non-admin authenticated user attempts to access the page
2. Page is not visible in the navigation and cannot be accessed
