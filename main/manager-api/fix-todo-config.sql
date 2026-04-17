-- ===============================
-- 检查并修复待办插件配置
-- ===============================

USE xiaozhi;

-- 1. 检查 ai_model_provider 表中的插件定义
SELECT 
    id,
    provider_code,
    name,
    model_type
FROM ai_model_provider
WHERE provider_code IN ('create_todo', 'get_todo_list');

-- 2. 检查智能体关联和配置
SELECT 
    apm.agent_id,
    a.agent_name,
    apm.plugin_id,
    apm.param_info
FROM ai_agent_plugin_mapping apm
LEFT JOIN ai_agent a ON apm.agent_id = a.id
WHERE apm.plugin_id IN ('SYSTEM_PLUGIN_CREATE_TODO', 'SYSTEM_PLUGIN_GET_TODO_LIST')
ORDER BY apm.agent_id;

-- 3. 修复配置：将所有 create_todo 插件的 manager_api_url 更新为正确的端口
UPDATE ai_agent_plugin_mapping
SET param_info = JSON_SET(
    param_info,
    '$.manager_api_url', 'http://localhost:8002'
)
WHERE plugin_id = 'SYSTEM_PLUGIN_CREATE_TODO'
AND (
    JSON_EXTRACT(param_info, '$.manager_api_url') IS NULL
    OR JSON_EXTRACT(param_info, '$.manager_api_url') = 'http://localhost:8080'
);

-- 4. 验证修复结果
SELECT 
    apm.agent_id,
    a.agent_name,
    apm.plugin_id,
    apm.param_info
FROM ai_agent_plugin_mapping apm
LEFT JOIN ai_agent a ON apm.agent_id = a.id
WHERE apm.plugin_id = 'SYSTEM_PLUGIN_CREATE_TODO'
ORDER BY apm.agent_id;
