From: https://gist.github.com/amcgregor/bbd3c3dea76fa925d2e1

Feature: Account management.
         As a player
         I want to manage my account
         So I can do nifty things


Scenario: User registration.
    Given an anonymous user.
    And no accounts exist.
        When account creation is requested without data.
            Then the call should fail.
            And no accounts should exist.
        When account creation is requested with invalid data.
            Then the call should fail.
            And no accounts should exist.
        When account creation is requested with valid data.
            Then the call should succeed.
            And a message should be sent by mail.
            And an account should exist.
                And the account should be unverified.

Scenario: Requesting password recovery.
    Given an anonymous user.
    And an existing account.
        When password recovery is requested for an invalid identity.
            Then the call should fail.
        When password recovery is requested for a valid identity.
            Then the call should succeed.
            And a message should be sent by mail.


Indentation implies that a step relies on the state of the parent.
I.e. we can't test that an account is verified until we are sure it exists, in the above.
Steps at the same indentation 'tier' happen in parallel.
A change of adverb must always be accompanied by an increase in indentation.
(The when relies an all givens, thens on the when, etc.)
