PRAGMA foreign_keys = OFF;
-- commands DDL
CREATE TABLE `commands` (`id` VARCHAR(36) NOT NULL PRIMARY KEY,
`name` VARCHAR(100) NOT NULL,
`command` VARCHAR(1000) NOT NULL,
`description` VARCHAR(500) NOT NULL,
`created_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
`expected_response` TEXT NULL DEFAULT '');
-- commands DML
INSERT INTO `commands` (`id`,`name`,`command`,`description`,`created_at`,`expected_response`) VALUES ('1','设置MAC','AT+MAC=026501123456','','2025-09-04 16:39:01',''),('2','获取MAC','AT+MAC?','123','2025-09-04 16:39:18','');
PRAGMA foreign_keys = ON;
