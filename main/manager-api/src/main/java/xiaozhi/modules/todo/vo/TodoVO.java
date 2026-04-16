package xiaozhi.modules.todo.vo;

import java.util.Date;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "待办事项VO")
public class TodoVO {

    @Schema(description = "ID")
    private String id;

    @Schema(description = "用户ID")
    private Long userId;

    @Schema(description = "智能体ID")
    private String agentId;

    @Schema(description = "设备ID（MAC地址）")
    private String deviceId;

    @Schema(description = "待办标题")
    private String title;

    @Schema(description = "待办内容")
    private String content;

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

    @Schema(description = "完成时间")
    private Date completedAt;

    @Schema(description = "排序")
    private Integer sort;

    @Schema(description = "创建时间")
    private Date createDate;

    @Schema(description = "更新时间")
    private Date updateDate;
}
