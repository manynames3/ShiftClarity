Feature: Evidence-first staffing verification
  Background:
    Given the canonical sc-demo-v1 synthetic records are loaded
    And the clock is fixed at 2026-10-12T17:00:00-04:00

  Scenario: Coverage never disappears behind the financial queue
    When I view the workspace
    Then I see 14 received records and 12 rule-checked records
    And I see 148 received hours and 124 checked hours in coverage details
    And I see 2 financial findings and 2 coverage tasks
    And neither task has an estimated financial impact
    And I see a persistent Synthetic demo label

  Scenario: Rate change is verified using service date
    When I inspect FND-001
    Then I see the approved October 5 amendment and rate 65.00
    And the expected amount is 2600.00 and billed amount is 2400.00
    And the potential discrepancy is 200.00, not recovered money
    And the late-entered October 4 control still uses 60.00

  Scenario: Missing invoice evidence is not missing billing
    Given the invoice extract is incomplete
    When reconciliation is repeated
    Then FND-002 is not asserted as a financial finding
    And its records are visibly not evaluated
    And no all-clear message is shown

  Scenario: Human decisions are local and reversible by new evidence
    When I dismiss FND-001 with a required reason
    Then the decision and reason appear in its review history
    And no source-system write or outgoing message occurs
    When a relevant invoice amount changes
    Then the finding reopens for review
    And the earlier decision remains visible

  Scenario: A rule needs an independent approver
    Given I am simulating the rule's author
    When I attempt to approve that rule
    Then approval is denied with an explanation
    When I simulate a separate authorized approver
    And I inspect the source and approve the draft
    Then a new approved version exists in demo state
    And the previously approved version is not edited

  Scenario: Empty filter is not zero risk
    When I filter to a facility with no matching financial findings
    Then I see No findings match these filters
    And the source coverage summary does not change
    And I can clear the filters with the keyboard

  Scenario: Demo boundary is real
    When I select an arbitrary file not in the supplied synthetic fixtures
    Then it is rejected without upload
    And I see that real-data import is not enabled

  Scenario: Restoring the demonstration
    Given I have changed review decisions and filters
    When I choose Reset demo and confirm
    Then the canonical counts and needs_review states return
    And no customer data or external service is contacted
