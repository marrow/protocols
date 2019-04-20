# From: https://gist.github.com/amcgregor/1338661

# A consultant sits down with a client and hammers out what the client wants
# end-users to be able to do.  These are called stories or scenarios.

Scenario: Users can purchase items online.
          As a user
          I want to spend money
          In order to get shiny trinkets

Given we have a user
And the user is logged in
And the user has added some products to the cart
    When the user begins checkout
    And the user enters shipping details
    And the user enters payment details
    And the user confirms the order
        Then the payment is processed
        And product inventory totals are updated
        And the order is completed
        And the user is notified by e-mail
