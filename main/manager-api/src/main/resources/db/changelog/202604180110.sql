-- ===============================
-- 为所有智能体关联完成待办和删除待办插件
-- ===============================
START TRANSACTION;

-- 1. 为所有智能体关联 complete_todo 插件
INSERT INTO ai_agent_plugin_mapping (agent_id, plugin_id, param_info)
SELECT a.id, 'SYSTEM_PLUGIN_COMPLETE_TODO', 
       JSON_OBJECT('manager_api_url', 'http://localhost:8002', 'api_key', '')
FROM ai_agent a
WHERE NOT EXISTS (
    SELECT 1 FROM ai_agent_plugin_mapping apm 
    WHERE apm.agent_id = a.id AND apm.plugin_id = 'SYSTEM_PLUGIN_COMPLETE_TODO'
);

-- 2. 为所有智能体关联 delete_todo 插件
INSERT INTO ai_agent_plugin_mapping (agent_id, plugin_id, param_info)
SELECT a.id, 'SYSTEM_PLUGIN_DELETE_TODO',
       JSON_OBJECT('manager_api_url', 'http://localhost:8002', 'api_key', '')
FROM ai_agent a
WHERE NOT EXISTS (
    SELECT 1 FROM ai_agent_plugin_mapping apm 
    WHERE apm.agent_id = a.id AND apm.plugin_id = 'SYSTEM_PLUGIN_DELETE_TODO'
);

COMMIT;
