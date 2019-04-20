#!/usr/bin/env feature
# encoding: korcu

# From: https://gist.github.com/amcgregor/d6e7814c56d6d23cf833

import web.auth

from rita.auth.model import User


Feature: Account management.
		 As a recruiter
		 I want to manage my account
		 In order to place orders and keep my details accurate


Scenario: User registration.
	>>> from rita.auth.controller.register import Register
	
	Given an anonymous user:
		>>> web.auth.deauthenticate(True)
	
	And no accounts exist:
		>>> User.objects.delete()
		>>> User.objects.count()
		0
		
		When account creation is requested without data:
			>>> kind, result = Register.post()
			
			Then the call should fail:
				>>> kind
				"json:"
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
			...	 username = 'test',
			...	 name = 'Test User',
			...	 email = 'test@example.com',
			...	 password = 'user',
			...	 pass2 = 'user')
			
			Then the call should succeed:
				>>> kind
				"json:"
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
				
				And the account should be logged in:
					>>> web.auth.user.id == user.id
					True


Scenario: Requesting password recovery.
	>>> from rita.auth.controller.recovery import Recovery
	
	Given an anonymous user.
	
	And an existing account:
		>>> User.objects(admin=False).delete()
		>>> user = User(username='test', email='test@example.com', name="Test User")
		>>> user.password = 'user'
		>>> user.save()
		User(..., test, "Test User")
		
		When password recovery is requested for an invalid identity:
			>>> kind, result = Recovery.post('bad')
			
			Then the call should fail.
		
		When password recovery is requested for a valid identity:
			>>> kind, result = Recovery.post('test')
			
			Then the call should succeed.
			And a message should be sent by mail.


Scenario: User sign-in.
	>>> from rita.auth.controller.authenticate import Authenticate
	
	Given an anonymous user.
	And an existing account.
	
		When authentication is requested with an invalid identity:
			>>> kind, result = Authenticate.post(identity='bob', password='dole')
			
			Then the call should fail.
		
		When authentication is requested with a valid identity:
			>>> kind, result = Authenticate.post(identity='test', password='user')
			
			Then the call should succeed.
			And the account should be logged in.


Scenario: User changes account details.
	>>> From rita.auth.controller.settings import Settings
	
	Given an existing account.
	
	And an authenticated user:
		>>> web.auth.authenticate(user.id, force=True)
		True
		
		When account settings are updated with a new e-mail address:
			>>> kind, result = Settings.post(name=user.name, email='test2@example.com')
			
			Then the call should succeed.
			And a message should be sent by mail.
			
			And the account should have an updated e-mail address:
				>>> user.reload().email
				"test2@example.com"
			
		When attempting to change the password without the current password:
			>>> kind, result = Settings.post(
			...	 name = user.name,
			...	 email = user.email,
			...	 password1 = 'bad',
			...	 password2 = 'fail')
			
			Then the call should fail.
		
		When account settings are updated with a new password:
			>>> kind, result = Settings.post(
			...	 name = user.name,
			...	 email = user.email,
			...	 password1 = 'user',
			...	 password2 = 'pass')
			
			Then the call should succeed.
			And a message should be sent by mail.
			
			And the new password should be effective:
				>>> web.auth.authenticate('test', 'pass')
				True
