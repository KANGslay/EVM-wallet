// EVM托管钱包系统前端应用

// API基础URL
const API_BASE_URL = 'http://localhost:8081/api';

// 全局状态
const state = {
    user: null,
    token: localStorage.getItem('token'),
    wallet: null,
    currentPage: 'welcome',
    transactions: [],
    balances: {},
    pagination: {
        currentPage: 1,
        pageSize: 10,
        totalItems: 0
    }
};

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 初始化导航事件
    initNavigation();
    
    // 初始化表单提交事件
    initForms();
    
    // 检查登录状态
    checkAuthStatus();
});

// 初始化导航
function initNavigation() {
    // 导航链接点击事件
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.getAttribute('data-page');
            navigateTo(page);
        });
    });
    
    // 退出按钮点击事件
    document.getElementById('logout-btn').addEventListener('click', logout);
}

// 初始化表单
function initForms() {
    // 登录表单
    document.getElementById('login-form').addEventListener('submit', (e) => {
        e.preventDefault();
        login();
    });
    
    // 注册表单
    document.getElementById('register-form').addEventListener('submit', (e) => {
        e.preventDefault();
        register();
    });
    
    // 发送资产表单
    document.getElementById('send-form').addEventListener('submit', (e) => {
        e.preventDefault();
        showTransactionConfirmation();
    });
    
    // 确认交易按钮
    document.getElementById('confirm-transaction-btn').addEventListener('click', sendTransaction);
    
    // 导入代币表单
    document.getElementById('import-token-form').addEventListener('submit', (e) => {
        e.preventDefault();
        importToken();
    });
    
    // 创建钱包按钮
    document.getElementById('create-wallet-btn').addEventListener('click', createWallet);
    
    // AI聊天表单
    document.getElementById('chat-form').addEventListener('submit', (e) => {
        e.preventDefault();
        sendChatMessage();
    });
    
    // 分页控制
    document.getElementById('prev-page').addEventListener('click', (e) => {
        e.preventDefault();
        if (state.pagination.currentPage > 1) {
            state.pagination.currentPage--;
            loadTransactions();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', (e) => {
        e.preventDefault();
        const totalPages = Math.ceil(state.pagination.totalItems / state.pagination.pageSize);
        if (state.pagination.currentPage < totalPages) {
            state.pagination.currentPage++;
            loadTransactions();
        }
    });
    
    document.getElementById('page-size').addEventListener('change', (e) => {
        state.pagination.pageSize = parseInt(e.target.value);
        state.pagination.currentPage = 1;
        loadTransactions();
    });
}

// 检查认证状态
function checkAuthStatus() {
    if (state.token) {
        // 有token，尝试获取用户信息
        axios.get(`${API_BASE_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${state.token}` }
        })
        .then(response => {
            state.user = response.data;
            updateUIForLoggedInUser();
            navigateTo('dashboard');
        })
        .catch(error => {
            console.error('获取用户信息失败:', error);
            // 根据错误类型提供不同的提示信息
            let errorMessage = '登录已过期或无效，请重新登录';
            if (error.response) {
                if (error.response.status === 401) {
                    errorMessage = '登录已过期，请重新登录';
                } else if (error.response.status === 403) {
                    errorMessage = '无访问权限，请重新登录';
                }
            } else if (error.request) {
                errorMessage = '网络连接失败，请检查网络后重试';
            }
            
            // 清除登录状态
            localStorage.removeItem('token');
            state.token = null;
            state.user = null;
            logout(false);
            navigateTo('welcome');
            // 显示错误提示
            showAlert('login-alert', errorMessage, 'warning');
        });
    } else {
        // 无token，显示欢迎页面
        navigateTo('welcome');
    }
}

// 更新已登录用户的UI
function updateUIForLoggedInUser() {
    // 显示用户信息，隐藏登录/注册按钮
    document.getElementById('auth-buttons').classList.add('d-none');
    document.getElementById('user-info').classList.remove('d-none');
    document.getElementById('username-display').textContent = state.user.username;
    
    // 加载钱包信息
    loadWalletInfo();
}

// 加载钱包信息
function loadWalletInfo() {
    axios.get(`${API_BASE_URL}/wallet/info`, {
        headers: { Authorization: `Bearer ${state.token}` }
    })
    .then(response => {
        state.wallet = response.data;
        updateWalletUI();
        
        // 如果有钱包，加载余额和交易记录
        if (state.wallet && state.wallet.address) {
            loadBalances();
            loadTransactions();
        }
    })
    .catch(error => {
        console.error('获取钱包信息失败:', error);
        // 显示创建钱包选项
        document.getElementById('wallet-info').innerHTML = '<p>获取钱包信息失败，请重试。</p>';
        document.getElementById('create-wallet-section').classList.remove('d-none');
    });
}

// 更新钱包UI
function updateWalletUI() {
    const walletInfoElement = document.getElementById('wallet-info');
    const createWalletSection = document.getElementById('create-wallet-section');
    
    if (state.wallet && state.wallet.address) {
        // 有钱包，显示钱包信息
        walletInfoElement.innerHTML = `
            <p><strong>钱包地址：</strong></p>
            <p class="text-break">${state.wallet.address}</p>
            <p><strong>创建时间：</strong> ${new Date(state.wallet.created_at).toLocaleString()}</p>
        `;
        createWalletSection.classList.add('d-none');
    } else {
        // 无钱包，显示创建钱包选项
        walletInfoElement.innerHTML = '<p>您还没有创建钱包。</p>';
        createWalletSection.classList.remove('d-none');
    }
}

// 加载余额
function loadBalances() {
    axios.get(`${API_BASE_URL}/wallet/balance/${state.wallet.address}`, {
        headers: { Authorization: `Bearer ${state.token}` }
    })
    .then(response => {
        state.balances = response.data;
        updateBalancesUI();
    })
    .catch(error => {
        console.error('获取余额失败:', error);
        document.getElementById('assets-overview').innerHTML = '<p>获取余额信息失败，请重试。</p>';
        document.getElementById('assets-list').innerHTML = '<p>获取余额信息失败，请重试。</p>';
    });
}

// 更新余额UI
function updateBalancesUI() {
    const assetsOverviewElement = document.getElementById('assets-overview');
    const assetsListElement = document.getElementById('assets-list');
    
    // 更新资产概览
    let overviewHTML = '<div class="row">';
    for (const [symbol, balance] of Object.entries(state.balances)) {
        overviewHTML += `
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">${symbol}</h5>
                        <h3 class="card-text">${balance}</h3>
                    </div>
                </div>
            </div>
        `;
    }
    overviewHTML += '</div>';
    assetsOverviewElement.innerHTML = overviewHTML;
    
    // 更新资产列表
    let listHTML = '<ul class="list-group">';
    for (const [symbol, balance] of Object.entries(state.balances)) {
        listHTML += `
            <li class="list-group-item d-flex justify-content-between align-items-center">
                ${symbol}
                <span class="badge bg-primary rounded-pill">${balance}</span>
            </li>
        `;
    }
    listHTML += '</ul>';
    assetsListElement.innerHTML = listHTML;
    
    // 更新资产选择下拉框
    const assetSelect = document.getElementById('asset-select');
    assetSelect.innerHTML = '';
    
    for (const symbol of Object.keys(state.balances)) {
        const option = document.createElement('option');
        option.value = symbol;
        option.textContent = symbol;
        assetSelect.appendChild(option);
    }
}

// 加载交易记录
function loadTransactions() {
    // 首先初始化交易记录为空数组，防止任何情况下出错
    state.transactions = [];
    
    try {
        if (!state.wallet || !state.wallet.address) {
            console.log('无法加载交易记录：钱包未初始化');
            const transactionsElement = document.getElementById('transactions-list');
            if (transactionsElement) {
                transactionsElement.innerHTML = '<p>请先创建钱包</p>';
            }
            return;
        }
    
    // 确保state.pagination存在
    if (!state.pagination) {
        state.pagination = {
            currentPage: 1,
            pageSize: 10,
            totalItems: 0
        };
    }
    
    const { currentPage = 1, pageSize = 10 } = state.pagination;
    
    // 检查token是否存在
    if (!state.token) {
        console.error('无法加载交易记录：未登录');
        document.getElementById('transactions-list').innerHTML = '<p>请先登录</p>';
        return;
    }
    
    axios.get(`${API_BASE_URL}/wallet/transactions/${state.wallet.address}`, {
        headers: { Authorization: `Bearer ${state.token}` },
        params: { page: currentPage, page_size: pageSize }
    })
    .then(response => {
        if (response.data && typeof response.data === 'object') {
            // 确保items是数组
            state.transactions = Array.isArray(response.data.items) ? response.data.items : [];
            // 确保state.pagination存在
            if (!state.pagination) {
                state.pagination = {
                    currentPage: 1,
                    pageSize: 10,
                    totalItems: 0
                };
            }
            state.pagination.totalItems = response.data.total || 0;
            updateTransactionsUI();
        } else {
            console.error('获取交易记录返回格式错误:', response.data);
            document.getElementById('transactions-list').innerHTML = '<p>获取交易记录失败，数据格式错误</p>';
        }
    })
    .catch(error => {
        console.error('获取交易记录失败:', error);
        const transactionsElement = document.getElementById('transactions-list');
        if (transactionsElement) {
            transactionsElement.innerHTML = '<p>获取交易记录失败，请重试。</p>';
        }
        // 确保交易记录是空数组
        state.transactions = [];
    });
    } catch (error) {
        console.error('加载交易记录过程中发生错误:', error);
        state.transactions = [];
    }
}

// 更新交易记录UI
function updateTransactionsUI() {
    // 首先确保state.transactions是一个有效的数组
    if (!state.transactions) state.transactions = [];
    if (!Array.isArray(state.transactions)) state.transactions = [];
    
    try {
        const transactionsElement = document.getElementById('transactions-list');
        if (!transactionsElement) {
            console.error('无法找到交易记录列表元素');
            return;
        }
        
        const paginationInfoElement = document.getElementById('pagination-info');
    
    // 确保state.pagination存在
    if (!state.pagination) {
        state.pagination = {
            currentPage: 1,
            pageSize: 10,
            totalItems: 0
        };
    }
    
    // 确保state.transactions存在且是一个数组
    if (!state.transactions) {
        state.transactions = [];
    }
    
    if (!Array.isArray(state.transactions)) {
        console.warn('交易记录不是数组，重置为空数组');
        state.transactions = [];
        transactionsElement.innerHTML = '<p>暂无交易记录</p>';
        if (paginationInfoElement) {
            paginationInfoElement.textContent = '总计 0 条记录';
        }
        return;
    }
    
    // 安全检查：确保state.transactions是一个有效的数组且有length属性
    if (!state.transactions || !Array.isArray(state.transactions) || state.transactions.length === 0) {
        transactionsElement.innerHTML = '<p>当前页暂无交易记录</p>';
        // 使用解构赋值并提供默认值
        const { pageSize = 10, totalItems = 0 } = state.pagination || {};
        const totalPages = Math.ceil(totalItems / pageSize) || 1;
        if (paginationInfoElement) {
            paginationInfoElement.textContent = `总计 ${totalItems} 条记录`;
        }
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-striped"><thead><tr>';
    html += '<th>时间</th><th>类型</th><th>资产</th><th>金额</th><th>状态</th><th>操作</th>';
    html += '</tr></thead><tbody>';
    
    for (const tx of state.transactions) {
        // 确保tx是一个有效的对象
        if (!tx || typeof tx !== 'object') continue;
        
        const date = new Date(tx.timestamp || new Date()).toLocaleString();
        const type = tx.from_address && state.wallet && state.wallet.address && 
                    tx.from_address.toLowerCase() === state.wallet.address.toLowerCase() ? '发送' : '接收';
        const status = tx.status === 'confirmed' ? '已确认' : '处理中';
        const amount = tx.amount || '0';
        const tokenSymbol = tx.token_symbol || 'ETH';
        const txHash = tx.tx_hash || '';
        
        html += `<tr>
            <td>${date}</td>
            <td>${type}</td>
            <td>${tokenSymbol}</td>
            <td>${amount}</td>
            <td><span class="badge ${tx.status === 'confirmed' ? 'bg-success' : 'bg-warning'}">${status}</span></td>
            <td>${txHash ? `<a href="https://etherscan.io/tx/${txHash}" target="_blank" class="btn btn-sm btn-outline-primary">查看</a>` : '-'}</td>
        </tr>`;
    }
    
    html += '</tbody></table></div>';
    transactionsElement.innerHTML = html;
    
    // 更新分页信息
    // 使用解构赋值并提供默认值，确保即使state.pagination为undefined也能正常工作
    const { currentPage = 1, pageSize = 10, totalItems = 0 } = state.pagination || {};
    const totalPages = Math.ceil(totalItems / pageSize) || 1;
    if (paginationInfoElement) {
        paginationInfoElement.textContent = `第 ${currentPage} 页，共 ${totalPages} 页，总计 ${totalItems} 条记录`;
    }
    } catch (error) {
        console.error('更新交易记录UI时发生错误:', error);
        const transactionsElement = document.getElementById('transactions-list');
        if (transactionsElement) {
            transactionsElement.innerHTML = '<p>显示交易记录时发生错误</p>';
        }
    }
}

// 页面导航
function navigateTo(page) {
    // 隐藏所有页面
    document.querySelectorAll('.page').forEach(p => p.classList.add('d-none'));
    
    // 显示目标页面
    const targetPage = document.getElementById(`${page}-page`);
    if (targetPage) {
        targetPage.classList.remove('d-none');
        state.currentPage = page;
        
        // 更新导航栏激活状态
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.getAttribute('data-page') === page) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
}

// 用户登录
function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    if (!username || !password) {
        showAlert('login-alert', '请输入用户名和密码', 'danger');
        return;
    }
    
    axios.post(`${API_BASE_URL}/auth/login`, {
        username,
        password
    })
    .then(response => {
        const { access_token } = response.data;
        state.token = access_token;
        localStorage.setItem('token', access_token);
        
        // 获取用户信息
        return axios.get(`${API_BASE_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${access_token}` }
        });
    })
    .then(response => {
        state.user = response.data;
        updateUIForLoggedInUser();
        navigateTo('dashboard');
    })
    .catch(error => {
        console.error('登录失败:', error);
        showAlert('login-alert', '登录失败，请检查用户名和密码', 'danger');
    });
}

// 用户注册
function register() {
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    
    if (!username || !email || !password) {
        showAlert('register-alert', '请填写所有必填字段', 'danger');
        return;
    }
    
    if (password !== confirmPassword) {
        showAlert('register-alert', '两次输入的密码不一致', 'danger');
        return;
    }
    
    axios.post(`${API_BASE_URL}/auth/register`, {
        username,
        email,
        password
    })
    .then(response => {
        showAlert('register-alert', '注册成功，请登录', 'success');
        // 清空表单
        document.getElementById('register-form').reset();
        // 切换到登录页面
        document.getElementById('login-tab').click();
    })
    .catch(error => {
        console.error('注册失败:', error);
        showAlert('register-alert', `注册失败: ${error.response?.data?.detail || '未知错误'}`, 'danger');
    });
}

// 用户退出
function logout(redirect = true) {
    // 清除状态
    state.user = null;
    state.token = null;
    state.wallet = null;
    state.transactions = [];
    state.balances = {};
    
    // 清除本地存储
    localStorage.removeItem('token');
    
    // 更新UI
    document.getElementById('auth-buttons').classList.remove('d-none');
    document.getElementById('user-info').classList.add('d-none');
    
    // 重定向到欢迎页面
    if (redirect) {
        navigateTo('welcome');
    }
}

// 显示交易确认对话框
function showTransactionConfirmation() {
    const toAddress = document.getElementById('to-address').value;
    const amount = document.getElementById('amount').value;
    const asset = document.getElementById('asset-select').value;
    
    if (!toAddress || !amount || !asset) {
        showAlert('send-alert', '请填写所有必填字段', 'danger');
        return;
    }
    
    // 显示确认信息
    document.getElementById('confirm-to-address').textContent = toAddress;
    document.getElementById('confirm-amount').textContent = amount;
    document.getElementById('confirm-asset').textContent = asset;
    
    // 显示确认对话框
    const confirmModal = new bootstrap.Modal(document.getElementById('transaction-confirm-modal'));
    confirmModal.show();
}

// 发送交易
function sendTransaction() {
    const toAddress = document.getElementById('to-address').value;
    const amount = document.getElementById('amount').value;
    const asset = document.getElementById('asset-select').value;
    
    if (!toAddress || !amount || !asset) {
        showAlert('send-alert', '请填写所有必填字段', 'danger');
        return;
    }
    
    // 隐藏确认对话框
    const confirmModal = bootstrap.Modal.getInstance(document.getElementById('transaction-confirm-modal'));
    confirmModal.hide();
    
    // 显示加载状态
    document.getElementById('send-btn').disabled = true;
    document.getElementById('send-btn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';
    
    axios.post(`${API_BASE_URL}/wallet/send`, {
        from_address: state.wallet.address,
        to_address: toAddress,
        amount: parseFloat(amount),
        token_symbol: asset
    }, {
        headers: { Authorization: `Bearer ${state.token}` }
    })
    .then(response => {
        // 重置表单
        document.getElementById('send-form').reset();
        
        // 显示成功消息
        showAlert('send-alert', '交易已提交，请等待确认', 'success');
        
        // 重新加载余额和交易记录
        loadBalances();
        loadTransactions();
    })
    .catch(error => {
        console.error('发送交易失败:', error);
        showAlert('send-alert', `发送交易失败: ${error.response?.data?.detail || '未知错误'}`, 'danger');
    })
    .finally(() => {
        // 恢复按钮状态
        document.getElementById('send-btn').disabled = false;
        document.getElementById('send-btn').textContent = '发送';
    });
}

// 创建钱包
function createWallet() {
    // 显示加载状态
    document.getElementById('create-wallet-btn').disabled = true;
    document.getElementById('create-wallet-btn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 创建中...';
    
    axios.post(`${API_BASE_URL}/wallet/create`, {}, {
        headers: { Authorization: `Bearer ${state.token}` }
    })
    .then(response => {
        state.wallet = response.data;
        updateWalletUI();
        
        // 显示成功消息
        showAlert('wallet-alert', '钱包创建成功', 'success');
        
        // 加载余额
        loadBalances();
    })
    .catch(error => {
        console.error('创建钱包失败:', error);
        showAlert('wallet-alert', `创建钱包失败: ${error.response?.data?.detail || '未知错误'}`, 'danger');
    })
    .finally(() => {
        // 恢复按钮状态
        document.getElementById('create-wallet-btn').disabled = false;
        document.getElementById('create-wallet-btn').textContent = '创建钱包';
    });
}

// 导入代币
function importToken() {
    const tokenAddress = document.getElementById('token-address').value;
    const tokenSymbol = document.getElementById('token-symbol').value;
    
    if (!tokenAddress || !tokenSymbol) {
        showAlert('import-token-alert', '请填写代币地址和符号', 'danger');
        return;
    }
    
    // 显示加载状态
    document.getElementById('import-token-btn').disabled = true;
    document.getElementById('import-token-btn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 导入中...';
    
    axios.post(`${API_BASE_URL}/wallet/import-token`, {
        wallet_address: state.wallet.address,
        token_address: tokenAddress,
        token_symbol: tokenSymbol
    }, {
        headers: { Authorization: `Bearer ${state.token}` }
    })
    .then(response => {
        // 重置表单
        document.getElementById('import-token-form').reset();
        
        // 显示成功消息
        showAlert('import-token-alert', '代币导入成功', 'success');
        
        // 重新加载余额
        loadBalances();
    })
    .catch(error => {
        console.error('导入代币失败:', error);
        showAlert('import-token-alert', `导入代币失败: ${error.response?.data?.detail || '未知错误'}`, 'danger');
    })
    .finally(() => {
        // 恢复按钮状态
        document.getElementById('import-token-btn').disabled = false;
        document.getElementById('import-token-btn').textContent = '导入';
    });
}

// 发送AI聊天消息
function sendChatMessage() {
    const messageInput = document.getElementById('chat-message');
    const message = messageInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // 清空输入框
    messageInput.value = '';
    
    // 添加用户消息到聊天窗口
    appendChatMessage('user', message);
    
    // 显示AI正在输入
    const typingElement = document.createElement('div');
    typingElement.id = 'ai-typing';
    typingElement.className = 'chat-message ai-message';
    typingElement.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    document.getElementById('chat-messages').appendChild(typingElement);
    
    // 滚动到底部
    scrollChatToBottom();
    
    // 发送请求到AI接口
    axios.post(`${API_BASE_URL}/ai/chat`, {
        message,
        wallet_address: state.wallet ? state.wallet.address : null
    }, {
        headers: { Authorization: `Bearer ${state.token}` }
    })
    .then(response => {
        // 移除正在输入指示器
        document.getElementById('ai-typing').remove();
        
        // 添加AI回复到聊天窗口
        appendChatMessage('ai', response.data.message);
        
        // 如果AI执行了操作，更新相关数据
        if (response.data.action === 'transfer') {
            loadBalances();
            loadTransactions();
        }
    })
    .catch(error => {
        console.error('AI聊天请求失败:', error);
        
        // 移除正在输入指示器
        const typingElement = document.getElementById('ai-typing');
        if (typingElement) {
            typingElement.remove();
        }
        
        // 添加错误消息
        appendChatMessage('ai', '抱歉，我遇到了一些问题，无法回应您的请求。');
    });
}

// 添加聊天消息到窗口
function appendChatMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${sender}-message`;
    
    const contentElement = document.createElement('div');
    contentElement.className = 'message-content';
    contentElement.textContent = message;
    
    messageElement.appendChild(contentElement);
    document.getElementById('chat-messages').appendChild(messageElement);
    
    // 滚动到底部
    scrollChatToBottom();
}

// 滚动聊天窗口到底部
function scrollChatToBottom() {
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 显示提示信息
function showAlert(elementId, message, type = 'info') {
    const alertElement = document.getElementById(elementId);
    alertElement.className = `alert alert-${type}`;
    alertElement.textContent = message;
    alertElement.classList.remove('d-none');
    
    // 5秒后自动隐藏
    setTimeout(() => {
        alertElement.classList.add('d-none');
    }, 5000);
}