package xiaozhi.modules.todo.controller;

import java.util.List;

import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import xiaozhi.common.page.PageData;
import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.security.user.SecurityUser;
import xiaozhi.modules.todo.dto.TodoQueryDTO;
import xiaozhi.modules.todo.dto.TodoSaveDTO;
import xiaozhi.modules.todo.entity.TodoEntity;
import xiaozhi.modules.todo.service.TodoService;
import xiaozhi.modules.todo.vo.TodoVO;

@Tag(name = "待办事项管理")
@RestController
@RequestMapping("/todo")
public class TodoController {

    private final TodoService todoService;

    public TodoController(TodoService todoService) {
        this.todoService = todoService;
    }

    @GetMapping("/page")
    @Operation(summary = "分页查询待办列表")
    @RequiresPermissions("sys:role:normal")
    public Result<PageData<TodoVO>> page(TodoQueryDTO queryDTO) {
        UserDetail user = SecurityUser.getUser();
        PageData<TodoVO> page = todoService.page(user.getId(), queryDTO);
        return new Result<PageData<TodoVO>>().ok(page);
    }

    @GetMapping("/list")
    @Operation(summary = "查询待办列表")
    @RequiresPermissions("sys:role:normal")
    public Result<List<TodoVO>> list(TodoQueryDTO queryDTO) {
        UserDetail user = SecurityUser.getUser();
        List<TodoVO> list = todoService.list(user.getId(), queryDTO);
        return new Result<List<TodoVO>>().ok(list);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取待办详情")
    @RequiresPermissions("sys:role:normal")
    public Result<TodoVO> getById(@PathVariable String id) {
        UserDetail user = SecurityUser.getUser();
        TodoVO todo = todoService.getById(id, user.getId());
        if (todo == null) {
            return new Result<TodoVO>().error("待办事项不存在");
        }
        return new Result<TodoVO>().ok(todo);
    }

    @PostMapping
    @Operation(summary = "创建待办事项")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> save(@Valid @RequestBody TodoSaveDTO dto) {
        UserDetail user = SecurityUser.getUser();
        todoService.save(dto, user.getId());
        return new Result<>();
    }

    @PutMapping("/{id}")
    @Operation(summary = "更新待办事项")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> update(@PathVariable String id, @Valid @RequestBody TodoSaveDTO dto) {
        UserDetail user = SecurityUser.getUser();
        todoService.update(id, dto, user.getId());
        return new Result<>();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除待办事项（逻辑删除）")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> delete(@PathVariable String id) {
        UserDetail user = SecurityUser.getUser();
        todoService.delete(id, user.getId());
        return new Result<>();
    }

    @PostMapping("/batch-delete")
    @Operation(summary = "批量删除待办事项（逻辑删除）")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> batchDelete(@RequestBody List<String> ids) {
        UserDetail user = SecurityUser.getUser();
        todoService.batchDelete(ids, user.getId());
        return new Result<>();
    }

    @PutMapping("/{id}/complete")
    @Operation(summary = "标记为已完成")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> complete(@PathVariable String id) {
        UserDetail user = SecurityUser.getUser();
        todoService.complete(id, user.getId());
        return new Result<>();
    }

    @PutMapping("/{id}/uncomplete")
    @Operation(summary = "取消完成")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> uncomplete(@PathVariable String id) {
        UserDetail user = SecurityUser.getUser();
        todoService.uncomplete(id, user.getId());
        return new Result<>();
    }

    @PostMapping("/voice/create")
    @Operation(summary = "语音创建待办（小智调用）- 智能解析重复类型、日期时间等")
    public Result<String> createByVoice(@RequestBody VoiceTodoRequest request) {
        UserDetail user = SecurityUser.getUser();
        String title = request.getTitle();
        String content = request.getContent();
        String agentId = request.getAgentId();
        String deviceId = request.getDeviceId();
        
        if (title == null || title.trim().isEmpty()) {
            return new Result<String>().error("标题不能为空");
        }
        
        TodoEntity entity = todoService.createByVoice(title, content, user.getId(), agentId, deviceId);
        return new Result<String>().ok(entity.getId());
    }

    /**
     * 语音创建待办请求对象
     */
    public static class VoiceTodoRequest {
        private String title;
        private String content;
        private String agentId;
        private String deviceId;

        public String getTitle() {
            return title;
        }

        public void setTitle(String title) {
            this.title = title;
        }

        public String getContent() {
            return content;
        }

        public void setContent(String content) {
            this.content = content;
        }

        public String getAgentId() {
            return agentId;
        }

        public void setAgentId(String agentId) {
            this.agentId = agentId;
        }

        public String getDeviceId() {
            return deviceId;
        }

        public void setDeviceId(String deviceId) {
            this.deviceId = deviceId;
        }
    }
}
