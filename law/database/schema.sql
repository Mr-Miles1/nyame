CREATE DATABASE store_system;
USE store_system;

-- Users
CREATE TABLE users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(150),
  role ENUM('admin','storekeeper','cashier','owner') DEFAULT 'storekeeper',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers
CREATE TABLE suppliers (
  supplier_id INT AUTO_INCREMENT PRIMARY KEY,
  supplier_name VARCHAR(150) NOT NULL,
  phone VARCHAR(30),
  email VARCHAR(100),
  address TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers
CREATE TABLE customers (
  customer_id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(150),
  phone VARCHAR(30),
  email VARCHAR(100),
  address TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products
CREATE TABLE products (
  product_id INT AUTO_INCREMENT PRIMARY KEY,
  product_name VARCHAR(255) NOT NULL,
  category VARCHAR(100),
  supplier_id INT,
  quantity_in_stock INT DEFAULT 0,
  reorder_level INT DEFAULT 5,
  cost_price DECIMAL(10,2),
  selling_price DECIMAL(10,2),
  expiry_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
);

-- Purchases
CREATE TABLE purchases (
  purchase_id INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT,
  supplier_id INT,
  quantity_purchased INT,
  purchase_price DECIMAL(10,2),
  purchase_date DATE DEFAULT (CURRENT_DATE),
  FOREIGN KEY (product_id) REFERENCES products(product_id),
  FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
);

-- Sales
CREATE TABLE sales (
  sale_id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT,
  user_id INT,
  total_amount DECIMAL(10,2),
  payment_method ENUM('cash','mobile_money','card') DEFAULT 'cash',
  sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Sale Items
CREATE TABLE sale_items (
  sale_item_id INT AUTO_INCREMENT PRIMARY KEY,
  sale_id INT,
  product_id INT,
  quantity_sold INT,
  unit_price DECIMAL(10,2),
  total_price DECIMAL(10,2),
  FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Logs
CREATE TABLE logs (
  log_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  action VARCHAR(120),
  details TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);
