Feature: test class steps
  Background: 
    Given I have a balance of 100
    
  Scenario: withdraw
    When I withdraw 42 from the account
    Then the balance should be 58
  
  Scenario: deposit
    When I deposit 42 into the account
    Then the balance should be 142

  Scenario: pay loans
    Given I have a balance of 1000
    When  I pay my student loan payment
    Then  the balance should be less than 1000
    When  I pay my car loan payment
    Then  the balance should be greater than or equal to 1

  Scenario: failing unittest assertion (expected to fail)
    Given I have a balance of 100
    Then  the following steps should fail
        """
        Then the balance should be 10
        """


  Scenario: withdrawing more than balance raises ValueError (expected to fail)
    #  this is expected to fail with a ValueError to show off the extended withdraw method
    Given I have a balance of 100
    Then the following steps should fail with "Insufficient Funds"
        """
        When  I withdraw 500 from the account
        """
