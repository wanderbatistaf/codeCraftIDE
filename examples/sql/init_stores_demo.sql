-- Initialize stores_demo database with sample tables
DATABASE stores_demo;

-- Customer table
CREATE TABLE customer (
    customer_num SERIAL PRIMARY KEY,
    fname VARCHAR(15),
    lname VARCHAR(15),
    company VARCHAR(20),
    address1 VARCHAR(20),
    address2 VARCHAR(20),
    city VARCHAR(15),
    state CHAR(2),
    zipcode CHAR(5),
    phone VARCHAR(18)
);

-- Insert sample customer data
INSERT INTO customer (fname, lname, company, city, state, zipcode, phone)
VALUES ('Ludwig', 'Pauli', 'All Sports Supplies', 'Redwood City', 'CA', '94026', '415-555-1212');

INSERT INTO customer (fname, lname, company, city, state, zipcode, phone)
VALUES ('Carole', 'Sadler', 'Sports Spot', 'Menlo Park', 'CA', '94025', '415-555-7600');

COMMIT WORK;
