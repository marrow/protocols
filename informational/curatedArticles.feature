Feature: Curated articles

Scenario: Article Listing.
          As a curator
          I want to view all articles
          In order to know what is displayed on my site

Given we have an user
And the user is logged in
And the user has permission to curate
  When the user views the articles to curate
  Then the user sees a listing of all articles
  And titles are displayed for each article
  And descriptions are displayed for each article
  And publication times are displayed for each article
  And unpublish times are displayed for each article
  And links are displayed for each article

Scenario: Adding new articles.
          As a curator
          I want to add an article
          In order to display it on my site

Given we have an user
And the user is logged in
And the user has permission to curate
And no articles exist
  When article creation is requested without data.
    Then the call should fail.
    And no articles should exist.
  When article creation is requested with invalid data.
    Then the call should fail.
    And no articles should exist.
  When article creation is requested with valid data.
    Then the call should succeed.
    And an article should exist.

Scenario: Publishing articles.
          As a curator
          I want to publish an article
          In order to start showing it to my audience

Given we have an user
And the user is logged in
And the user has permission to publish
  When the user publishes the article with a date in the past.
    Then the call should succeed.
    And the article's publication date should match a date in the past.
  When the user publishes the article with the current time.
    Then the call should succeed.
    And the article's publication date should be within a few seconds of the current time.
  When the user publishes the article with a date in the future.
    Then the call should succeed.
    And the article's publication date should match a date in the future.