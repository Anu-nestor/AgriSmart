# Copyright (c) 2026, Anu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, today, add_days


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
    # Update overall inventory stock
        self.update_stock()

        # Check farm-wise reorder level
        self.check_reorder_level()


    def on_cancel(self):
    # Reverse the stock movement
        self.update_stock(reverse=True)

        # Recalculate stock and check replenishment
        self.check_reorder_level()



    def check_reorder_level(self):
        # Calculate stock available at this particular farm
        farm_stock = frappe.db.sql("""
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN transaction_type = 'Stock In'
                                THEN quantity
                            WHEN transaction_type = 'Stock Out'
                                THEN -quantity
                            ELSE 0
                        END
                    ), 0
                )
            FROM `tabStock Transaction`
            WHERE farm = %s
            AND inventory_item = %s
            AND docstatus = 1
        """, (self.farm, self.inventory_item))[0][0]

        item = frappe.get_doc(
            "Inventory Item",
            self.inventory_item
        )

        # Check whether automatic replenishment is enabled
        if not item.replenishment_enabled:
            return

        # Check reorder level
        if flt(farm_stock) > flt(item.reorder_level):
            return

        # Prevent duplicate pending purchase requests
        existing_request = frappe.db.exists(
            "Purchase Request",
            {
                "farm": self.farm,
                "inventory_item": self.inventory_item,
                "status": ["in", ["Draft", "Approved", "Ordered"]],
                "replenishment_completed": 0
            }
        )

        if existing_request:
            return

        # Generate automatic Purchase Request
        purchase_request = frappe.get_doc({
            "doctype": "Purchase Request",
            "inventory_item": self.inventory_item,
            "farm": self.farm,
            "requested_quantity": item.reorder_quantity,
            "required_by_date": add_days(today(), 7),
            "status": "Draft",
            "auto_generated": 1,
            "source_transaction": self.name
        })

        purchase_request.insert(ignore_permissions=True)

        # Notify responsible users
        self.send_replenishment_notifications(
            purchase_request,
            farm_stock,
            item
        )


    def send_replenishment_notifications(
        self, purchase_request, farm_stock, item
    ):

        # Get Farm Manager
        farm_manager = frappe.db.get_value(
            "Farm",
            self.farm,
            "farm_owner"
        )

        # Get Inventory Managers
        inventory_managers = frappe.get_all(
            "Has Role",
            filters={
                "role": "Inventory Manager",
                "parenttype": "User"
            },
            pluck="parent"
        )

        # Combine recipients and remove duplicates
        recipients = set(inventory_managers)

        if farm_manager:
            recipients.add(farm_manager)

        # Send Frappe in-app notifications
        for user in recipients:

            if not frappe.db.get_value(
                "User", user, "enabled"
            ):
                continue

            notification = frappe.get_doc({
                "doctype": "Notification Log",
                "subject": "AgriSmart: Low Stock Alert",
                "for_user": user,
                "type": "Alert",
                "document_type": "Purchase Request",
                "document_name": purchase_request.name,
                "email_content": (
                    f"Low stock detected for {item.item_name}. "
                    f"Farm: {self.farm}. "
                    f"Available stock: {farm_stock} {item.uom}. "
                    f"Reorder level: {item.reorder_level} {item.uom}. "
                    f"Purchase quantity: {item.reorder_quantity} "
                    f"{item.uom}. "
                    f"Purchase Request: {purchase_request.name}"
                )
            })

            notification.insert(ignore_permissions=True)
