-- Test schema for DLT loading patterns
-- This creates simple tables to test different loading scenarios

USE StackOverflowMini;
GO

-- 1. Simple table for REPLACE loading (full refresh)
IF OBJECT_ID('dbo.TestCustomers', 'U') IS NOT NULL
    DROP TABLE dbo.TestCustomers;
GO

CREATE TABLE dbo.TestCustomers (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    Email NVARCHAR(100),
    City NVARCHAR(50),
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    IsActive BIT DEFAULT 1
);
GO

-- 2. Table for INCREMENTAL loading (timestamp-based)
IF OBJECT_ID('dbo.TestOrders', 'U') IS NOT NULL
    DROP TABLE dbo.TestOrders;
GO

CREATE TABLE dbo.TestOrders (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    CustomerId INT NOT NULL,
    OrderDate DATETIME2 DEFAULT GETDATE(),
    Amount DECIMAL(10,2),
    Status NVARCHAR(20) DEFAULT 'pending',
    LastModified DATETIME2 DEFAULT GETDATE()
);
GO

-- 3. Table for APPEND loading (log-style data)
IF OBJECT_ID('dbo.TestEvents', 'U') IS NOT NULL
    DROP TABLE dbo.TestEvents;
GO

CREATE TABLE dbo.TestEvents (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    EventType NVARCHAR(50),
    EventData NVARCHAR(MAX),
    Timestamp DATETIME2 DEFAULT GETDATE(),
    UserId INT
);
GO

-- 4. Small table for quick testing
IF OBJECT_ID('dbo.TestCategories', 'U') IS NOT NULL
    DROP TABLE dbo.TestCategories;
GO

CREATE TABLE dbo.TestCategories (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(50) NOT NULL,
    Description NVARCHAR(200),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);
GO

-- Insert test data
PRINT 'Inserting test data...'

-- Test customers (replace scenario)
INSERT INTO dbo.TestCustomers (Name, Email, City, CreatedDate, IsActive) VALUES
('John Doe', 'john@example.com', 'New York', '2024-01-01', 1),
('Jane Smith', 'jane@example.com', 'Los Angeles', '2024-01-02', 1),
('Bob Johnson', 'bob@example.com', 'Chicago', '2024-01-03', 0),
('Alice Brown', 'alice@example.com', 'Houston', '2024-01-04', 1),
('Charlie Wilson', 'charlie@example.com', 'Phoenix', '2024-01-05', 1);

-- Test orders (incremental scenario)
INSERT INTO dbo.TestOrders (CustomerId, OrderDate, Amount, Status, LastModified) VALUES
(1, '2024-01-01 10:00:00', 99.99, 'completed', '2024-01-01 10:00:00'),
(2, '2024-01-02 11:30:00', 149.50, 'completed', '2024-01-02 11:30:00'),
(3, '2024-01-03 14:15:00', 75.25, 'pending', '2024-01-03 14:15:00'),
(1, '2024-01-04 09:45:00', 200.00, 'completed', '2024-01-04 09:45:00'),
(4, '2024-01-05 16:20:00', 50.00, 'cancelled', '2024-01-05 16:20:00'),
(2, '2024-01-06 13:10:00', 125.75, 'pending', '2024-01-06 13:10:00'),
(5, '2024-01-07 15:30:00', 300.00, 'completed', '2024-01-07 15:30:00');

-- Test events (append scenario)
INSERT INTO dbo.TestEvents (EventType, EventData, Timestamp, UserId) VALUES
('login', '{"ip": "192.168.1.1"}', '2024-01-01 08:00:00', 1),
('page_view', '{"page": "/home"}', '2024-01-01 08:01:00', 1),
('login', '{"ip": "10.0.0.1"}', '2024-01-01 09:00:00', 2),
('purchase', '{"order_id": 1, "amount": 99.99}', '2024-01-01 10:00:00', 1),
('logout', '{}', '2024-01-01 10:30:00', 1),
('login', '{"ip": "172.16.0.1"}', '2024-01-01 11:00:00', 3),
('page_view', '{"page": "/products"}', '2024-01-01 11:05:00', 3);

-- Test categories (small table)
INSERT INTO dbo.TestCategories (Name, Description, CreatedDate) VALUES
('Electronics', 'Electronic devices and gadgets', '2024-01-01'),
('Books', 'Physical and digital books', '2024-01-01'),
('Clothing', 'Apparel and accessories', '2024-01-01');

PRINT 'Test schema and data created successfully!'

-- Show row counts
SELECT 'TestCustomers' as TableName, COUNT(*) as RowCount FROM dbo.TestCustomers
UNION ALL
SELECT 'TestOrders', COUNT(*) FROM dbo.TestOrders  
UNION ALL
SELECT 'TestEvents', COUNT(*) FROM dbo.TestEvents
UNION ALL
SELECT 'TestCategories', COUNT(*) FROM dbo.TestCategories;

GO