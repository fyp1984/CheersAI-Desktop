-- Update admin account with correct password format
-- Email: admin@local.com
-- Password: admin123
-- Using Dify's custom pbkdf2 + salt format

UPDATE accounts 
SET 
    password = 'MjhiZjBmZjFmNjY5ODJkNjA4NDcxZjdjY2M0ZTI0ZWQ3Y2JkNWQwNzRiM2YxNzRlMTZmNTQ4YmYyMWM1MmI0Yg==',
    password_salt = 'QCW5oSbjdDJ7qvZh/2jt8g==',
    updated_at = NOW()
WHERE email = 'admin@local.com';

-- Verify the account
SELECT email, name, status, LENGTH(password) as pwd_len, LENGTH(password_salt) as salt_len 
FROM accounts WHERE email = 'admin@local.com';
