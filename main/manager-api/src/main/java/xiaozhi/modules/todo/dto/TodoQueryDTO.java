package xiaozhi.modules.todo.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "待办事项查询DTO")
public class TodoQueryDTO {

    @Schema(description = "状态：0-未完成，1-已完成")
    private Integer status;

    @Schema(description = "优先级：0-普通，1-重要，2-紧急")
    private Integer priority;

    @Schema(description = "智能体ID")
    private String agentId;

    @Schema(description = "设备ID")
    private String deviceId;

    @Schema(description = "重复类型")
    private String repeatType;

    @Schema(description = "关键词搜索")
    private String keyword;

    @Schema(description = "截止日期开始")
    private String dueDateStart;

    @Schema(description = "截止日期结束")
    private String dueDateEnd;
}
