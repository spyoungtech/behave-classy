# behave-classy

*beahve-classy* provides a class-based API for behave step implementations

This package is geared towards authors of step implementation libraries and aims to provide a more flexible and 
extensible interface for behave step libraries and their users.

The primary features 

- ability to define step definitions as classes
- ability to extend steps from your own classes (or perhaps classes provided by other libraries/packages)
- ability to define a matcher per-method without changing global state of the 'current matcher'
- wraps methods to transform context into an attribute (`self.context`), so it's not necessary to have each method use context as first parameter in the signature. Works with default behave runner.

# Installation

Installation is made easy with `pip`

```
pip install behave-classy
```

# Usage

Usage is fairly simple and follows these basic steps:

- Use the `step_impl_base` to create a base class that will contain your step definitions in its own local registry.
- Make your subclass and definitions
- When you want to use your steps, simply call the `register` method of your class.


# Example

Consider some step library which provides a set of steps in the class `BankAccountSteps`.

```python
#  some_library/steps.py
from behave_classy import step_impl_base

Base = step_impl_base()

class BankAccountSteps(Base):
    @property
    def balance(self):
        """convenience shortcut for context balance"""
        amount = getattr(self.context, 'balance', 0)
        return amount
    
    @balance.setter
    def balance(self, new_amount):
        """convenience setter"""
        self.context.balance = new_amount


    @Base.given(u'I have a balance of {amount:d}')
    def set_balance(self, amount):
        self.balance = amount
    
    @Base.when(u'I deposit {amount:d} into the account')
    def deposit(self, amount):
        if amount < 0:
            raise ValueError('Deposit amounts cannot be negative')
        self.balance += amount
    
    @Base.when(u'I withdraw {amount:d} from the account')
    def withdraw(self, amount):
        self.balance -= amount
    
    @Base.then(u'the balance should be {expected_amount:d}')
    def check_balance(self, expected_amount):
        assert self.balance == expected_amount

```

As a user of such a library, you would import the class, then *register* it, so its definitions are added to the global step registry used by behave.

```python
# myproject/features/steps/mysteps.py
from some_library.steps import BankAccountSteps
BankAccountSteps().register()
```

Then with a typical feature file...

```gherkin
# myproject/features/account_balance.feature
Feature: bank account balance
  Background: 
    Given I have a balance of 100
    
  Scenario: withdraw
    When I withdraw 42 from the account
    Then the balance should be 58
  
  Scenario: deposit
    When I deposit 42 into the account
    Then the balance should be 142
```

You can simply run behave as normal

```
$ behave

Feature: bank account balance # features/account_balance.feature:2

  Background:   # features/account_balance.feature:3

  Scenario: withdraw                    # features/account_balance.feature:6
    Given I have a balance of 100       # features/steps/steps.py:18
    When I withdraw 42 from the account # features/steps/steps.py:28
    Then the balance should be 58       # features/steps/steps.py:32

  Scenario: deposit                    # features/account_balance.feature:10
    Given I have a balance of 100      # features/steps/steps.py:18
    When I deposit 42 into the account # features/steps/steps.py:22
    Then the balance should be 142     # features/steps/steps.py:32

1 feature passed, 0 failed, 0 skipped
2 scenarios passed, 0 failed, 0 skipped
6 steps passed, 0 failed, 0 skipped, 0 undefined
Took 0m0.002s
```


## extending and integrating existing work

Without *behave-classy*, you would typically use behave's `context.execute_steps` feature to extend on work. Although 
this works for simple cases, it can be quite inflexible, especially once your cases become nontrivial. *behave-classy* allows you to use usual python techniques (e.g. subclassing, method extensions/overriding, etc.) to reuse 
your existing code, just like you would do in any other python code.

Consider the Bank Account example from the previous section. This example **demonstrates several features**:

1. We will add additional steps the class, adding new methods, which reuse existing methods. One of these will use a different matcher, the RegexMatcher.
2. We will *extend* the existing `withdraw` method to first check that the account has sufficient funds, otherwise raising a ValueError.
3. We will *integrate* unittest assertion matchers to the class by using `unittest.TestCase` as a mixin
4. We will *override* the existing `check_balance` method to use `unittest.TestCase` assertions

```python
# myproject/features/steps/mysteps.py
from unittest import TestCase
from behave.matchers import RegexMatcher
from some_library.steps import BankAccountSteps as Base

class ExtendedSteps(Base, TestCase):
    def withdraw(self, amount):
        """Extends withdraw method to make sure enough funds are in the account, then calls withdraw from superclass"""
        if amount > self.balance:
            raise ValueError('Insufficient Funds')
        super().withdraw(amount)
    
    def check_balance(self, expected_amount):
        """Override check_balance method to use unittest assertions instead"""
        self.assertEquals(self.balance, expected_amount)
        

    @Base.when(u'I pay my {loan_name} loan payment')
    def pay_loan(self, loan_name):
        """additional when step for loan payments"""
        loan_payments = {
            'student': 600,
            'car': 200
        }
        payment_amount = loan_payments[loan_name]
        self.withdraw(payment_amount)


    @Base.then(u'the balance should be (less|greater) than (or equal to )*(\d+)', matcher=RegexMatcher)
    def compare_balance(self, operator, or_equals, amount):
        """Additional step using regex matcher to compare the current balance with some number"""
        amount = int(amount)
        if operator == 'less':
            if or_equals:
                self.assertLessEqual(self.balance, amount)
            else:
                self.assertLess(self.balance, amount)
        elif or_equals:
            self.assertGreaterEqual(self.balance, amount)
        else:
            self.assertGreater(self.balance, amount)


ExtendedSteps().register()
```

We'll add some additional scenarios to our feature file to show off these new alterations

```gherkin
# myproject/features/account_balance.feature
# ...
  Scenario: pay loans
    Given I have a balance of 1000
    When  I pay my student loan payment
    Then  the balance should be less than 1000
    When  I pay my car loan payment
    Then  the balance should be greater than or equal to 1

  Scenario: failing unittest assertion (expected to fail)
    # this is expected to fail, to show off the unittest assertion at work
    Given I have a balance of 100
    Then  the balance should be greater than 100


  Scenario: withdrawing more than balance raises ValueError (expected to fail)
    #  this is expected to fail with a ValueError to show off the extended withdraw method
    Given I have a balance of 100
    When  I withdraw 500 from the account

```

Then if we run this using behave...

```
$ behave
Feature: bank account balance # features/account_balance.feature:2

  Background:   # features/account_balance.feature:3

  Scenario: withdraw                    # features/account_balance.feature:6
    Given I have a balance of 100       # features/steps/steps.py:25
    When I withdraw 42 from the account # features/steps/steps.py:58
    Then the balance should be 58       # features/steps/steps.py:45

  Scenario: deposit                    # features/account_balance.feature:10
    Given I have a balance of 100      # features/steps/steps.py:25
    When I deposit 42 into the account # features/steps/steps.py:29
    Then the balance should be 142     # features/steps/steps.py:45

  Scenario: pay loans                                     # features/account_balance.feature:14
    Given I have a balance of 100                         # features/steps/steps.py:25
    Given I have a balance of 1000                        # features/steps/steps.py:25
    When I pay my student loan payment                    # features/steps/steps.py:48
    Then the balance should be less than 1000             # features/steps/steps.py:64
    When I pay my car loan payment                        # features/steps/steps.py:48
    Then the balance should be greater than or equal to 1 # features/steps/steps.py:64

  Scenario: failing unittest assertion (expected to fail)  # features/account_balance.feature:21
    Given I have a balance of 100                          # features/steps/steps.py:25
    Given I have a balance of 100                          # features/steps/steps.py:25
    Then the balance should be 10                          # features/steps/steps.py:45
      Assertion Failed: 100 != 10


  Scenario: withdrawing more than balance raises ValueError (expected to fail)  # features/account_balance.feature:27
    Given I have a balance of 100                                               # features/steps/steps.py:25
    Given I have a balance of 100                                               # features/steps/steps.py:25
    When I withdraw 500 from the account                                        # features/steps/steps.py:58
      Traceback (most recent call last):
        <partially omitted for readme brevity>
        File "features\steps\steps.py", line 61, in withdraw
          raise ValueError('Insufficient Funds')
      ValueError: Insufficient Funds



Failing scenarios:
  features/account_balance.feature:21  failing unittest assertion (expected to fail)
  features/account_balance.feature:27  withdrawing more than balance raises ValueError (expected to fail)

0 features passed, 1 failed, 0 skipped
3 scenarios passed, 2 failed, 0 skipped
16 steps passed, 2 failed, 0 skipped, 0 undefined
Took 0m0.008s
```

We can see our additional scenarios ran and observe the following from the results:

1. Our additional loan payment steps ran as expected
2. Our step definition `compare_balance`, using the RegexMatcher, correctly matched our steps in the feature file
3. Our override of the `check_balance` method worked and used unittest assertion (evidenced in the failure case)
4. Our extended `withdraw` method was successfully used as expected (demonstrated by the failing case with ValueError)
