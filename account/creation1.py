#!/usr/bin/env feature
# coding: scenario

# From: https://gist.github.com/amcgregor/ac48c35e5c50052aaefb

import web.auth

from rita.auth.model import User


Feature: Account management.
		As a recruiter
		I want to manage my account
		In order to place orders and keep my details accurate


Scenario: Users can register.
	>>> from rita.auth.register import Register
	
	Given an anonymous user:
		>>> web.auth.deauthenticate(True)
	
	And no accounts exist:
		>>> User.objects.delete()
		>>> User.objects.count()
		0
		
		When account creation is requested without data:
			>>> kind, result = Register.post()
			
			Then the call should fail:
				>>> result['success']
				False
			
			And no accounts should exist:
				>>> User.objects.count()
				0
		
		When account creation is requested with invalid data:
			>>> kind, result = Register.post(email='not-an-email-address')
			
			Then the call should fail.
			And no accounts should exist.
		
		When account creation is requested with valid data:
			>>> kind, result = Register.post(
			...		username = 'test',
			...		name = 'Test User',
			...		email = 'test@example.com',
			...		password = 'user',
			...		pass2 = 'user')
			>>> kind
			"json:"
			
			Then the call should succeed:
				>>> result['success']
				True
			
			And a message should be sent by mail:
				>>> from rita.util.testing import messages
				>>> bool(messages)
				True
			
			And an account should exist:
				>>> user = User.objects.first()
				>>> user
				User(..., test, "Test User")
				
				And the account should be unverified:
					>>> bool(user.verified)
					False


Scenario: Users can request password recovery.
	>>> from rita.auth.recovery import Recovery
	
	Given an anonymous user.
	
	And an existing account:
		>>> User.objects.delete()
		>>> User(username='test', email='test@example.com', name="Test User").save()
		User(..., test, "Test User")
		
		When password recovery is requested for an invalid identity:
			>>> kind, result = Recovery.post('bad')
			>>> kind
			"json:"
			
			Then the call should fail.
		
		When password recovery is requested for a valid identity:
			>>> kind, result = Recovery.post('test')
			>>> kind
			"json:"
			
			Then the call should succeed.
			And a message should be sent by mail.
