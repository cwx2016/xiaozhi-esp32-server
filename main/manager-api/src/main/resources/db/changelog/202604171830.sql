-- ===============================
-- 添加待办事项插件配置
-- ===============================
START TRANSACTION;

-- 1. 创建待办事项插件
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_CREATE_TODO',
        'Plugin',
        'create_todo',
        '创建待办事项',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'manager_api_url',
                        'type', 'string',
                        'label', 'Manager API 地址',
                        'default', 'http://localhost:8080'
                ),
                JSON_OBJECT(
                        'key', 'api_key',
                        'type', 'string',
                        'label', 'API 密钥',
                        'default', ''
                )
        ),
        30, 0, NOW(), 0, NOW());

-- 2. 查询待办列表插件
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_GET_TODO_LIST',
        'Plugin',
        'get_todo_list',
        '查询待办列表',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'manager_api_url',
                        'type', 'string',
                        'label', 'Manager API 地址',
                        'default', 'http://localhost:8080'
                ),
                JSON_OBJECT(
                        'key', 'api_key',
                        'type', 'string',
                        'label', 'API 密钥',
                        'default', ''
                )
        ),
        31, 0, NOW(), 0, NOW());

COMMIT;
