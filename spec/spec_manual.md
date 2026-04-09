# Requirement ID: FR1

- Description: [The system shall display, before a user opens a locked feature, whether the feature is included in the free plan or the premium plan.]
- Source Persona: [Budget-Conscious Support Seeker]
- Traceability: [Derived from review group G1 via persona P1]
- Acceptance Criteria: [Given a non-premium user is viewing a screen that contains a locked feature When the feature is shown Then the screen identifies that feature as free or premium before the user starts checkout.]

# Requirement ID: FR2

- Description: [The system shall show the subscription price, billing period, renewal condition, and cancellation channel before a user confirms a premium purchase.]
- Source Persona: [Budget-Conscious Support Seeker]
- Traceability: [Derived from review group G1 via persona P1]
- Acceptance Criteria: [Given a user selects a premium upgrade When the purchase summary screen is displayed Then the price, billing period, renewal condition, and cancellation channel are visible on that screen before confirmation.]

# Requirement ID: FR3

- Description: [The system shall allow each user to configure separate reminder times for morning, afternoon, and evening check-ins.]
- Source Persona: [Structured Check-In User]
- Traceability: [Derived from review group G2 via persona P2]
- Acceptance Criteria: [Given a user enters three reminder times in settings When the user saves the settings Then the application stores and displays one reminder time for each of the morning, afternoon, and evening check-in periods.]

# Requirement ID: FR4

- Description: [The system shall allow a user to submit a missed check-in after the scheduled notification window closes and store it under the intended check-in period.]
- Source Persona: [Structured Check-In User]
- Traceability: [Derived from review group G2 via persona P2]
- Acceptance Criteria: [Given a user missed a scheduled check-in period When the user opens the app and selects that intended period Then the application accepts the answers and stores them under the selected period instead of discarding them.]

# Requirement ID: FR5

- Description: [The system shall generate a progress report for a tracked reporting period that includes mood trends, symptom trends, and saved journal entries from that period.]
- Source Persona: [Therapy-Prepared Journaler]
- Traceability: [Derived from review group G3 via persona P3]
- Acceptance Criteria: [Given a reporting period contains saved entries When the user generates a report for that period Then the report includes a mood trend section, a symptom trend section, and the saved journal entries from that period.]

# Requirement ID: FR6

- Description: [The system shall allow a user to export a generated progress report for sharing with a therapist or doctor.]
- Source Persona: [Therapy-Prepared Journaler]
- Traceability: [Derived from review group G3 via persona P3]
- Acceptance Criteria: [Given a generated progress report is open When the user chooses export Then the application produces a downloadable file that contains the report content for the selected date range.]

# Requirement ID: FR7

- Description: [The system shall restore a returning user's journal entries and mood history after successful account sign-in.]
- Source Persona: [Privacy and Continuity User]
- Traceability: [Derived from review group G4 via persona P4]
- Acceptance Criteria: [Given an account already contains saved journal entries and mood history When the user signs in successfully Then the application shows the saved journal entries and mood history in that account.]

# Requirement ID: FR8

- Description: [The system shall show the current data-sharing and privacy information on an in-app privacy screen.]
- Source Persona: [Privacy and Continuity User]
- Traceability: [Derived from review group G4 via persona P4]
- Acceptance Criteria: [Given an authenticated user opens the privacy screen When the screen loads Then the current data-sharing and privacy information is visible on that screen.]

# Requirement ID: FR9

- Description: [The system shall allow a user to add and reuse custom emotion labels and custom activity labels in check-ins.]
- Source Persona: [Nuanced Mood Tracker]
- Traceability: [Derived from review group G5 via persona P5]
- Acceptance Criteria: [Given a user creates a custom emotion label and a custom activity label When the labels are saved Then both labels are available for selection in later check-ins without being re-entered.]

# Requirement ID: FR10

- Description: [The system shall support a third response option of I do not know for binary self-assessment questions.]
- Source Persona: [Nuanced Mood Tracker]
- Traceability: [Derived from review group G5 via persona P5]
- Acceptance Criteria: [Given a binary self-assessment question is displayed When the user does not know the answer Then the user can submit I do not know and the application stores that response.]
