-- ===============================
-- 为现有智能体添加待办事项插件配置
-- ===============================
START TRANSACTION;

-- 1. 获取所有已存在的智能体ID
-- 2. 为每个智能体添加 create_todo 和 get_todo_list 插件

-- 插入 create_todo 插件（如果智能体尚未关联）
INSERT INTO ai_agent_plugin_mapping (agent_id, plugin_id, param_info)
SELECT 
    a.id AS agent_id,
    'SYSTEM_PLUGIN_CREATE_TODO' AS plugin_id,
    JSON_OBJECT(
        'manager_api_url', 'http://localhost:8002',
        'api_key', ''
    ) AS param_info
FROM ai_agent a
WHERE NOT EXISTS (
    SELECT 1 FROM ai_agent_plugin_mapping apm 
    WHERE apm.agent_id = a.id AND apm.plugin_id = 'SYSTEM_PLUGIN_CREATE_TODO'
);

-- 插入 get_todo_list 插件（如果智能体尚未关联）
INSERT INTO ai_agent_plugin_mapping (agent_id, plugin_id, param_info)
SELECT 
    a.id AS agent_id,
    'SYSTEM_PLUGIN_GET_TODO_LIST' AS plugin_id,
    JSON_OBJECT(
        'manager_api_url', 'http://localhost:8002',
        'api_key', ''
    ) AS param_info
FROM ai_agent a
WHERE NOT EXISTS (
    SELECT 1 FROM ai_agent_plugin_mapping apm 
    WHERE apm.agent_id = a.id AND apm.plugin_id = 'SYSTEM_PLUGIN_GET_TODO_LIST'
);

COMMIT;

-- ===============================
-- 验证查询：检查插件配置是否正确
-- ===============================
SELECT 
    a.id AS agent_id,
    a.agent_name,
    apm.plugin_id,
    apm.param_info
FROM ai_agent a
LEFT JOIN ai_agent_plugin_mapping apm ON a.id = apm.agent_id
WHERE apm.plugin_id IN ('SYSTEM_PLUGIN_CREATE_TODO', 'SYSTEM_PLUGIN_GET_TODO_LIST')
ORDER BY a.id, apm.plugin_id;
