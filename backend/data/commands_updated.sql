PRAGMA foreign_keys = OFF;

-- commands DDL
-- CREATE TABLE `commands` (
--     `id` VARCHAR(36) NOT NULL PRIMARY KEY,
--     `name` VARCHAR(100) NOT NULL,
--     `command` VARCHAR(1000) NOT NULL,
--     `description` VARCHAR(500) NOT NULL,
--     `created_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
--     `expected_response` TEXT NULL DEFAULT '',
--     `send_as_hex` BOOLEAN NOT NULL DEFAULT 0,
--     `show_notification` BOOLEAN NOT NULL DEFAULT 0,
--     `target_serial_id` INTEGER NULL
-- );

-- commands DML
INSERT INTO `commands` (`id`, `name`, `command`, `description`, `created_at`, `expected_response`, `send_as_hex`, `show_notification`, `target_serial_id`) VALUES 
('1', '设置MAC', 'AT+MAC=026501123456', '', '2025-09-04 16:39:01', '', 0, 0, 1),
('2', '获取MAC', 'AT+MAC?', '123', '2025-09-04 16:39:18', '', 0, 0, 1),
('4c1eae2c-49e4-431c-a271-81fc7c5dcd54', '测试 Eeprom', 'Eeprom', '', '2025-09-06 10:42:26', 'EEPROM Test OK\r\n', 0, 0, 1),
('4c1eae2c-49e4-431c-a271-81fc7c5dcd55', '测试LED1', 'ON1', 'LED1 是否亮灯?', '2025-09-06 10:42:26', 'LED1OK\r\n', 0, 1, 1),
('4c1eae2c-49e4-431c-a271-81fc7c5dcd56', '测试LED2', 'ON2', 'LED2 是否亮灯?', '2025-09-06 10:42:26', 'LED2OK\r\n', 0, 1, 1),
('4c1eae2c-49e4-431c-a271-81fc7c5dcd57', '测试LED3', 'ON1', 'LED3 是否亮灯?', '2025-09-06 10:42:26', 'LED3OK\r\n', 0, 1, 1),
('4c1eae2c-49e4-431c-a271-81fc7c5dcd58', '测试 DPLCA', 'DPLCA', '', '2025-09-06 10:42:26', '', 0, 0, 1),
('4c1eae2c-49e4-431c-a271-81fc7c5dcd59', '测试 S485B', 'S485B', '', '2025-09-06 10:42:26', '485BOK\r\n', 0, 0, 2);

PRAGMA foreign_keys = ON;
