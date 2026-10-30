# Copyright (c) 2026, Anu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class InventoryItem(Document):

    def validate(self):

        # Reorder level must be positive
        if flt(self.reorder_level) <= 0:
            frappe.throw(
                "Reorder Level must be greater than zero."
            )

        # Stock cannot be negative
        if flt(self.current_stock) < 0:
            frappe.throw(
                "Current Stock cannot be negative."
            )

        # Reorder quantity validation
        if self.replenishment_enabled:
            if flt(self.reorder_quantity) <= 0:
                frappe.throw(
                    "Reorder Quantity must be greater than zero "
                    "when replenishment is enabled."
                )

        # Prevent direct stock modification
        if not self.is_new():

            old_stock = frappe.db.get_value(
                "Inventory Item",
                self.name,
                "current_stock"
            )

            if flt(self.current_stock) != flt(old_stock):
                frappe.throw(
                    "Current Stock cannot be changed manually. "
                    "Please use Stock Transaction."
                )

        elif flt(self.current_stock) != 0:
            frappe.throw(
                "New inventory items must start with zero stock. "
                "Use Stock In to add opening stock."
            )

