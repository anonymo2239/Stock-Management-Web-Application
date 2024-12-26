# **Stock Management Application**

This project, **Stock Management Application**, is designed to manage product inventories, orders and customer requests using **Django** and **MS SQL**. It features an admin-side simulation of **threading** for handling tasks based on priority scores. The application provides a user-friendly interface with visualizations like pie charts and a robust logging system for efficient management.

---

## **Features**

### **Stock Management**
- View and update product inventories.
- Manage stock quantities and prices for each product.
- Visualize stock distribution using pie charts.

### **Order Management**
- Manage and list customer orders.
- Handle tasks based on priority scores.
- Approve or reject orders directly from the admin panel.

### **Customer Requests**
- Manage customer-specific product requests.
- Track requests by product and quantity.

### **Logging System**
- Automatically log all admin actions.
- View detailed logs with timestamps and operation details.

---

## **Technologies Used**
- **Frontend**: HTML, CSS, JavaScript.
- **Backend**: Django (Python web framework).
- **Database**: Microsoft SQL Server.
- **Development Environment**: Visual Studio Code.

---

## **Installation and Setup**

### **Requirements**
- Python 3.9 or later
- Django 4.x
- MSSQL Server (e.g., SQL Server Management Studio)
- Pip and virtualenv (recommended)

### **Installation Steps**

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/Stock-Management-Django.git
   cd Stock-Management-Django

2. **Create and Activate a Virtual Environment (Optioanl)** 
   ```bash
   python -m venv env
   source env/bin/activate   # For MacOS/Linux
   env\Scripts\activate      # For Windows

3. **Install Required Python Packages (Optioanl)**
   ```bash
   pip install -r requirements.txt

4. **Configure MS SQL Database**
     * Make sure the django-mssql-backend package is installed.
     * Open the settings.py file and update the database settings:
      ```bash
      DATABASES = {
       'default': {
           'ENGINE': 'mssql',
           'NAME': 'DbStockApplication',
           'USER': 'your_db_user',
           'PASSWORD': 'your_password',
           'HOST': 'your_server_host',
           'PORT': '1433',
           'OPTIONS': {
               'driver': 'ODBC Driver 17 for SQL Server',
           },
       }
   }
   
5. **Apply Database Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   
6. **Run the Development Server**
   ```bash
   python manage.py runserver

7. **Access the Application**
   * Admin panel: http://127.0.0.1:8000/admin
   * Application: http://127.0.0.1:8000
  
## Database Setup
1. Create a New Database in MS SQL Server
   * Open SQL Server Management Studio (SSMS).
   * Create a new database:
   ```bash
   CREATE DATABASE StockManagementDB;

2. Create Tables
   * Use the provided SQL script to define the database schema:
   ```bash
   CREATE TABLE Products (
       id INT PRIMARY KEY IDENTITY,
       name NVARCHAR(100),
       stock INT,
       price DECIMAL(10, 2)
   );
   ```
   * Define other tables and relationships based on your requirements.

## Usage
1. Log in to the admin panel to manage stock, orders, and customer requests.
2. Use the threading simulation to handle tasks based on priority scores.
3. Monitor and review all actions via the logging system.

## Contributors
   * Developer 1: Adem Alperen Arda (alperen.arda.adem22@gmail.com)
   * Developer 2: Ömer Şimşek (omer20200@hotmail.com)

## License
This project is licensed under the MIT License.
