package xiaozhi.modules.todo.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_todo")
@Schema(description = "待办事项")
public class TodoEntity {

    @TableId(type = IdType.ASSIGN_UUID)
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

    @Schema(description = "逻辑删除：0-未删除，1-已删除")
    private Integer deleted;

    @Schema(description = "排序")
    private Integer sort;

    @Schema(description = "更新者")
    @TableField(fill = FieldFill.UPDATE)
    private Long updater;

    @Schema(description = "更新时间")
    @TableField(fill = FieldFill.UPDATE)
    private Date updateDate;

    @Schema(description = "创建者")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "创建时间")
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;
}
