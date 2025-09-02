"""
Serial Login Configuration Service
串口登录配置服务
"""

import logging
import json
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from app.core.exceptions import SerialException, ErrorCode
from app.services.serial_service import serial_service
from app.schemas.serial_login_schemas import (
    CreateSerialLoginConfigRequest,
    UpdateSerialLoginConfigRequest,
    SerialLoginTestRequest,
    SerialLoginConfigResponse,
    SerialLoginTestResponse,
    SerialLoginConfig
)

logger = logging.getLogger(__name__)


class SerialLoginService:
    """串口登录配置服务"""
    
    def __init__(self):
        self.config_file = Path("data/serial_login_configs.json")
        self.config_file.parent.mkdir(exist_ok=True)
        self._configs: Dict[int, Dict[str, Any]] = {}
        self._next_id = 1
        self._active_config_id: Optional[int] = None
        self._load_configs()
    
    def _load_configs(self):
        """从文件加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._configs = {int(k): v for k, v in data.get('configs', {}).items()}
                    self._next_id = data.get('next_id', 1)
                    self._active_config_id = data.get('active_config_id')
                    logger.info(f"已加载 {len(self._configs)} 个串口登录配置")
            else:
                logger.info("配置文件不存在，使用空配置")
        except Exception as e:
            logger.error(f"加载串口登录配置失败: {e}")
            self._configs = {}
            self._next_id = 1
            self._active_config_id = None
    
    def _save_configs(self):
        """保存配置到文件"""
        try:
            data = {
                'configs': self._configs,
                'next_id': self._next_id,
                'active_config_id': self._active_config_id
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存串口登录配置失败: {e}")
            raise SerialException(ErrorCode.SYSTEM_ERROR, f"保存配置失败: {str(e)}")
    
    async def get_all_configs(self) -> List[SerialLoginConfigResponse]:
        """获取所有配置"""
        configs = []
        for config_id, config_data in self._configs.items():
            config_data['id'] = config_id
            config_data['is_active'] = (config_id == self._active_config_id)
            configs.append(SerialLoginConfigResponse(**config_data))
        return configs
    
    async def get_config_by_id(self, config_id: int) -> Optional[SerialLoginConfigResponse]:
        """根据ID获取配置"""
        if config_id not in self._configs:
            return None
        
        config_data = self._configs[config_id].copy()
        config_data['id'] = config_id
        config_data['is_active'] = (config_id == self._active_config_id)
        return SerialLoginConfigResponse(**config_data)
    
    async def create_config(self, request: CreateSerialLoginConfigRequest) -> SerialLoginConfigResponse:
        """创建新配置"""
        # 检查名称是否重复
        for config_data in self._configs.values():
            if config_data['name'] == request.name:
                raise SerialException(ErrorCode.BUSINESS_ERROR, f"配置名称 '{request.name}' 已存在")
        
        # 创建配置
        config_id = self._next_id
        self._next_id += 1
        
        now = datetime.now().isoformat()
        config_data = {
            'name': request.name,
            'port': request.port,
            'baudrate': request.baudrate,
            'bytesize': request.bytesize,
            'parity': request.parity,
            'stopbits': request.stopbits,
            'timeout': request.timeout,
            'auto_connect': request.auto_connect,
            'login_command': request.login_command,
            'expected_response': request.expected_response,
            'retry_count': request.retry_count,
            'retry_delay': request.retry_delay,
            'created_at': now,
            'updated_at': now
        }
        
        self._configs[config_id] = config_data
        self._save_configs()
        
        # 返回响应
        config_data['id'] = config_id
        config_data['is_active'] = False
        return SerialLoginConfigResponse(**config_data)
    
    async def update_config(self, config_id: int, request: UpdateSerialLoginConfigRequest) -> Optional[SerialLoginConfigResponse]:
        """更新配置"""
        if config_id not in self._configs:
            return None
        
        config_data = self._configs[config_id]
        
        # 检查名称是否重复（排除自己）
        if request.name:
            for other_id, other_config in self._configs.items():
                if other_id != config_id and other_config['name'] == request.name:
                    raise SerialException(ErrorCode.BUSINESS_ERROR, f"配置名称 '{request.name}' 已存在")
        
        # 更新字段
        update_fields = request.dict(exclude_unset=True)
        for field, value in update_fields.items():
            config_data[field] = value
        
        config_data['updated_at'] = datetime.now().isoformat()
        self._save_configs()
        
        # 返回响应
        config_data['id'] = config_id
        config_data['is_active'] = (config_id == self._active_config_id)
        return SerialLoginConfigResponse(**config_data)
    
    async def delete_config(self, config_id: int) -> bool:
        """删除配置"""
        if config_id not in self._configs:
            return False
        
        # 如果删除的是激活配置，清除激活状态
        if self._active_config_id == config_id:
            self._active_config_id = None
        
        del self._configs[config_id]
        self._save_configs()
        return True
    
    async def activate_config(self, config_id: int) -> bool:
        """激活配置"""
        if config_id not in self._configs:
            return False
        
        self._active_config_id = config_id
        self._save_configs()
        return True
    
    async def get_active_config(self) -> Optional[SerialLoginConfigResponse]:
        """获取激活的配置"""
        if not self._active_config_id or self._active_config_id not in self._configs:
            return None
        
        return await self.get_config_by_id(self._active_config_id)
    
    async def test_config(self, request: SerialLoginTestRequest) -> SerialLoginTestResponse:
        """测试配置"""
        start_time = time.time()
        
        try:
            # 获取配置
            if request.config_id:
                config_data = self._configs.get(request.config_id)
                if not config_data:
                    raise SerialException(ErrorCode.BUSINESS_ERROR, "配置不存在")
                config = SerialLoginConfig(**config_data)
            elif request.temp_config:
                config = request.temp_config
            else:
                raise SerialException(ErrorCode.BUSINESS_ERROR, "必须提供配置ID或临时配置")
            
            # 测试串口连接
            connection_start = time.time()
            
            # 检查串口是否可用
            available_ports = await serial_service.get_available_ports()
            port_exists = any(port.device == config.port for port in available_ports)
            if not port_exists:
                return SerialLoginTestResponse(
                    success=False,
                    message=f"串口 {config.port} 不可用",
                    connection_time=time.time() - connection_start,
                    error_details="指定的串口设备不存在或无法访问"
                )
            
            # 尝试连接串口
            try:
                # 断开现有连接
                if await serial_service.is_connected():
                    await serial_service.disconnect()
                
                # 连接串口
                await serial_service.connect(
                    port=config.port,
                    baudrate=config.baudrate,
                    bytesize=config.bytesize,
                    parity=config.parity,
                    stopbits=config.stopbits,
                    timeout=config.timeout
                )
                
                connection_time = time.time() - connection_start
                
                # 如果有登录命令，执行登录测试
                login_time = None
                response_data = None
                
                if config.login_command:
                    login_start = time.time()
                    
                    for attempt in range(config.retry_count):
                        try:
                            # 发送登录命令
                            response = await serial_service.send_raw_data(config.login_command)
                            response_data = response.received_data
                            
                            # 检查期望响应
                            if config.expected_response:
                                if config.expected_response in response_data:
                                    login_time = time.time() - login_start
                                    break
                                else:
                                    if attempt < config.retry_count - 1:
                                        await asyncio.sleep(config.retry_delay)
                                        continue
                                    else:
                                        return SerialLoginTestResponse(
                                            success=False,
                                            message="登录命令执行失败：响应不匹配",
                                            connection_time=connection_time,
                                            login_time=time.time() - login_start,
                                            response_data=response_data,
                                            error_details=f"期望响应: {config.expected_response}, 实际响应: {response_data}"
                                        )
                            else:
                                login_time = time.time() - login_start
                                break
                                
                        except Exception as e:
                            if attempt < config.retry_count - 1:
                                await asyncio.sleep(config.retry_delay)
                                continue
                            else:
                                return SerialLoginTestResponse(
                                    success=False,
                                    message=f"登录命令执行失败：{str(e)}",
                                    connection_time=connection_time,
                                    login_time=time.time() - login_start,
                                    error_details=str(e)
                                )
                
                # 测试成功
                total_time = time.time() - start_time
                return SerialLoginTestResponse(
                    success=True,
                    message="配置测试成功",
                    connection_time=connection_time,
                    login_time=login_time,
                    response_data=response_data
                )
                
            except Exception as e:
                connection_time = time.time() - connection_start
                return SerialLoginTestResponse(
                    success=False,
                    message=f"串口连接失败：{str(e)}",
                    connection_time=connection_time,
                    error_details=str(e)
                )
            
        except SerialException:
            raise
        except Exception as e:
            return SerialLoginTestResponse(
                success=False,
                message=f"测试过程中发生错误：{str(e)}",
                connection_time=time.time() - start_time,
                error_details=str(e)
            )
    
    async def connect_with_active_config(self) -> bool:
        """使用激活的配置连接串口"""
        if not self._active_config_id or self._active_config_id not in self._configs:
            return False
        
        config_data = self._configs[self._active_config_id]
        config = SerialLoginConfig(**config_data)
        
        try:
            # 断开现有连接
            if await serial_service.is_connected():
                await serial_service.disconnect()
            
            # 连接串口
            await serial_service.connect(
                port=config.port,
                baudrate=config.baudrate,
                bytesize=config.bytesize,
                parity=config.parity,
                stopbits=config.stopbits,
                timeout=config.timeout
            )
            
            # 如果有登录命令，执行登录
            if config.login_command:
                for attempt in range(config.retry_count):
                    try:
                        response = await serial_service.send_raw_data(config.login_command)
                        
                        # 检查期望响应
                        if config.expected_response:
                            if config.expected_response in response.received_data:
                                break
                            else:
                                if attempt < config.retry_count - 1:
                                    await asyncio.sleep(config.retry_delay)
                                    continue
                                else:
                                    raise SerialException(ErrorCode.BUSINESS_ERROR, "登录失败：响应不匹配")
                        else:
                            break
                            
                    except Exception as e:
                        if attempt < config.retry_count - 1:
                            await asyncio.sleep(config.retry_delay)
                            continue
                        else:
                            raise SerialException(ErrorCode.BUSINESS_ERROR, f"登录失败：{str(e)}")
            
            logger.info(f"使用配置 '{config_data['name']}' 成功连接串口 {config.port}")
            return True
            
        except Exception as e:
            logger.error(f"使用激活配置连接失败: {e}")
            raise SerialException(ErrorCode.BUSINESS_ERROR, f"连接失败：{str(e)}")


# 创建全局服务实例
serial_login_service = SerialLoginService()