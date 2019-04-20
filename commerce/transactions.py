# -*- coding: utf-8 -*-

# From: https://github.com/lesite/Shoplifter

# Monkeypatching memcache client to use mockcache instead.
import memcache
import mockcache
memcache.Client = mockcache.Client

import decimal
from pkg_resources import load_entry_point

import mongoengine
from lettuce import step, world
from nose.tools import assert_equals

from shoplifter.payment import config, plugins
from shoplifter.core import plugins as core_plugins


TEST_CREDENTIALS = {
    'dummypayment': ('4242424242424242', '2011', '01', '123'),
    'dummygiftcard': ('derp', ),
    }


mongoengine.connect('testdb6')


core_plugins.load('temp_storage', 'memcache', **{
        'key': 'testkey123456789',
        'location': ('127.0.0.1:11211', ),
        })

config.update({
        'cc_store_time': 5 * 60,
        'temp_store': core_plugins['temp_storage'].memcache,
        })


backend_settings = {
    'dummypayment': {
        'username': 'derp',
        'password': 'derp',
        'api_key': 'derp',
        'url': 'http://derp',
        },
    'dummygiftcard': {
        'username': 'derp',
        'password': 'derp',
        'api_key': 'derp',
        'url': 'http://derp',
        },
    'dummydebit': {
        'username': 'derp',
        'password': 'derp',
        'api_key': 'derp',
        'url': 'http://derp',
        },
    }


@step(u'I have an order worth (\d[\.\d]*)\$')
def i_have_an_order_worth(step, amount):
    from shoplifter.payment.lib.test_helpers import TestOrder
    world.order = TestOrder(decimal.Decimal(amount))
    assert_equals(world.order.total, decimal.Decimal('30'))


@step(u'I have a backend "([^"]*)" using "([^"]*)"')
def prepare_backend(step, backend_name, payment_type):
    use_pre_auth = payment_type == 'pre-auth'
    backend_conf = backend_settings[backend_name]
    backend_conf['use_pre_auth'] = use_pre_auth
    plugins.load('payment_backends', backend_name, backend_conf)

    assert backend_name in plugins['payment_backends']
    # assert_equals(settings.backends[backend_name].name, backend_name)


@step(u'I prepare a payment of (\d[\.\d]*)\$ using "([^"]*)"')
def prepare_payment(step, amount, backend_name):
    amount = decimal.Decimal(amount)
    backend = plugins['payment_backends'][backend_name]
    args = TEST_CREDENTIALS[backend_name]
    payment = backend.prepare_payment(
        world.order, amount, *args)
    assert_equals(payment.amount, amount)


@step(u'the order balance is (\d[\.\d]*)\$')
def the_order_balance_is(step, amount):
    assert_equals(world.order.balance, decimal.Decimal(amount))


@step(u'the order prepared payment amount is (\d[\.\d]*)\$')
def the_order_prepared_payment_amount_is(step, amount):
    assert_equals(world.order.payment.get_prepared_amount(),
                  decimal.Decimal(amount))


@step(u'the order to prepare payment amount is (\d[\.\d]*)\$')
def the_order_to_prepare_payment_amount_is(step, amount):
    assert_equals(world.order.payment.get_to_prepare_amount(),
                  decimal.Decimal(amount))


@step(u'I process the payments for the order')
def and_i_process_the_payments_for_the_order(step):
    world.order.payment.process_all_payments()
    assert True


@step(u'the order is (not )?prepared')
def and_the_order_is_prepared(step, not_bool):
    assert ((not(not_bool) and world.order.is_prepared) or
             not_bool and not world.order.is_prepared)


@step(u'the captured amount is (\d[\.\d]*)\$')
def the_captured_amount_is(step, amount):
    assert_equals(world.order.payment.get_captured_amount(),
                  decimal.Decimal(amount))


@step(u'Then I capture all authorizations')
def then_i_capture_all_authorizations(step):
    world.order.payment.capture_all_authorizations()
    assert True


@step(u'When the user goes to the bank website to approve the transaction')
def when_the_user_goes_to_the_bank_website_to_approve_the_transaction(step):
    assert False, 'This step must be implemented'


@step(u'Then the bank system does a post to the (approval|denied) URL with a transaction ID')
def then_the_bank_system_does_a_post_to_the_approval_url_with_a_transaction_id(step):
    assert False, 'This step must be implemented'
