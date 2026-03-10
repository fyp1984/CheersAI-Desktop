-- Reset password for 1@qq.com to '123456'
-- Password hash generated with: werkzeug.security.generate_password_hash('123456', method='pbkdf2:sha256')
UPDATE accounts 
SET password = 'pbkdf2:sha256:600000$IfSS16Zw0tFG2cE5$43b04a657e1525a5e7fb44c6e036027dd62ceb2881dc8fd9875ad2a58296190a'
WHERE email = '1@qq.com';

-- Verify the update
SELECT email, name, status, LENGTH(password) as pwd_len FROM accounts WHERE email = '1@qq.com';
