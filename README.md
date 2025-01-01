# Django Inventory Management System

A comprehensive inventory management system built with Django. This system allows users to manage inventory items, categories, departments, employees, and track stock history and issuance.

## Features

- User authentication and authorization
- Inventory item management
- Category and department management
- Employee management
- Stock history tracking
- Issuance of inventory items
- Detailed reports and dashboards

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Hillary520/Django_Inventory_Management_System.git
    cd Django_Inventory_Management_System
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Apply the migrations:
    ```sh
    python manage.py migrate
    ```

5. Create a superuser:
    ```sh
    python manage.py createsuperuser
    ```

6. Run the development server:
    ```sh
    python manage.py runserver
    ```

7. Open your browser and navigate to `http://127.0.0.1:8000/` to access the application.

## Usage

- Log in with your superuser account.
- Add categories, departments, and employees.
- Manage inventory items and track their stock history.
- Issue inventory items to employees and track the issuance history.
- Generate detailed reports and view dashboards.


## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.





