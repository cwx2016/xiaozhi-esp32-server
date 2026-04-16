-- 创建待办事项表
DROP TABLE IF EXISTS `ai_todo`;
CREATE TABLE `ai_todo` (
    `id` VARCHAR(32) NOT NULL COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `agent_id` VARCHAR(32) DEFAULT NULL COMMENT '智能体ID',
    `device_id` VARCHAR(30) DEFAULT NULL COMMENT '设备ID（MAC地址），示例：AA:BB:CC:DD:EE:FF',
    `title` VARCHAR(255) NOT NULL COMMENT '待办标题',
    `content` TEXT COMMENT '待办内容',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-未完成，1-已完成',
    `priority` TINYINT NOT NULL DEFAULT 0 COMMENT '优先级：0-普通，1-重要，2-紧急',
    `due_date` VARCHAR(10) DEFAULT NULL COMMENT '截止日期，字符串格式：2025-12-31',
    `due_time` VARCHAR(5) DEFAULT NULL COMMENT '截止时间，字符串格式：10:00',
    `repeat_type` VARCHAR(20) DEFAULT 'none' COMMENT '重复类型：none-不重复、daily-每天、weekly-每周、monthly-每月、yearly-每年',
    `completed_at` DATETIME DEFAULT NULL COMMENT '完成时间',
    `deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '逻辑删除：0-未删除，1-已删除',
    `sort` INT DEFAULT 0 COMMENT '排序',
    `creator` BIGINT DEFAULT NULL COMMENT '创建者',
    `create_date` DATETIME DEFAULT NULL COMMENT '创建时间',
    `updater` BIGINT DEFAULT NULL COMMENT '更新者',
    `update_date` DATETIME DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_agent_id` (`agent_id`),
    KEY `idx_status` (`status`),
    KEY `idx_create_date` (`create_date`),
    KEY `idx_due_date` (`due_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='待办事项表';
