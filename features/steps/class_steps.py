import unittest
import pytest
import behave
from behave_classy import step_impl_base
from behave.matchers import RegexMatcher


@behave.step(u'the following steps should fail')
def step_should_fail(context):
    with pytest.raises(Exception):
        context.execute_steps(context.text)

@behave.step(u'the following steps should fail with "{exception_message}"')
def step_should_fail_with(context, exception_message):
    with pytest.raises(Exception) as excinfo:
        context.execute_steps(context.text)
    assert exception_message in str(excinfo.value)

Base = step_impl_base()

class BankAccountSteps(Base):
    @property
    def balance(self):
        """convenience shortcut for context balance"""
        amount = getattr(self.context, 'balance', 0)
        return amount

    @balance.setter
    def balance(self, new_amount):
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


class ExtendedSteps(BankAccountSteps, unittest.TestCase):
    def check_balance(self, expected_amount):
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

    def withdraw(self, amount):
        """Extends withdraw method to make sure enough funds are in the account, then call withdraw from superclass"""
        if amount > self.balance:
            raise ValueError('Insufficient Funds')
        super().withdraw(amount)

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