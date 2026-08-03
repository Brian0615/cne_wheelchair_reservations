# CNE Wheelchair Reservations Manual

Last updated: August 2, 2026 9:50:00 PM

## 1 Reservations

### 1.1 Creating a New Reservation

To create a new reservation:

1. Navigate to the **New Reservation** page
2. Fill in the form with the reservation information
3. Click **Submit**

To view the number of remaining reservations available for each day, expand the dropdown labelled
“View Reservation Availability” .

### 1.2 Updating an Existing Reservation

To modify an existing reservation:

1. Navigate to the **Manage Reservation** page
2. Select the date of the reservation
3. Select the reservation to be modified

After selecting the desired reservation, the following may be performed:

4. Confirm a reservation
    - Note: This option is only available for scooters
5. Cancel a reservation
6. Update information about the reservation

Notes:

- The reservation date and type (scooter/wheelchair) may not be modified. To do so, the reservation must be cancelled
  and a new reservation will need to be created.
- Any reservation that has been cancelled, picked up, or completed (i.e. returned) may not be modified.

### 1.3 Reservation Availability

To view the number of available or taken reservations, navigate to the **Reservation Availability** page.

On this page, users with the admin role may modify the maximum reservations allowed per day. Note that:

- The limit for wheelchair and scooter reservations can be set independently
- The limit is applied for all days – i.e. different limits cannot be set for different days
- If the reservation limit is reached, any new reservations will automatically be put on the waitlist. However, if the
  reservation limit is reduced, any prior reservations (even if above the limit) will not be modified

### 1.4 Reservation Status

Reservations are assigned one of the following statuses:

- Waitlisted
- Reserved
- Pending Confirmation
- Confirmed
- Picked Up
- Completed
- Cancelled

#### 1.4.1 Scooters

- Scooter reservations are automatically assigned the **Pending Confirmation** status when first created
- If there are no more available reservations, the reservation is assigned the **Waitlisted** status instead
- After calling to confirm a scooter reservation, the reservation can be marked as **Confirmed** using the
  **Manage Reservations** page
- When a rental for the reservation is created, the reservation status will automatically be updated to **Picked Up**
- When the rental is completed, the reservation status will automatically be updated to **Completed**

Below is a flowchart illustrating the reservation status process for a scooter reservation:

`Waitlisted -> Pending Confirmation -> Confirmed -> Picked Up -> Completed`

#### 1.4.2 Wheelchairs

- Wheelchair reservations are automatically assigned the **Reserved** status when first created
- If there are no more available reservations, the reservation is assigned the **Waitlisted** status instead
- When a rental for the reservation is created, the reservation status will automatically be updated to **Picked Up**
- When the rental is completed, the reservation status will automatically be updated to **Completed**

Below is a flowchart illustrating the reservation status process for a wheelchair reservation:

`Waitlisted -> Reserved -> Picked Up -> Completed`

## 2 Rentals

### 2.1 Creating a New Rental

To create a new rental:

1. Navigate to the **New Rental** page
2. Complete the following fields:
    - **Rental Date** – this field will default to the current date
    - **Pickup Time** – you may either enter a time or select a time from the dropdown
    - **Pickup Location** – select BLC or PG from the dropdown
    - **Rental Type** – select Scooter or Wheelchair from the dropdown
3. Once the first four fields are completed, you may fill in the remainder of the form:
    - Select the reservation:
        - For guests with a reservation, choose their reservation from the dropdown.
        - For guests without a reservation, select the **Walk In – No Reservation** option. This is the last option in
          the dropdown.
    - Select the scooter/wheelchair number
    - Fill in the renter information, and check the box once you’ve verified ID
    - Fill in payment information
    - Fill in your name under **Staff Name**, and list any items left behind by the renter
4. Once everything is complete, click **Submit** to start the rental.

After clicking **Submit**, you will see one of the following:

- **Success**: If all the information has been verified successfully, you will see a green success dialog.
    1. Click **Download** to download the rental form so it can be printed.
    2. Afterwards, click **Close** to return to the main page.
- **Error**: If there is missing or invalid information, you will see an error. Please correct any
  missing information and try to resubmit the form.

#### 2.1.1 Credit Card Deposits

Please use the paper credit card deposit slips to record credit card information. Do NOT include any credit card
information in the reservation system.

#### 2.1.2 Troubleshooting

- The remainder of the form will not appear unless the first four fields are filled
- You may need to scroll down to see all the fields
- If you accidentally close the Success pop-up without downloading the rental form, see the instructions in Section 2.4
  for a way to retrieve the rental form.

### 2.2 Modifying an Existing Rental

If a wheelchair or scooter needs to be swapped out during a rental, do the following:

1. Navigate to the **Manage Reservations** page
2. Select the date and the rental
    - The date will default to the current date
    - To select a rental, you may choose an option from the dropdown, or search by typing in one of the following:
        - The current wheelchair/scooter ID
        - The renter’s name
        - The rental ID found on the rental form
3. After selecting the rental, the option to update the wheelchair or scooter will appear. You will then need to:
    1. Select the current location from the dropdown
        - This does not need to be the same location as the pickup location
    2. Select the new wheelchair or scooter ID from the dropdown
    3. Enter your name under **Staff Name**
    4. Click **Update Wheelchair** or **Update Scooter**
        - This button will only be clickable if all the required fields are completed

Notes:

- The option to update a wheelchair / scooter will not appear if a rental is not selected
- The option to update a wheelchair / scooter will be disabled if the rental is already completed.

### 2.3 Completing a Rental

When a wheelchair or scooter rental is brought back, please complete the following:

1. Navigate to the **Complete Rental** page
2. Select the date and the rental
    - The date will default to the current date
    - To select a rental, you may choose an option from the dropdown, or search by typing in one of the following:
        - The current wheelchair/scooter ID
        - The renter’s name
        - The rental ID found on the rental form
3. After selecting the rental, the form to complete the rental will appear. You will then need to:
    1. Select the **Return Date** – the date will default to the current date
    2. Select or type in the **Return Time**
    3. Select the **Return Location**
    4. Enter your name under **Staff Name**
    5. Confirm by checking the boxes that the deposit, and any items left behind during the rental have been
       returned
    6. Click **Complete Rental**
        - This button will only be clickable if all the required fields are completed

### 2.4 Retrieving a Rental Form

To retrieve a rental form, complete the following:

1. Navigate to the **Manage Reservations** page
2. Select the date and the rental
    - The date will default to the current date
    - To select a rental, you may choose an option from the dropdown, or search by typing in one of the following:
        - The current wheelchair/scooter ID
        - The renter’s name
        - The rental ID found on the rental form
3. After selecting the rental, the option to download the rental form will appear. You can then click **Download**
   to download the rental form.