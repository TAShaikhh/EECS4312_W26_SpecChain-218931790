# Requirement ID: HR1

- Description: [The system shall identify, before a user opens a locked feature, whether that feature is included in the free plan or the premium plan.]
- Source Persona: [Budget-Conscious Support Seeker]
- Traceability: [Derived from review group A1 via persona HP1]
- Acceptance Criteria: [Given a non-premium user is viewing a screen that contains a locked feature When the feature is displayed Then the screen identifies that feature as free or premium before the user starts checkout.]

# Requirement ID: HR2

- Description: [The system shall show the subscription price, billing period, renewal condition, and cancellation channel before a user confirms a premium purchase.]
- Source Persona: [Budget-Conscious Support Seeker]
- Traceability: [Derived from review group A1 via persona HP1]
- Acceptance Criteria: [Given a user selects a premium upgrade When the purchase summary screen is displayed Then the price, billing period, renewal condition, and cancellation channel are visible before confirmation.]

# Requirement ID: HR3

- Description: [The system shall allow each user to configure separate reminder times for morning, afternoon, and evening check-ins.]
- Source Persona: [Structured Check-In User]
- Traceability: [Derived from review group A2 via persona HP2]
- Acceptance Criteria: [Given a user enters reminder times for morning, afternoon, and evening When the user saves the settings Then the application stores and displays one reminder time for each check-in period.]

# Requirement ID: HR4

- Description: [The system shall allow a user to submit a missed check-in after the scheduled notification window closes and store it under the intended check-in period.]
- Source Persona: [Structured Check-In User]
- Traceability: [Derived from review group A2 via persona HP2]
- Acceptance Criteria: [Given a user missed a scheduled check-in period When the user opens the app and selects that intended period Then the application accepts the answers and stores them under the selected period instead of discarding them.]

# Requirement ID: HR5

- Description: [The system shall store each mood entry with its recorded time so that multiple entries from the same day remain distinguishable.]
- Source Persona: [Reflective Mood Tracker]
- Traceability: [Derived from review group A3 via persona HP3]
- Acceptance Criteria: [Given a user records more than one mood entry on the same day When the entries are saved Then each entry is stored with its own recorded time.]

# Requirement ID: HR6

- Description: [The system shall display a chronological history of a user's recorded moods and reflections.]
- Source Persona: [Reflective Mood Tracker]
- Traceability: [Derived from review group A3 via persona HP3]
- Acceptance Criteria: [Given a user has saved mood entries and reflections When the user opens the history view Then the application displays those entries in chronological order.]

# Requirement ID: HR7

- Description: [The system shall allow a user to record a written reflection together with a mood entry.]
- Source Persona: [Emotional Reflection User]
- Traceability: [Derived from review group A4 via persona HP4]
- Acceptance Criteria: [Given a user is completing a mood entry When the user adds written text and saves the entry Then the application stores the written reflection with that mood entry.]

# Requirement ID: HR8

- Description: [The system shall present relevant insight, reading, or exercise content after a user records feelings in a check-in.]
- Source Persona: [Emotional Reflection User]
- Traceability: [Derived from review group A4 via persona HP4]
- Acceptance Criteria: [Given a user completes a check-in When the check-in is submitted Then the application shows at least one related insight, reading, or exercise item.]

# Requirement ID: HR9

- Description: [The system shall generate a progress summary for a tracked period that includes the user's recorded mood patterns.]
- Source Persona: [Therapy-Support User]
- Traceability: [Derived from review group A5 via persona HP5]
- Acceptance Criteria: [Given a tracked period contains saved entries When the user generates a summary for that period Then the summary includes the recorded mood patterns from that period.]

# Requirement ID: HR10

- Description: [The system shall allow a user to access mental health guidance resources from within the application.]
- Source Persona: [Therapy-Support User]
- Traceability: [Derived from review group A5 via persona HP5]
- Acceptance Criteria: [Given a user opens the guidance or support area When the screen loads Then the application displays available mental health guidance resources.]
