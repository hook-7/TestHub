#!/usr/bin/env node

/**
 * 前端功能自动化测试脚本
 * 使用 Node.js 和 fetch API 测试前端功能
 */

const baseUrl = 'http://localhost:3000';
const apiUrl = 'http://localhost:8000/api/v1';

// 测试结果收集
const testResults = {
  passed: 0,
  failed: 0,
  tests: []
};

// 测试函数
async function runTest(name, testFn) {
  try {
    console.log(`🧪 运行测试: ${name}`);
    await testFn();
    testResults.passed++;
    testResults.tests.push({ name, status: 'PASSED' });
    console.log(`✅ ${name} - 通过\n`);
  } catch (error) {
    testResults.failed++;
    testResults.tests.push({ name, status: 'FAILED', error: error.message });
    console.log(`❌ ${name} - 失败: ${error.message}\n`);
  }
}

// 测试 API 健康检查
async function testAPIHealth() {
  const response = await fetch(`${apiUrl}/health`);
  const data = await response.json();
  
  if (data.code !== 0) {
    throw new Error(`API健康检查失败: ${data.msg}`);
  }
  
  console.log(`   API状态: ${data.data.status}`);
}

// 测试前端页面加载
async function testFrontendPages() {
  const pages = [
    { path: '/', name: '首页' },
    { path: '/serial-config', name: '串口配置' },
    { path: '/communication', name: 'AT指令交互' },
    { path: '/workflow', name: '工作流管理' },
    { path: '/workflow-orchestration', name: '工作流编排' }
  ];
  
  for (const page of pages) {
    const response = await fetch(`${baseUrl}${page.path}`);
    if (!response.ok) {
      throw new Error(`${page.name}页面加载失败: ${response.status}`);
    }
    console.log(`   ${page.name}页面: OK`);
  }
}

// 测试工作流功能
async function testWorkflowFeatures() {
  // 1. 获取工作流列表
  const listResponse = await fetch(`${apiUrl}/workflows/`);
  const listData = await listResponse.json();
  
  if (listData.code !== 0) {
    throw new Error(`获取工作流列表失败: ${listData.msg}`);
  }
  
  console.log(`   工作流列表: 找到 ${listData.data.total} 个工作流`);
  
  // 2. 创建工作流
  const createResponse = await fetch(`${apiUrl}/workflows/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: '自动化测试工作流',
      description: '由自动化测试创建',
      nodes: [
        {
          id: 'node_start',
          type: 'start',
          name: '开始',
          position: { x: 100, y: 100 },
          status: 'pending',
          config: {}
        },
        {
          id: 'node_end',
          type: 'end',
          name: '结束',
          position: { x: 300, y: 100 },
          status: 'pending',
          config: {}
        }
      ],
      connections: []
    })
  });
  
  const createData = await createResponse.json();
  if (createData.code !== 0) {
    throw new Error(`创建工作流失败: ${createData.msg}`);
  }
  
  const workflowId = createData.data.id;
  console.log(`   创建工作流: ${workflowId}`);
  
  // 3. 执行工作流
  const executeResponse = await fetch(`${apiUrl}/workflows/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      workflow_id: workflowId,
      mac_address: '026501123456',
      serial_number: '25990000001',
      operator: '自动化测试',
      workstation: '测试工位',
      device_id: '测试设备'
    })
  });
  
  const executeData = await executeResponse.json();
  if (executeData.code !== 0) {
    throw new Error(`执行工作流失败: ${executeData.msg}`);
  }
  
  console.log(`   执行工作流: ${executeData.data.id}`);
  
  // 4. 获取统计信息
  const statsResponse = await fetch(`${apiUrl}/workflows/stats`);
  const statsData = await statsResponse.json();
  
  if (statsData.code !== 0) {
    throw new Error(`获取统计信息失败: ${statsData.msg}`);
  }
  
  console.log(`   统计信息: 总工作流数 ${statsData.data.total_workflows}`);
}

// 测试命令管理功能
async function testCommandFeatures() {
  // 获取命令列表
  const response = await fetch(`${apiUrl}/commands/`);
  const data = await response.json();
  
  if (data.code !== 0) {
    throw new Error(`获取命令列表失败: ${data.msg}`);
  }
  
  console.log(`   命令列表: 找到 ${data.data.total} 个命令`);
  
  // 检查是否有测试命令
  const testCommands = data.data.commands.filter(cmd => 
    cmd.name.includes('测试') || cmd.name.includes('LED')
  );
  
  if (testCommands.length === 0) {
    throw new Error('未找到测试命令');
  }
  
  console.log(`   测试命令: 找到 ${testCommands.length} 个`);
}

// 测试测试结果功能
async function testTestResultFeatures() {
  // 获取测试结果列表
  const response = await fetch(`${apiUrl}/test-results/`);
  const data = await response.json();
  
  if (data.code !== 0) {
    throw new Error(`获取测试结果列表失败: ${data.msg}`);
  }
  
  console.log(`   测试结果: 找到 ${data.data.results.length} 条记录`);
  
  // 检查是否有测试数据
  if (data.data.results.length > 0) {
    const latestResult = data.data.results[0];
    console.log(`   最新测试: MAC ${latestResult.mac_address}, 通过率 ${Math.round(latestResult.passed_tests / latestResult.total_tests * 100)}%`);
  }
}

// 主测试函数
async function runAllTests() {
  console.log('🚀 开始前端功能自动化测试\n');
  
  await runTest('API健康检查', testAPIHealth);
  await runTest('前端页面加载', testFrontendPages);
  await runTest('工作流功能', testWorkflowFeatures);
  await runTest('命令管理功能', testCommandFeatures);
  await runTest('测试结果功能', testTestResultFeatures);
  
  // 输出测试结果
  console.log('📊 测试结果汇总:');
  console.log(`✅ 通过: ${testResults.passed}`);
  console.log(`❌ 失败: ${testResults.failed}`);
  console.log(`📈 成功率: ${Math.round(testResults.passed / (testResults.passed + testResults.failed) * 100)}%`);
  
  if (testResults.failed > 0) {
    console.log('\n❌ 失败的测试:');
    testResults.tests
      .filter(t => t.status === 'FAILED')
      .forEach(t => console.log(`   - ${t.name}: ${t.error}`));
  }
  
  console.log('\n🎉 测试完成!');
}

// 运行测试
runAllTests().catch(console.error);