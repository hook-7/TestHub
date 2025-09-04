
# Element Plus Icons 参考

## 自动化模块使用的图标

### 命令类型图标
- **系统命令**: Setting
- **设备命令**: Monitor  
- **测试命令**: Operation
- **维护命令**: Tools

### 状态图标
- **等待**: Clock
- **执行中**: Loading
- **成功**: Check
- **失败**: Close
- **取消**: CircleClose
- **警告**: Warning

### 操作图标
- **添加**: Plus
- **文档**: Document
- **刷新**: Refresh
- **下拉**: ArrowDown

### 使用示例
```vue
<script setup>
import { Setting, Monitor, Operation, Tools } from '@element-plus/icons-vue'

const getCommandIcon = (type) => {
  const icons = {
    system: Setting,
    device: Monitor, 
    test: Operation,
    maintenance: Tools
  }
  return icons[type] || Setting
}
</script>
```

## 注意事项
- 避免使用可能不存在的图标如: TestTube, Experiment, Flask
- 优先使用通用图标: Operation, Document, Setting
- 测试前确认图标在 @element-plus/icons-vue 中存在
