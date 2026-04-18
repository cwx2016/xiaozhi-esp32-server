-- ===============================
-- 添加完成待办和删除待办插件配置
-- ===============================
START TRANSACTION;

-- 1. 完成待办事项插件
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_COMPLETE_TODO',
        'Plugin',
        'complete_todo',
        '完成待办事项',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'manager_api_url',
                        'type', 'string',
                        'label', 'Manager API 地址',
                        'default', 'http://localhost:8002'
                ),
                JSON_OBJECT(
                        'key', 'api_key',
                        'type', 'string',
                        'label', 'API 密钥',
                        'default', ''
                )
        ),
        32, 0, NOW(), 0, NOW())
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- 2. 删除待办事项插件
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_DELETE_TODO',
        'Plugin',
        'delete_todo',
        '删除待办事项',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'manager_api_url',
                        'type', 'string',
                        'label', 'Manager API 地址',
                        'default', 'http://localhost:8002'
                ),
                JSON_OBJECT(
                        'key', 'api_key',
                        'type', 'string',
                        'label', 'API 密钥',
                        'default', ''
                )
        ),
        33, 0, NOW(), 0, NOW())
ON DUPLICATE KEY UPDATE name = VALUES(name);

COMMIT;
