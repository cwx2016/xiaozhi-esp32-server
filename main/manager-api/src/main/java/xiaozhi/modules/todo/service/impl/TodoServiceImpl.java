package xiaozhi.modules.todo.service.impl;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Date;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.page.PageData;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.modules.todo.dao.TodoDao;
import xiaozhi.modules.todo.dto.TodoQueryDTO;
import xiaozhi.modules.todo.dto.TodoSaveDTO;
import xiaozhi.modules.todo.entity.TodoEntity;
import xiaozhi.modules.todo.service.TodoService;
import xiaozhi.modules.todo.vo.TodoVO;

@Slf4j
@Service
@AllArgsConstructor
public class TodoServiceImpl extends BaseServiceImpl<TodoDao, TodoEntity> implements TodoService {

    private final TodoDao todoDao;

    @Override
    public PageData<TodoVO> page(Long userId, TodoQueryDTO queryDTO) {
        QueryWrapper<TodoEntity> wrapper = buildQueryWrapper(userId, queryDTO);
        IPage<TodoEntity> page = baseDao.selectPage(
                getPage(null, "sort", true),
                wrapper
        );
        return getPageData(page, TodoVO.class);
    }

    @Override
    public List<TodoVO> list(Long userId, TodoQueryDTO queryDTO) {
        QueryWrapper<TodoEntity> wrapper = buildQueryWrapper(userId, queryDTO);
        wrapper.orderByAsc("sort");
        wrapper.orderByDesc("create_date");
        List<TodoEntity> entities = todoDao.selectList(wrapper);
        return ConvertUtils.sourceToTarget(entities, TodoVO.class);
    }

    @Override
    public TodoVO getById(String id, Long userId) {
        QueryWrapper<TodoEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("id", id);
        wrapper.eq("user_id", userId);
        wrapper.eq("deleted", 0);
        TodoEntity entity = todoDao.selectOne(wrapper);
        if (entity == null) {
            return null;
        }
        return ConvertUtils.sourceToTarget(entity, TodoVO.class);
    }

    @Override
    public void save(TodoSaveDTO dto, Long userId) {
        Date now = new Date();

        TodoEntity entity = ConvertUtils.sourceToTarget(dto, TodoEntity.class);
        entity.setUserId(userId);
        entity.setStatus(dto.getStatus() != null ? dto.getStatus() : 0);
        entity.setPriority(dto.getPriority() != null ? dto.getPriority() : 0);
        entity.setRepeatType(StringUtils.isNotBlank(dto.getRepeatType()) ? dto.getRepeatType() : "none");
        entity.setDeleted(0);
        entity.setSort(0);
        entity.setCreator(userId);
        entity.setCreateDate(now);
        entity.setUpdater(userId);
        entity.setUpdateDate(now);

        // 如果没有设置日期时间，且是不重复类型，默认设置为第二天10:00
        if ("none".equals(entity.getRepeatType()) && StringUtils.isBlank(entity.getDueDate())) {
            LocalDate tomorrow = LocalDate.now().plusDays(1);
            entity.setDueDate(tomorrow.format(DateTimeFormatter.ofPattern("yyyy-MM-dd")));
            entity.setDueTime("10:00");
        }

        todoDao.insert(entity);
    }

    @Override
    public void update(String id, TodoSaveDTO dto, Long userId) {
        TodoEntity entity = todoDao.selectById(id);
        if (entity == null || !entity.getUserId().equals(userId) || entity.getDeleted() == 1) {
            throw new RuntimeException("待办事项不存在");
        }

        BeanUtils.copyProperties(dto, entity);
        entity.setUpdater(userId);
        entity.setUpdateDate(new Date());

        if (dto.getStatus() != null && dto.getStatus() == 1 && entity.getCompletedAt() == null) {
            entity.setCompletedAt(new Date());
        } else if (dto.getStatus() != null && dto.getStatus() == 0) {
            entity.setCompletedAt(null);
        }

        todoDao.updateById(entity);
    }

    @Override
    public void delete(String id, Long userId) {
        TodoEntity entity = todoDao.selectById(id);
        if (entity == null || !entity.getUserId().equals(userId) || entity.getDeleted() == 1) {
            throw new RuntimeException("待办事项不存在");
        }
        entity.setDeleted(1);
        entity.setUpdater(userId);
        entity.setUpdateDate(new Date());
        todoDao.updateById(entity);
    }

    @Override
    public void complete(String id, Long userId) {
        TodoEntity entity = todoDao.selectById(id);
        if (entity == null || !entity.getUserId().equals(userId) || entity.getDeleted() == 1) {
            throw new RuntimeException("待办事项不存在");
        }
        entity.setStatus(1);
        entity.setCompletedAt(new Date());
        entity.setUpdater(userId);
        entity.setUpdateDate(new Date());
        todoDao.updateById(entity);
    }

    @Override
    public void uncomplete(String id, Long userId) {
        TodoEntity entity = todoDao.selectById(id);
        if (entity == null || !entity.getUserId().equals(userId) || entity.getDeleted() == 1) {
            throw new RuntimeException("待办事项不存在");
        }
        entity.setStatus(0);
        entity.setCompletedAt(null);
        entity.setUpdater(userId);
        entity.setUpdateDate(new Date());
        todoDao.updateById(entity);
    }

    @Override
    public TodoEntity createByVoice(String title, String content, Long userId, String agentId, String deviceId, 
                                   String dueDate, String priority, String repeatType) {
        Date now = new Date();
        TodoEntity entity = new TodoEntity();

        // 智能解析标题和内容
        ParseResult parseResult = parseTodoContent(title, content);

        entity.setTitle(parseResult.getTitle());
        entity.setContent(content);
        entity.setUserId(userId);
        entity.setAgentId(agentId);
        entity.setDeviceId(deviceId);
        entity.setStatus(0);
        
        // 优先使用前端传递的参数，如果没有则使用智能解析的结果
        // 设置优先级：前端传递 > 智能解析 > 默认0（普通）
        if (priority != null && !priority.isEmpty()) {
            // 将字符串转换为Integer：high->2, medium->1, low->0
            Integer priorityValue = convertPriorityToInt(priority);
            entity.setPriority(priorityValue);
        } else {
            entity.setPriority(parseResult.getPriority() != null ? parseResult.getPriority() : 0);
        }
        
        // 设置截止日期和时间：前端传递 > 智能解析
        if (dueDate != null && !dueDate.isEmpty()) {
            try {
                // 解析日期时间字符串：YYYY-MM-DD HH:mm:ss 或 YYYY-MM-DD
                String dateStr = dueDate;
                String timeStr = null;
                
                if (dueDate.contains(" ")) {
                    // 如果包含时间部分，分离日期和时间
                    String[] parts = dueDate.split(" ", 2);
                    dateStr = parts[0];
                    if (parts.length > 1) {
                        // 提取时间部分，格式可能是 HH:mm:ss 或 HH:mm
                        String fullTime = parts[1];
                        if (fullTime.contains(":")) {
                            // 只取前两位时间（HH:mm）
                            String[] timeParts = fullTime.split(":");
                            if (timeParts.length >= 2) {
                                timeStr = timeParts[0] + ":" + timeParts[1];
                            }
                        }
                    }
                }
                
                // 验证日期格式是否为 YYYY-MM-DD
                if (dateStr.matches("\\d{4}-\\d{2}-\\d{2}")) {
                    entity.setDueDate(dateStr);
                    // 如果有时间部分，设置 dueTime
                    if (timeStr != null && !timeStr.isEmpty()) {
                        entity.setDueTime(timeStr);
                        log.info("从dueDate中提取时间: {}", timeStr);
                    } else {
                        // 如果没有时间部分，使用智能解析的结果
                        entity.setDueTime(parseResult.getDueTime());
                    }
                } else {
                    log.warn("dueDate格式不正确: {}, 使用智能解析结果", dueDate);
                    entity.setDueDate(parseResult.getDueDate());
                    entity.setDueTime(parseResult.getDueTime());
                }
            } catch (Exception e) {
                // 如果解析失败，使用智能解析的结果
                entity.setDueDate(parseResult.getDueDate());
                entity.setDueTime(parseResult.getDueTime());
                log.warn("解析dueDate失败: {}, 使用智能解析结果", dueDate, e);
            }
        } else {
            entity.setDueDate(parseResult.getDueDate());
            entity.setDueTime(parseResult.getDueTime());
        }
        
        // 设置重复类型：前端传递 > 智能解析 > 默认none
        if (repeatType != null && !repeatType.isEmpty()) {
            entity.setRepeatType(repeatType);
        } else {
            entity.setRepeatType(parseResult.getRepeatType() != null ? parseResult.getRepeatType() : "none");
        }
        
        entity.setDeleted(0);
        entity.setSort(0);
        entity.setCreator(userId);
        entity.setCreateDate(now);
        entity.setUpdater(userId);
        entity.setUpdateDate(now);

        todoDao.insert(entity);
        return entity;
    }

    /**
     * 将优先级字符串转换为整数
     * @param priority 优先级字符串 (high, medium, low)
     * @return 优先级整数 (2, 1, 0)
     */
    private Integer convertPriorityToInt(String priority) {
        if (priority == null) {
            return 0;
        }
        switch (priority.toLowerCase()) {
            case "high":
            case "紧急":
                return 2;
            case "medium":
            case "重要":
                return 1;
            case "low":
            case "普通":
            default:
                return 0;
        }
    }

    @Override
    public void batchDelete(List<String> ids, Long userId) {
        for (String id : ids) {
            try {
                delete(id, userId);
            } catch (Exception e) {
                log.error("删除待办事项失败，id: {}", id, e);
            }
        }
    }

    @Override
    public List<TodoVO> getDeviceTodoList(Long userId, String agentId, String deviceId, Integer limit) {
        QueryWrapper<TodoEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId);
        wrapper.eq("deleted", 0);
//        wrapper.eq("status", 0); // 只返回未完成的待办

        // 如果提供了 agentId 或 deviceId，进行过滤
        if (StringUtils.isNotBlank(agentId)) {
            wrapper.eq("agent_id", agentId);
        }
        if (StringUtils.isNotBlank(deviceId)) {
            wrapper.eq("device_id", deviceId);
        }

        // 按优先级和创建时间排序
        wrapper.orderByDesc("priority");
        wrapper.orderByDesc("create_date");
        wrapper.orderByAsc("due_date", "due_time");

        // 限制返回数量
        if (limit != null && limit > 0) {
            wrapper.last("LIMIT " + limit);
        }

        List<TodoEntity> entities = todoDao.selectList(wrapper);
        return ConvertUtils.sourceToTarget(entities, TodoVO.class);
    }

    @Override
    public List<TodoVO> listByMacAddress(String macAddress) {
        QueryWrapper<TodoEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("deleted", 0);
//        wrapper.eq("status", 0); // 只返回未完成的待办
        wrapper.eq("device_id", macAddress);

        // 按优先级和创建时间排序
        wrapper.orderByDesc("priority");
        wrapper.orderByDesc("create_date");
        wrapper.orderByAsc("due_date", "due_time");

        List<TodoEntity> entities = todoDao.selectList(wrapper);
        return ConvertUtils.sourceToTarget(entities, TodoVO.class);
    }

    /**
     * 构建查询条件
     */
    private QueryWrapper<TodoEntity> buildQueryWrapper(Long userId, TodoQueryDTO queryDTO) {
        QueryWrapper<TodoEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId);
        wrapper.eq("deleted", 0);

        if (queryDTO != null) {
            if (queryDTO.getStatus() != null) {
                wrapper.eq("status", queryDTO.getStatus());
            }
            if (queryDTO.getPriority() != null) {
                wrapper.eq("priority", queryDTO.getPriority());
            }
            if (StringUtils.isNotBlank(queryDTO.getAgentId())) {
                wrapper.eq("agent_id", queryDTO.getAgentId());
            }
            if (StringUtils.isNotBlank(queryDTO.getDeviceId())) {
                wrapper.eq("device_id", queryDTO.getDeviceId());
            }
            if (StringUtils.isNotBlank(queryDTO.getRepeatType())) {
                wrapper.eq("repeat_type", queryDTO.getRepeatType());
            }
            if (StringUtils.isNotBlank(queryDTO.getKeyword())) {
                wrapper.and(w -> w.like("title", queryDTO.getKeyword())
                        .or()
                        .like("content", queryDTO.getKeyword()));
            }
            if (StringUtils.isNotBlank(queryDTO.getDueDateStart())) {
                wrapper.ge("due_date", queryDTO.getDueDateStart());
            }
            if (StringUtils.isNotBlank(queryDTO.getDueDateEnd())) {
                wrapper.le("due_date", queryDTO.getDueDateEnd());
            }
        }

        return wrapper;
    }

    /**
     * 智能解析待办内容
     * 从标题和内容中提取：重复类型、优先级、日期、时间
     */
    private ParseResult parseTodoContent(String title, String content) {
        ParseResult result = new ParseResult();
        result.setTitle(title);
        result.setPriority(0);
        result.setRepeatType("none");

        String fullText = title + " " + (content != null ? content : "");

        // 解析重复类型
        if (fullText.contains("每天") || fullText.contains("每日")) {
            result.setRepeatType("daily");
        } else if (fullText.contains("每周")) {
            result.setRepeatType("weekly");
        } else if (fullText.contains("每月")) {
            result.setRepeatType("monthly");
        } else if (fullText.contains("每年") || fullText.contains("生日")) {
            result.setRepeatType("yearly");
        }

        // 解析优先级
        if (fullText.contains("紧急") || fullText.contains("重要")) {
            result.setPriority(2);
        } else if (fullText.contains("重要") || fullText.contains("优先")) {
            result.setPriority(1);
        }

        // 解析日期（格式：YYYY-MM-DD 或 YYYY/MM/DD 或 MM月DD日）
        Pattern datePattern1 = Pattern.compile("(\\d{4})[-/](\\d{1,2})[-/](\\d{1,2})");
        Matcher matcher1 = datePattern1.matcher(fullText);
        if (matcher1.find()) {
            String year = matcher1.group(1);
            String month = String.format("%02d", Integer.parseInt(matcher1.group(2)));
            String day = String.format("%02d", Integer.parseInt(matcher1.group(3)));
            result.setDueDate(year + "-" + month + "-" + day);
        } else {
            Pattern datePattern2 = Pattern.compile("(\\d{1,2})月(\\d{1,2})日");
            Matcher matcher2 = datePattern2.matcher(fullText);
            if (matcher2.find()) {
                int month = Integer.parseInt(matcher2.group(1));
                int day = Integer.parseInt(matcher2.group(2));
                int year = LocalDate.now().getYear();
                // 如果月份小于当前月份，说明是明年
                if (month < LocalDate.now().getMonthValue()) {
                    year++;
                }
                result.setDueDate(String.format("%d-%02d-%02d", year, month, day));
            }
        }

        // 解析时间（格式：HH:MM 或 HH点MM分）
        Pattern timePattern1 = Pattern.compile("(\\d{1,2}):(\\d{2})");
        Matcher matcher3 = timePattern1.matcher(fullText);
        if (matcher3.find()) {
            String hour = String.format("%02d", Integer.parseInt(matcher3.group(1)));
            String minute = matcher3.group(2);
            result.setDueTime(hour + ":" + minute);
        } else {
            Pattern timePattern2 = Pattern.compile("(\\d{1,2})点(\\d{1,2})分");
            Matcher matcher4 = timePattern2.matcher(fullText);
            if (matcher4.find()) {
                String hour = String.format("%02d", Integer.parseInt(matcher4.group(1)));
                String minute = String.format("%02d", Integer.parseInt(matcher4.group(2)));
                result.setDueTime(hour + ":" + minute);
            } else {
                Pattern timePattern3 = Pattern.compile("(\\d{1,2})点");
                Matcher matcher5 = timePattern3.matcher(fullText);
                if (matcher5.find()) {
                    String hour = String.format("%02d", Integer.parseInt(matcher5.group(1)));
                    result.setDueTime(hour + ":00");
                }
            }
        }

        // 如果没有设置日期时间，且是不重复类型，默认设置为第二天10:00
        if ("none".equals(result.getRepeatType()) && result.getDueDate() == null) {
            LocalDate tomorrow = LocalDate.now().plusDays(1);
            result.setDueDate(tomorrow.format(DateTimeFormatter.ofPattern("yyyy-MM-dd")));
            result.setDueTime("10:00");
        }

        return result;
    }

    /**
     * 解析结果内部类
     */
    private static class ParseResult {
        private String title;
        private Integer priority;
        private String dueDate;
        private String dueTime;
        private String repeatType;

        public String getTitle() {
            return title;
        }

        public void setTitle(String title) {
            this.title = title;
        }

        public Integer getPriority() {
            return priority;
        }

        public void setPriority(Integer priority) {
            this.priority = priority;
        }

        public String getDueDate() {
            return dueDate;
        }

        public void setDueDate(String dueDate) {
            this.dueDate = dueDate;
        }

        public String getDueTime() {
            return dueTime;
        }

        public void setDueTime(String dueTime) {
            this.dueTime = dueTime;
        }

        public String getRepeatType() {
            return repeatType;
        }

        public void setRepeatType(String repeatType) {
            this.repeatType = repeatType;
        }
    }
}
