package xiaozhi.modules.todo.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "待办事项保存DTO")
public class TodoSaveDTO {

    @Schema(description = "待办标题")
    @NotBlank(message = "标题不能为空")
    private String title;

    @Schema(description = "待办内容")
    private String content;

    @Schema(description = "智能体ID")
    private String agentId;

    @Schema(description = "设备ID（MAC地址）")
    private String deviceId;

    @Schema(description = "状态：0-未完成，1-已完成")
    private Integer status;

    @Schema(description = "优先级：0-普通，1-重要，2-紧急")
    private Integer priority;

    @Schema(description = "截止日期，格式：2025-12-31")
    private String dueDate;

    @Schema(description = "截止时间，格式：10:00")
    private String dueTime;

    @Schema(description = "重复类型：none-不重复、daily-每天、weekly-每周、monthly-每月、yearly-每年")
    private String repeatType;
}
