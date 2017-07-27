CREATE DATABASE IF NOT EXISTS alexacloud;
GRANT USAGE ON *.* TO 'alexacloud'@'%' IDENTIFIED BY 'sirisucks';
GRANT ALL PRIVILEGES ON alexacloud.* TO 'alexacloud'@'%';
FLUSH PRIVILEGES;
