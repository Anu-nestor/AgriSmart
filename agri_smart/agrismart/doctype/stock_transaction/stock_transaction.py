# Copyright (c) 2026, Anu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class StockTransaction(Document):
    def validate(self):
        if flt(self.quantity) <= 0:
            frappe.throw("Quantity must be greater than zero.")

        if self.transaction_type not in ("Stock In", "Stock Out"):
            frappe.throw("Select a valid transaction type.")

    def update_stock(self, reverse=False):
        item = frappe.get_doc(
            "Inventory Item", self.inventory_item
        )

        # Lock the item row while calculating its new stock.
        frappe.db.sql(
            """
            SELECT name FROM `tabInventory Item`
            WHERE name = %s FOR UPDATE
            """,
            (self.inventory_item,),
        )

        item.reload()
        current = flt(item.current_stock)
        qty = flt(self.quantity)

        stock_in = self.transaction_type == "Stock In"

        # Cancellation reverses the original transaction.
        increase = stock_in != reverse
        new_stock = current + qty if increase else current - qty

        if new_stock < 0:
            frappe.throw(
                f"Insufficient stock for {self.inventory_item}."
            )

        item.db_set("current_stock", new_stock)

    def on_submit(self):
        self.update_stock()

    def on_cancel(self):
        self.update_stock(reverse=True)
