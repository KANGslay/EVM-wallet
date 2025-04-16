#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// 当前脚本路径
const scriptDir = __dirname;
const projectRoot = path.resolve(scriptDir, '..');

// Python 解释器路径
const pythonPath = '/Users/apple/anaconda3/envs/web3/bin/python';

// 使用模块方式启动 app.ai.mcp_stdio_adapter
const pythonArgs = ['-m', 'app.ai.mcp_stdio_adapter'];

// 创建日志文件
const logFile = fs.createWriteStream(path.join(projectRoot, 'mcp_stdio.log'), { flags: 'a' });
const logMessage = (msg) => {
  const timestamp = new Date().toISOString();
  logFile.write(`[${timestamp}] ${msg}
`);
};

logMessage('启动 MCP stdio 适配器');

// 处理 Windsurf 的初始化请求
const handleInitialize = (req) => {
  const response = {
    jsonrpc: '2.0',
    id: req.id,
    result: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      serverInfo: {
        name: 'EVM Wallet MCP Server',
        version: '1.0.0'
      }
    }
  };
  process.stdout.write(JSON.stringify(response) + '\n');
  logMessage('直接响应初始化请求');
  return true;
};

// 处理 Windsurf 的工具列表请求
const handleListTools = (req) => {
  // 预定义的工具列表，包含 inputSchema 字段
  const tools = [
    {
      name: 'get_wallet_balance',
      description: '查询钱包余额',
      parameters: { type: 'object', properties: {}, required: [] },
      inputSchema: { type: 'object', properties: {}, required: [] }
    },
    {
      name: 'get_transaction_history',
      description: '获取交易历史',
      parameters: { type: 'object', properties: {}, required: [] },
      inputSchema: { type: 'object', properties: {}, required: [] }
    },
    {
      name: 'import_token',
      description: '导入代币',
      parameters: {
        type: 'object',
        properties: {
          token_address: { type: 'string' },
          token_symbol: { type: 'string' }
        },
        required: ['token_address']
      },
      inputSchema: {
        type: 'object',
        properties: {
          token_address: { type: 'string' },
          token_symbol: { type: 'string' }
        },
        required: ['token_address']
      }
    },
    {
      name: 'create_wallet',
      description: '创建新钱包',
      parameters: { type: 'object', properties: {}, required: [] },
      inputSchema: { type: 'object', properties: {}, required: [] }
    },
    {
      name: 'send_transaction',
      description: '发送交易',
      parameters: {
        type: 'object',
        properties: {
          to: { type: 'string' },
          amount: { type: 'string' },
          token: { type: 'string' }
        },
        required: ['to', 'amount']
      },
      inputSchema: {
        type: 'object',
        properties: {
          to: { type: 'string' },
          amount: { type: 'string' },
          token: { type: 'string' }
        },
        required: ['to', 'amount']
      }
    }
  ];

  const response = {
    jsonrpc: '2.0',
    id: req.id,
    result: tools
  };
  process.stdout.write(JSON.stringify(response) + '\n');
  logMessage(`直接响应工具列表请求，共 ${tools.length} 个工具`);
  return true;
};

// 读取标准输入的缓冲区
let buffer = '';
process.stdin.on('data', (chunk) => {
  buffer += chunk.toString();
  
  // 处理完整的行
  const lines = buffer.split('\n');
  buffer = lines.pop(); // 保留最后一行（可能不完整）
  
  for (const line of lines) {
    if (!line.trim()) continue;
    
    try {
      const req = JSON.parse(line);
      logMessage(`收到请求: ${line}`);
      
      // 处理特殊请求
      const method = req.method || '';
      
      // 如果是初始化请求，直接处理
      if (method === 'initialize') {
        if (handleInitialize(req)) continue;
      }
      
      // 如果是工具列表请求，直接处理
      if (method === 'mcp:list-tools' || method === 'list-tools') {
        if (handleListTools(req)) continue;
      }
      
      // 其他请求转发给 Python
      pythonProcess.stdin.write(line + '\n');
      
    } catch (err) {
      logMessage(`解析JSON错误: ${err.message}, 输入: ${line}`);
    }
  }
});

// 确保工作目录是项目根目录
const pythonProcess = spawn(pythonPath, pythonArgs, {
  stdio: ['pipe', 'pipe', 'pipe'],
  cwd: projectRoot
});

// 处理 Python 输出
pythonProcess.stdout.on('data', (data) => {
  // 直接将 Python 输出写入标准输出
  process.stdout.write(data);
  logMessage(`Python 输出: ${data.toString().trim()}`);
});

// 处理 Python 错误
pythonProcess.stderr.on('data', (data) => {
  // 记录到日志文件，但不输出到标准错误
  logMessage(`Python 错误: ${data.toString().trim()}`);
});

// 处理 Python 进程结束
pythonProcess.on('close', (code) => {
  logMessage(`Python 进程退出，退出码: ${code}`);
  process.exit(code);
});

// 处理信号
process.on('SIGINT', () => {
  logMessage('收到 SIGINT，关闭 Python');
  pythonProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
  logMessage('收到 SIGTERM，关闭 Python');
  pythonProcess.kill('SIGTERM');
});
