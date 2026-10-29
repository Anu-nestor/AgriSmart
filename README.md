# AgriSmart — Agriculture Management System

AgriSmart is a farm and inventory management application built using the **Frappe Framework**. It helps manage farm records, agricultural inventory, stock movements, purchase requests, and farm-wise stock availability.

## Features

- **Farm Management:** Create, update, and search farm records.
- **Inventory Management:** Manage agricultural items, units, and reorder levels.
- **Stock Transactions:** Track stock-in and stock-out movements with submission and cancellation support.
- **Purchase Requests:** Manage requests through Draft → Approved → Ordered.
- **Inventory Reports:** View farm-wise stock balances and identify low-stock items.
- **Validation & Testing:** Enforce business rules and test critical stock operations.

## Tech Stack

- Python
- Frappe Framework v15
- MariaDB
- Frappe Desk UI
- SQL Query Reports
- Frappe Unit Testing Framework

## Installation

Run these commands from your Frappe Bench directory:

```bash
bench get-app https://github.com/Anu-nestor/AgriSmart
bench --site <site-name> install-app agri_smart
bench --site <site-name> migrate
```

Start the development server:

```bash
bench start
```

## Testing

```bash
bench --site <site-name> run-tests --app agri_smart
```

## Usage

1. Create farms and inventory items.
2. Record stock movements through Stock Transactions.
3. Create and approve Purchase Requests.
4. Run the **Farm-wise Inventory** report to review stock levels and replenishment requirements.

## License

MIT
