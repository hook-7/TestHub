# 统一错误处理文档

## 🎯 设计目标

统一所有API的错误返回格式，提供一致的错误码和错误消息，便于前端处理和用户理解。

## 📋 错误码规范

### 基础错误码
- `0`: 成功
- `400`: 参数错误
- `500`: 系统内部错误

### 业务错误码 (1000+)

#### 串口相关 (1000-1099)
- `1001`: 未检测到可用串口
- `1002`: 串口连接失败
- `1003`: 串口断开失败
- `1004`: 串口未连接
- `1005`: 串口读取失败
- `1006`: 串口写入失败
- `1007`: 无效的串口数据格式
- `1008`: 串口通信超时
- `1009`: 串口设备错误

#### 通信协议相关 (1100-1199)
- `1101`: 协议校验错误
- `1102`: 协议响应无效
- `1103`: 从站设备错误
- `1104`: 协议功能码错误

#### 配置相关 (1200-1299)
- `1201`: 无效的串口配置
- `1202`: 无效的波特率配置
- `1203`: 无效的配置参数

## 📝 响应格式

所有API都遵循统一的响应格式：

```json
{
  "code": 0,
  "msg": "success",
  "data": {...}
}
```

### 成功响应示例
```json
{
  "code": 0,
  "msg": "获取串口列表成功",
  "data": [
    {
      "device": "/dev/ttyUSB0",
      "name": "USB Serial",
      "description": "USB-Serial Controller",
      "hwid": "USB VID:PID=1A86:7523",
      "manufacturer": "QinHeng Electronics"
    }
  ]
}
```

### 错误响应示例

#### 参数验证错误 (400)
```json
{
  "code": 400,
  "msg": "参数 'slave_id' Input should be less than or equal to 247",
  "data": null
}
```

#### 业务错误 (1004)
```json
{
  "code": 1004,
  "msg": "串口未连接",
  "data": null
}
```

#### 系统错误 (500)
```json
{
  "code": 500,
  "msg": "系统内部错误，请联系管理员",
  "data": null
}
```

## 🏗️ 技术实现

### 1. 异常类层次结构

```python
# 基础异常类
class HMIException(Exception):
    def __init__(self, error_code: ErrorCode, message: str, details: Any = None)

# 具体业务异常
class SerialException(HMIException)      # 串口相关异常
class ProtocolException(HMIException)    # 协议相关异常  
class ConfigException(HMIException)      # 配置相关异常
```

### 2. 全局异常处理器

系统注册了以下异常处理器：
- `HMIException`: 处理业务异常
- `HTTPException`: 处理HTTP异常 (404, 405等)
- `RequestValidationError`: 处理参数验证异常
- `Exception`: 处理未捕获的系统异常

### 3. 服务层异常抛出

服务层统一抛出具体的业务异常：

```python
# ❌ 旧方式 - 返回None或False
async def read_registers(self, request) -> Optional[Response]:
    try:
        # ... 业务逻辑
        return result
    except Exception:
        return None  # 错误信息丢失

# ✅ 新方式 - 抛出具体异常
async def read_registers(self, request) -> Response:
    try:
        if not serial_driver.is_connected:
            raise SerialException(ErrorCode.SERIAL_NOT_CONNECTED, "串口未连接")
        # ... 业务逻辑
        return result
    except SerialException:
        raise  # 重新抛出业务异常
    except Exception as e:
        raise SerialException(ErrorCode.SERIAL_READ_FAILED, f"读取异常: {e}")
```

### 4. API层简化

API端点不再需要复杂的异常处理：

```python
# ❌ 旧方式 - 复杂的异常处理
@router.post("/read-registers")
async def read_registers(request: ReadRegistersRequest):
    try:
        result = await serial_service.read_registers(request)
        if result:
            return APIResponse.success(data=result)
        else:
            return APIResponse.business_error(4, "读取失败")
    except Exception as e:
        return APIResponse.system_error("读取异常")

# ✅ 新方式 - 简洁的业务逻辑
@router.post("/read-registers")
async def read_registers(request: ReadRegistersRequest):
    result = await serial_service.read_registers(request)
    return APIResponse.success(data=result, msg="读取寄存器成功")
```

## 🧪 测试方法

### 1. 运行错误处理测试
```bash
./test_errors_curl.sh
```

### 2. 手动测试示例

#### 测试参数验证
```bash
curl -X POST http://localhost:8000/api/v1/serial/read-registers \
  -H "Content-Type: application/json" \
  -d '{"slave_id": 999, "start_addr": -1}'
```

#### 测试业务异常
```bash
curl -X POST http://localhost:8000/api/v1/serial/read-registers \
  -H "Content-Type: application/json" \
  -d '{"slave_id": 1, "start_addr": 0, "count": 1, "function_code": 3}'
```

## 📈 优势

1. **一致性**: 所有API使用相同的错误格式
2. **可维护性**: 错误处理逻辑集中管理
3. **可扩展性**: 易于添加新的错误类型和处理器
4. **调试友好**: 详细的错误日志和堆栈跟踪
5. **用户体验**: 清晰的错误消息，便于前端展示

## 🔧 前端集成

前端axios拦截器会自动处理错误响应：

```typescript
// 响应拦截器自动处理错误
api.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.code !== 0) {
      ElMessage.error(data.msg || '请求失败')
      return Promise.reject(new Error(data.msg))
    }
    return data
  },
  (error) => {
    ElMessage.error(error.response?.data?.msg || '网络错误')
    return Promise.reject(error)
  }
)
```

这样前端只需要关注业务逻辑，错误会自动显示给用户。