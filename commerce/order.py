#!/usr/bin/env feature
# coding: scenario

# From: https://gist.github.com/amcgregor/1338661

# This is what the programmer does to the feature file to actually write the tests.
# The style is identical to doctests but with some convenience added in.
# Yes, this is a Python module and is imported like one.  Note the coding.  :)
# This means your tests are bytecode compiled for efficiency.  Line numbers are
# preserved.  Imports are fine and would go here.

Scenario: Users can purchase items online.
          As a user                         # This is descriptive text.
          I want to spend money             # It has no real impact on anything.
          In order to get shiny trinkets    # (It's a docstring.)

Given we have a user:
    >>> user = db.Users.objects.first()     # locals() are deep copied and passed down
    >>> user
    User("Bob Dole", bdole@whitehouse.gov)
    
And the user is logged in:
    >>> web.core.auth.authenticate(user, force=True)
    >>> web.core.auth.user == user
    True
    
And the user has added some products to the cart:
    >>> products = db.Product.objects[:3]
    >>> for product in products:
    ...     api.cart.add(product, 1)
    >>> api.cart.items                      # vvv Abbreviations!
    [(1, Product("Ham")), ...]
    >>> len(api.cart.items)
    3

    When the user begins checkout:
        >>> transaction = api.cart.transaction.begin()
        >>> transaction.state
        "incomplete"
        >>> transaction.balance
        "2.15"
    
    And the user enters shipping details:
        >>> transaction.shipping = Address("1 Government Street", "Washington", "DC")

    And the user enters payment details:
        >>> transaction.method = MockPayment('success', amount="2.15")

    And the user confirms the order:
        >>> transaction.submit()

        Then the payment is processed:
            >>> transaction.state
            'complete'
            >>> transaction.balance
            >>> "0.00"

        And product inventory totals are updated:
            >>> difference = [old - new for old, new in zip(products, db.Product.objects[:3])]
            [1, 1, 1]

        And the order is completed:
            >>> api.cart.empty
            True

        And the user is notified by e-mail:
            >>> log[-1]
            "Sending confirmation e-mail to..."
