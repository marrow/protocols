From: https://github.com/lesite/Shoplifter/tree/feature/taxonomy-model (LGPL)

Feature: Transactions
	Transactions are what the payment system create, process and store.
	
	Scenario: Preparing a payment for an order with 1 transaction using a payment gateway that's configured for pre-authorization.
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "pre-auth"
		Then the order balance is 30$
		And the order prepared payment amount is 0$
		And the order to prepare payment amount is 30$
		When I prepare a payment of 30$ using "dummypayment"
		Then the order balance is 30$
		And the order prepared payment amount is 30$
		And the order to prepare payment amount is 0$
		And the order is prepared
	
	Scenario: Preparing a payment for an order with 2 transaction using a payment gateway that's configured for pre-authorization.
	    Given I have an order worth 30$
		And I have a backend "dummygiftcard" using "pre-auth"
		And I have a backend "dummypayment" using "pre-auth"
		When I prepare a payment of 25$ using "dummygiftcard"
		When I prepare a payment of 5$ using "dummygiftcard"
		Then the order balance is 30$
		And the order prepared payment amount is 30$
		And the order to prepare payment amount is 0$
		And the order is prepared
	
	Scenario: Preparing a payment for an order with 1 transaction worth less than the total amount, using a payment gateway that's configured for pre-authorization.
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "pre-auth"
		When I prepare a payment of 25$ using "dummypayment"
		Then the order balance is 30$
		And the order prepared payment amount is 25$
		And the order to prepare payment amount is 5$
		And the order is not prepared
	
	Scenario: Preparing a payment for an order with 1 transaction using a payment gateway that's configured for one-time purchases.
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "purchase"
		When I prepare a payment of 30$ using "dummypayment"
		Then the order balance is 30$
		And the order prepared payment amount is 30$
		And the order to prepare payment amount is 0$
		And the order is prepared
	
	Scenario: Preparing a payment for an order with 2 transaction using a payment gateway that's configured for one-time purchases.
	    Given I have an order worth 30$
		And I have a backend "dummygiftcard" using "purchase"
		And I have a backend "dummypayment" using "purchase"
		When I prepare a payment of 25$ using "dummygiftcard"
		When I prepare a payment of 5$ using "dummypayment"
		Then the order balance is 30$
		And the order prepared payment amount is 30$
		And the order to prepare payment amount is 0$
		And the order is prepared
	
	Scenario: Preparing a payment for an order with 1 transaction worth less than the total amount, using a payment gateway that's configured for one-time purchases.
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "purchase"
		When I prepare a payment of 25$ using "dummypayment"
		Then the order balance is 30$
		And the order prepared payment amount is 25$
		And the order to prepare payment amount is 5$
		And the order is not prepared
	
	Scenario: Paying for an order with 1 transaction using dummypayment configured for pre-authorizatons.
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "pre-auth"
		When I prepare a payment of 30$ using "dummypayment"
		And I process the payments for the order
		Then the order balance is 0$
		And the order prepared payment amount is 0$
		And the order to prepare payment amount is 0$
		And the order is prepared
	
	Scenario: Paying for an order with 1 transaction using dummypayment configured for payment capture.
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "pre-auth"
		When I prepare a payment of 30$ using "dummypayment"
		And I process the payments for the order
		Then the order balance is 0$
		And the order prepared payment amount is 0$
		And the order to prepare payment amount is 0$
		And the order is prepared
	
	Scenario: Paying for an order with 2 transactions using dummypayment and dummygiftcard configured for pre-authorizatons.
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "pre-auth"
		And I have a backend "dummygiftcard" using "pre-auth"
		When I prepare a payment of 13.45$ using "dummypayment"
		When I prepare a payment of 16.55$ using "dummygiftcard"
		And I process the payments for the order
		Then the order balance is 0$
		And the order prepared payment amount is 0$
		And the order to prepare payment amount is 0$
		And the order is prepared
	
	Scenario: Paying for an order with 2 transactions using dummypayment and dummygiftcard configured for payment capture.
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "purchase"
		And I have a backend "dummygiftcard" using "purchase"
		When I prepare a payment of 13.45$ using "dummypayment"
		When I prepare a payment of 16.55$ using "dummygiftcard"
		And I process the payments for the order
		Then the order balance is 0$
		And the order prepared payment amount is 0$
		And the order to prepare payment amount is 0$
		And the order is prepared
	
	Scenario: Paying for an order with 2 transactions using dummypayment and dummygiftcard configured for 2 different payment types (1 is purchase, the other is pre-auth)
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "purchase"
		And I have a backend "dummygiftcard" using "pre-auth"
		When I prepare a payment of 13.45$ using "dummypayment"
		When I prepare a payment of 16.55$ using "dummygiftcard"
		And I process the payments for the order
		Then the order balance is 0$
		And the order prepared payment amount is 0$
		And the order to prepare payment amount is 0$
		And the order is prepared
	
	Scenario: Paying for an order with 1 transactions using dummypayment for an amount that's lesser than order.total
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "purchase"
		When I prepare a payment of 13.45$ using "dummypayment"
		And the order prepared payment amount is 13.45$
		Then the order balance is 30$
		And I process the payments for the order
		Then the order balance is 16.55$
		And the order prepared payment amount is 0$
		And the order to prepare payment amount is 16.55$
		And the order is not prepared
	
	Scenario: Capturing a pre-authorized authorization payment.
	    Given I have an order worth 30$
		And I have a backend "dummypayment" using "pre-auth"
		When I prepare a payment of 30$ using "dummypayment"
		Then the captured amount is 0$
		And I process the payments for the order
		And the captured amount is 0$
		Then I capture all authorizations
		Then the captured amount is 30$
	
	Scenario: Preparing a payment using Interac Online.
	    Given I have an order worth 30$
		And I have a backend "dummydebit" using "purchase"
		When the user goes to the bank website to approve the transaction
		Then the bank system does a post to the approval URL with a transaction ID
		And the order is prepared
	
	Scenario: Preparing a payment using Interac Online.
	    Given I have an order worth 30$
		And I have a backend "dummydebit" using "purchase"
		When the user goes to the bank website to approve the transaction
		Then the bank system does a post to the approval URL with a transaction ID
		And the order is prepared
	
	Scenario: Failing to prepare a payment using Interac Online.
	    Given I have an order worth 30$
		And I have a backend "dummydebit" using "purchase"
		When the user goes to the bank website to approve the transaction
		Then the bank system does a post to the denied URL with a transaction ID
		And the order is prepared
