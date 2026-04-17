-- ===============================
-- 修复 Liquibase 校验和错误
-- ===============================
-- 执行此脚本清除有问题的迁移记录校验和

USE xiaozhi;

-- 方法1: 删除迁移记录（推荐）
-- 这样 Liquibase 会重新执行该迁移脚本
DELETE FROM DATABASECHANGELOG WHERE ID = '202604171900';

-- 方法2: 如果不想删除记录，可以清空校验和让Liquibase重新计算
-- UPDATE DATABASECHANGELOG SET MD5SUM = NULL WHERE ID = '202604171900';

-- 验证
SELECT ID, AUTHOR, FILENAME, MD5SUM, EXECTYPE 
FROM DATABASECHANGELOG 
WHERE ID IN ('202604171830', '202604171900')
ORDER BY DATEEXECUTED DESC;
