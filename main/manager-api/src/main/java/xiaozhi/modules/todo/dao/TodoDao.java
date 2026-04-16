package xiaozhi.modules.todo.dao;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import xiaozhi.modules.todo.entity.TodoEntity;

@Mapper
public interface TodoDao extends BaseMapper<TodoEntity> {
}
