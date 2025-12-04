-- Initialize database for local development
CREATE USER acham WITH PASSWORD 'acham123';
CREATE DATABASE acham OWNER acham;
GRANT ALL PRIVILEGES ON DATABASE acham TO acham;
