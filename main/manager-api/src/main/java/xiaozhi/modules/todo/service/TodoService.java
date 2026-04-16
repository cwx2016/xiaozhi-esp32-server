package xiaozhi.modules.todo.service;

import java.util.List;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.todo.dto.TodoQueryDTO;
import xiaozhi.modules.todo.dto.TodoSaveDTO;
import xiaozhi.modules.todo.entity.TodoEntity;
import xiaozhi.modules.todo.vo.TodoVO;

public interface TodoService extends BaseService<TodoEntity> {

    /**
     * 分页查询待办列表
     */
    PageData<TodoVO> page(Long userId, TodoQueryDTO queryDTO);

    /**
     * 查询待办列表
     */
    List<TodoVO> list(Long userId, TodoQueryDTO queryDTO);

    /**
     * 获取待办详情
     */
    TodoVO getById(String id, Long userId);

    /**
     * 创建待办事项
     */
    void save(TodoSaveDTO dto, Long userId);

    /**
     * 更新待办事项
     */
    void update(String id, TodoSaveDTO dto, Long userId);

    /**
     * 删除待办事项（逻辑删除）
     */
    void delete(String id, Long userId);

    /**
     * 标记为已完成
     */
    void complete(String id, Long userId);

    /**
     * 取消完成
     */
    void uncomplete(String id, Long userId);

    /**
     * 语音创建待办（小智调用）
     * 支持智能解析：重复类型、日期时间等
     */
    TodoEntity createByVoice(String title, String content, Long userId, String agentId, String deviceId);

    /**
     * 批量删除待办事项（逻辑删除）
     */
    void batchDelete(List<String> ids, Long userId);
}
