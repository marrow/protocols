# From: https://gist.github.com/amcgregor/4a318ba8c71475676af9e2db5c762f9b

Scenario: User authentication and session initialization.
	>>> from web.app.example.account import Account
	>>> from web.app.example.session import Sessions
	
	Given an anonymous user.
		>>> assert 'session' not in context
	
	And an existing account.
		>>> assert Account.get_collection().count_documents()
		
		When authentication is requested with an invalid identity:
			>>> result = Sessions.post(identity='bob', password='dole')
			
			Then the call should fail.
				>>> result['ok']
				False
			
			And no session should persist.
				>>> assert 'session' not in context
		
		When authentication is requested with a valid identity:
			>>> result = Sessions.post(identity='test', password='user')
			
			Then the call should succeed.
				>>> result['ok']
				True
			
			And the account should be logged in.
				>>> assert 'session' in context
				>>> assert 'user' in context
				>>> assert context.user.id == 'test'
