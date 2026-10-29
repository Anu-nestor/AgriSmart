# Copyright (c) 2026, Anu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


class PurchaseRequest(Document):
    def validate(self):
        if flt(self.requested_quantity) <= 0:
            frappe.throw(
                "Requested quantity must be greater than zero."
            )

        if not self.inventory_item:
            frappe.throw("Please select an inventory item.")

        if not self.farm:
            frappe.throw("Please select a farm.")

        if not self.required_by_date:
            frappe.throw("Please select a required-by date.")

        if getdate(self.required_by_date) < getdate(today()):
            frappe.throw(
                "Required-by date cannot be in the past."
            )
