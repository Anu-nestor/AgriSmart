# Copyright (c) 2026, Anu and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestStockTransaction(FrappeTestCase):

    def setUp(self):
        suffix = frappe.generate_hash(length=8)

        self.farm = frappe.get_doc({
            "doctype": "Farm",
            "farm_name": f"Test Farm {suffix}",
            "location": "Test Location",
            "farm_owner": "Administrator",
            "size_acres": 10,
            "soil_type": "Alluvial",
        }).insert(ignore_permissions=True)

        self.item = frappe.get_doc({
            "doctype": "Inventory Item",
            "item_name": f"Test Seeds {suffix}",
            "category": "Seed",
            "uom": "kg",
            "current_stock": 0,
            "reorder_level": 20,
        }).insert(ignore_permissions=True)

    def create_transaction(self, transaction_type, quantity):
        transaction = frappe.get_doc({
            "doctype": "Stock Transaction",
            "transaction_date": today(),
            "inventory_item": self.item.name,
            "farm": self.farm.name,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "remarks": "Automated unit test",
        })
        transaction.insert(ignore_permissions=True)
        return transaction

    def get_stock(self):
        return frappe.db.get_value(
            "Inventory Item",
            self.item.name,
            "current_stock",
        )

    def test_stock_in_increases_inventory(self):
        transaction = self.create_transaction("Stock In", 50)
        transaction.submit()

        self.assertEqual(self.get_stock(), 50)

    def test_stock_out_decreases_inventory(self):
        stock_in = self.create_transaction("Stock In", 50)
        stock_in.submit()

        stock_out = self.create_transaction("Stock Out", 15)
        stock_out.submit()

        self.assertEqual(self.get_stock(), 35)

    def test_insufficient_stock_is_rejected(self):
        transaction = self.create_transaction("Stock Out", 10)

        with self.assertRaises(frappe.ValidationError):
            transaction.submit()

        self.assertEqual(self.get_stock(), 0)

    def test_zero_quantity_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            self.create_transaction("Stock In", 0)

        self.assertEqual(self.get_stock(), 0)

    def test_negative_quantity_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            self.create_transaction("Stock In", -5)

        self.assertEqual(self.get_stock(), 0)

    def test_cancellation_reverses_stock_in(self):
        transaction = self.create_transaction("Stock In", 40)
        transaction.submit()

        self.assertEqual(self.get_stock(), 40)

        transaction.cancel()

        self.assertEqual(self.get_stock(), 0)

    def test_cancellation_reverses_stock_out(self):
        stock_in = self.create_transaction("Stock In", 50)
        stock_in.submit()

        stock_out = self.create_transaction("Stock Out", 15)
        stock_out.submit()

        self.assertEqual(self.get_stock(), 35)

        stock_out.cancel()

        self.assertEqual(self.get_stock(), 50)

