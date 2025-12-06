// 全局变量
let charts = {};
let currentTab = 'dashboard';

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 设置默认日期
    const today = new Date().toISOString().split('T')[0];
    const lastMonth = new Date();
    lastMonth.setMonth(lastMonth.getMonth() - 1);
    const lastMonthDate = lastMonth.toISOString().split('T')[0];

    document.getElementById('startDate').value = lastMonthDate;
    document.getElementById('endDate').value = today;

    // 加载数据
    loadDashboardData();
    loadCharts();
    loadOrderStatusChart();
    
});

// 切换标签页
function switchTab(tabName) {
    // 更新按钮状态
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // 更新内容显示
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName + '-tab').classList.add('active');

    currentTab = tabName;

    // 加载对应标签页的数据
    switch(tabName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'employees':
            loadEmployeeStats();
            break;
        case 'orders':
            loadOrderStats();
            break;
        case 'customers':
            loadCustomerStats();
            break;
        case 'rooms':
            loadRoomStats();
            break;
        case 'revenue':
            loadRevenueAnalysis();
            break;
    }
}

// 加载仪表板数据
async function loadDashboardData() {
    try {
        const response = await fetch('/api/analytics/dashboard');
        const result = await response.json();

        if (result.success) {
            updateDashboardStats(result.data);
        } else {
            showNotification('加载仪表板数据失败: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('网络错误: ' + error.message, 'error');
    }
}

// 更新仪表板统计数据
function updateDashboardStats(data) {
    const summary = data.summary;

    // 创建或更新统计卡片
    const statsGrid = document.getElementById('dashboard-stats');
    statsGrid.innerHTML = '';

    const statCards = [
        {
            icon: 'users',
            iconColor: '#2196F3',
            label: '员工总数',
            value: summary.employees,
            change: null
        },
        {
            icon: 'user-check',
            iconColor: '#4CAF50',
            label: '在职员工',
            value: summary.active_employees,
            change: null
        },
        {
            icon: 'user-friends',
            iconColor: '#03A9F4',
            label: '客户总数',
            value: summary.customers,
            change: null
        },
        {
            icon: 'bed',
            iconColor: '#8BC34A',
            label: '房间总数',
            value: summary.rooms,
            change: null
        },
        {
            icon: 'door-open',
            iconColor: '#FF9800',
            label: '入住率',
            value: summary.occupancy_rate + '%',
            change: null
        },
        {
            icon: 'shopping-cart',
            iconColor: '#9C27B0',
            label: '订单总数',
            value: summary.total_orders,
            change: null
        },
        {
            icon: 'money-bill-wave',
            iconColor: '#4CAF50',
            label: '今日收入',
            value: '¥' + formatNumber(summary.today_revenue),
            change: null
        },
        {
            icon: 'hand-holding-usd',
            iconColor: '#FFC107',
            label: '今日实收',
            value: '¥' + formatNumber(summary.today_paid),
            change: null
        }
    ];

    statCards.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = `
            <div class="stat-icon" style="background: rgba(${hexToRgb(stat.iconColor)}, 0.2); color: ${stat.iconColor};">
                <i class="fas fa-${stat.icon}"></i>
            </div>
            <div class="stat-label">${stat.label}</div>
            <div class="stat-value">${stat.value}</div>
        `;
        statsGrid.appendChild(card);
    });
}

// 加载图表数据
async function loadCharts() {
    // 加载员工部门分布图
    await loadChart('employee_dept', 'employeeDeptChart', 'doughnut');

    // 加载收入趋势图
    await loadChart('revenue_trend', 'revenueTrendChart', 'line');

    // 加载房型分布图
    await loadChart('room_type', 'roomTypeChart', 'doughnut');
}

async function loadChart(chartType, canvasId, chartTypeName) {
    try {
        const response = await fetch(`/api/analytics/chart?type=${chartType}`);
        const result = await response.json();

        if (result.success) {
            renderChart(canvasId, result, chartTypeName);
        }
    } catch (error) {
        console.error(`加载${chartType}图表失败:`, error);
    }
}

// 渲染图表
function renderChart(canvasId, chartData, type) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // 销毁现有的图表实例
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }

    const config = {
        type: type,
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: 'var(--color-gray-light)'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff'
                }
            },
            scales: type === 'line' ? {
                x: {
                    ticks: { color: 'var(--color-gray-light)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    ticks: { color: 'var(--color-gray-light)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    beginAtZero: true
                }
            } : undefined
        }
    };

    charts[canvasId] = new Chart(ctx, config);
}

// 加载员工统计数据
async function loadEmployeeStats() {
    try {
        const response = await fetch('/api/analytics/employees');
        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // 更新统计卡片
            document.getElementById('total-employees').textContent = data.total;
            document.getElementById('active-employees').textContent = data.active;
            document.getElementById('terminated-employees').textContent = data.terminated;
            document.getElementById('active-rate').textContent = data.active_rate + '%';

            // 渲染柱状图
            renderEmployeeDeptBarChart(data.by_department);
        }
    } catch (error) {
        showNotification('加载员工统计数据失败: ' + error.message, 'error');
    }
}

// 渲染员工部门柱状图
function renderEmployeeDeptBarChart(deptData) {
    const ctx = document.getElementById('employeeDeptBarChart').getContext('2d');

    if (charts['employeeDeptBarChart']) {
        charts['employeeDeptBarChart'].destroy();
    }

    const labels = deptData.map(dept => dept.department_name);
    const data = deptData.map(dept => dept.count);

    charts['employeeDeptBarChart'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '员工数量',
                data: data,
                backgroundColor: '#2196F3',
                borderColor: '#0d8bf2',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'var(--color-gray-light)'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'var(--color-gray-light)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: 'var(--color-gray-light)',
                        precision: 0
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}



// 渲染支付状态柱状图
function renderPaymentStatusChart(paymentData) {
    const ctx = document.getElementById('paymentStatusChart').getContext('2d');

    if (charts['paymentStatusChart']) {
        charts['paymentStatusChart'].destroy();
    }

    const labels = paymentData.map(item => item.payment_status);
    const data = paymentData.map(item => item.count);

    charts['paymentStatusChart'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '订单数量',
                data: data,
                backgroundColor: '#FF9800',
                borderColor: '#e68900',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'var(--color-gray-light)'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'var(--color-gray-light)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: 'var(--color-gray-light)',
                        precision: 0
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// 加载客户统计数据
async function loadCustomerStats() {
    try {
        const response = await fetch('/api/analytics/customers');
        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // 更新统计卡片
            document.getElementById('total-customers').textContent = data.total;
            document.getElementById('today-new-customers').textContent = data.today_new;
            document.getElementById('vip-customers').textContent = data.top_customers.length;

            // 计算平均消费
            const totalSpent = data.top_customers.reduce((sum, customer) => sum + (customer.total_spent || 0), 0);
            const avgSpent = data.top_customers.length > 0 ? totalSpent / data.top_customers.length : 0;
            document.getElementById('avg-spent').textContent = '¥' + formatNumber(avgSpent);

            // 渲染趋势图
            renderCustomerTrendChart(data.trend_data);

            // 更新客户排行表格
            updateTopCustomersTable(data.top_customers);
        }
    } catch (error) {
        showNotification('加载客户统计数据失败: ' + error.message, 'error');
    }
}

// 渲染客户增长趋势图
function renderCustomerTrendChart(trendData) {
    const ctx = document.getElementById('customerTrendChart').getContext('2d');

    if (charts['customerTrendChart']) {
        charts['customerTrendChart'].destroy();
    }

    const labels = trendData.map(item => item.date);
    const data = trendData.map(item => item.count);

    charts['customerTrendChart'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '新增客户',
                data: data,
                borderColor: '#03A9F4',
                backgroundColor: 'rgba(3, 169, 244, 0.2)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'var(--color-gray-light)'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'var(--color-gray-light)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: 'var(--color-gray-light)',
                        precision: 0
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// 更新客户排行表格
function updateTopCustomersTable(customers) {
    const tbody = document.querySelector('#top-customers-table tbody');
    tbody.innerHTML = '';

    customers.forEach(customer => {
        const avgSpent = customer.order_count > 0 ? customer.total_spent / customer.order_count : 0;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><i class="fas fa-user"></i> ${customer.name}</td>
            <td>${customer.order_count}</td>
            <td><span class="badge badge-success">¥${formatNumber(customer.total_spent)}</span></td>
            <td>¥${formatNumber(avgSpent)}</td>
        `;
        tbody.appendChild(row);
    });
}

// 加载房间统计数据
async function loadRoomStats() {
    try {
        const response = await fetch('/api/analytics/rooms');
        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // 更新统计卡片
            document.getElementById('total-rooms').textContent = data.total;
            document.getElementById('occupied-rooms').textContent = data.occupied;
            document.getElementById('occupancy-rate').textContent = data.occupancy_rate + '%';

            // 计算平均房价
            const totalPrice = data.type_stats.reduce((sum, type) => sum + (type.avg_price * type.count), 0);
            const avgPrice = data.total > 0 ? totalPrice / data.total : 0;
            document.getElementById('avg-room-price').textContent = '¥' + formatNumber(avgPrice);

            // 渲染房间状态饼图
            renderRoomStatusChart(data.status_stats);

            // 渲染房型价格柱状图
            renderRoomPriceChart(data.type_stats);
        }
    } catch (error) {
        showNotification('加载房间统计数据失败: ' + error.message, 'error');
    }
}

// 渲染房间状态饼图
function renderRoomStatusChart(statusData) {
    const ctx = document.getElementById('roomStatusChart').getContext('2d');

    if (charts['roomStatusChart']) {
        charts['roomStatusChart'].destroy();
    }

    const labels = statusData.map(item => item.status);
    const data = statusData.map(item => item.count);

    charts['roomStatusChart'] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#4CAF50', // 空闲
                    '#2196F3', // 已预订
                    '#FF9800', // 已入住
                    '#9C27B0'  // 维修中
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: 'var(--color-gray-light)'
                    }
                }
            }
        }
    });
}

// 渲染房型价格柱状图
function renderRoomPriceChart(typeData) {
    const ctx = document.getElementById('roomPriceChart').getContext('2d');

    if (charts['roomPriceChart']) {
        charts['roomPriceChart'].destroy();
    }

    const labels = typeData.map(item => item.room_type);
    const prices = typeData.map(item => item.avg_price);
    const counts = typeData.map(item => item.count);

    charts['roomPriceChart'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '平均价格',
                    data: prices,
                    backgroundColor: '#4CAF50',
                    borderColor: '#45a049',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: '房间数量',
                    data: counts,
                    backgroundColor: '#2196F3',
                    borderColor: '#0d8bf2',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'var(--color-gray-light)'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'var(--color-gray-light)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: '平均价格(元)',
                        color: 'var(--color-gray-light)'
                    },
                    ticks: {
                        color: 'var(--color-gray-light)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: '房间数量',
                        color: 'var(--color-gray-light)'
                    },
                    ticks: {
                        color: 'var(--color-gray-light)',
                        precision: 0
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// 加载收入分析数据
async function loadRevenueAnalysis() {
    try {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        const response = await fetch(`/api/analytics/revenue?start_date=${startDate}&end_date=${endDate}`);
        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // 更新统计卡片
            document.getElementById('total-revenue').textContent = '¥' + formatNumber(data.revenue_stats.total_revenue || 0);
            document.getElementById('total-paid').textContent = '¥' + formatNumber(data.revenue_stats.total_paid || 0);
            document.getElementById('total-unpaid').textContent = '¥' + formatNumber((data.revenue_stats.total_revenue || 0) - (data.revenue_stats.total_paid || 0));

            const avgOrderValue = data.revenue_stats.order_count > 0 ?
                (data.revenue_stats.total_revenue || 0) / data.revenue_stats.order_count : 0;
            document.getElementById('avg-order-value').textContent = '¥' + formatNumber(avgOrderValue);

            // 渲染收入分析图
            renderRevenueAnalysisChart(data.daily_trend);

            // 渲染房型收入排行
            renderRoomTypeRevenueChart(data.room_type_stats);

            // 渲染支付方式分布
            renderPaymentMethodChart(data.payment_stats);
        }
    } catch (error) {
        showNotification('加载收入分析数据失败: ' + error.message, 'error');
    }
}

// 渲染收入分析趋势图
function renderRevenueAnalysisChart(trendData) {
    const ctx = document.getElementById('revenueAnalysisChart').getContext('2d');

    if (charts['revenueAnalysisChart']) {
        charts['revenueAnalysisChart'].destroy();
    }

    const labels = trendData.map(item => item.date);
    const revenueData = trendData.map(item => item.daily_revenue || 0);
    const paidData = trendData.map(item => item.daily_paid || 0);

    charts['revenueAnalysisChart'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '每日收入',
                    data: revenueData,
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.2)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: '每日实收',
                    data: paidData,
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.2)',
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'var(--color-gray-light)'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'var(--color-gray-light)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: 'var(--color-gray-light)',
                        callback: function(value) {
                            return '¥' + formatNumber(value);
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// 渲染房型收入排行
function renderRoomTypeRevenueChart(roomTypeData) {
    const ctx = document.getElementById('roomTypeRevenueChart').getContext('2d');

    if (charts['roomTypeRevenueChart']) {
        charts['roomTypeRevenueChart'].destroy();
    }

    const labels = roomTypeData.map(item => item.room_type);
    const revenueData = roomTypeData.map(item => item.revenue || 0);

    charts['roomTypeRevenueChart'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '收入(元)',
                data: revenueData,
                backgroundColor: '#FF9800',
                borderColor: '#e68900',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'var(--color-gray-light)'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: 'var(--color-gray-light)',
                        callback: function(value) {
                            return '¥' + formatNumber(value);
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    ticks: {
                        color: 'var(--color-gray-light)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// 渲染支付方式分布
function renderPaymentMethodChart(paymentData) {
    const ctx = document.getElementById('paymentMethodChart').getContext('2d');

    if (charts['paymentMethodChart']) {
        charts['paymentMethodChart'].destroy();
    }

    const labels = paymentData.map(item => item.payment_status);
    const data = paymentData.map(item => item.count);

    charts['paymentMethodChart'] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#4CAF50', // 已支付
                    '#2196F3', // 部分支付
                    '#FF9800', // 未支付
                    '#F44336'  // 已退款
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: 'var(--color-gray-light)'
                    }
                }
            }
        }
    });
}

// 应用日期筛选
function applyDateFilter() {
    if (currentTab === 'revenue') {
        loadRevenueAnalysis();
    } else {
        // 重新加载当前标签页数据
        switch(currentTab) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'employees':
                loadEmployeeStats();
                break;
            case 'orders':
                loadOrderStats();
                break;
            case 'customers':
                loadCustomerStats();
                break;
            case 'rooms':
                loadRoomStats();
                break;
        }
    }
}

// 重置日期筛选
function resetDateFilter() {
    const today = new Date().toISOString().split('T')[0];
    const lastMonth = new Date();
    lastMonth.setMonth(lastMonth.getMonth() - 1);
    const lastMonthDate = lastMonth.toISOString().split('T')[0];

    document.getElementById('startDate').value = lastMonthDate;
    document.getElementById('endDate').value = today;

    applyDateFilter();
}

// 导出数据
async function exportData(type) {
    try {
        const response = await fetch(`/api/analytics/export?type=${type}`);
        const result = await response.json();

        if (result.success) {
            if (type === 'json') {
                // 下载JSON文件
                const dataStr = JSON.stringify(result.data, null, 2);
                const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                const exportFileDefaultName = `hotel-analytics-${new Date().toISOString().split('T')[0]}.json`;

                const linkElement = document.createElement('a');
                linkElement.setAttribute('href', dataUri);
                linkElement.setAttribute('download', exportFileDefaultName);
                linkElement.click();

                showNotification('JSON数据导出成功！', 'success');
            } else if (type === 'summary') {
                // 显示文本报告
                showModal('统计报告', `<pre style="white-space: pre-wrap; color: var(--color-light);">${result.data}</pre>`);
            }
        } else {
            showNotification('导出失败: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('导出失败: ' + error.message, 'error');
    }
}

// 刷新所有数据
function refreshAll() {
    switch(currentTab) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'employees':
            loadEmployeeStats();
            break;
        case 'orders':
            loadOrderStats();
            break;
        case 'customers':
            loadCustomerStats();
            break;
        case 'rooms':
            loadRoomStats();
            break;
        case 'revenue':
            loadRevenueAnalysis();
            break;
    }

    showNotification('数据已刷新！', 'success');
}

// 辅助函数
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ?
        `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` :
        '33, 150, 243';
}

function formatNumber(num) {
    if (isNaN(num)) return '0.00';
    return parseFloat(num).toFixed(2);
}

function showModal(title, content) {
    // 创建一个简单的模态框
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        padding: 20px;
    `;

    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: var(--color-secondary);
        border-radius: 12px;
        padding: 30px;
        max-width: 600px;
        width: 100%;
        max-height: 80vh;
        overflow-y: auto;
        border: 1px solid rgba(255,255,255,0.1);
    `;

    modalContent.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h3 style="color: var(--color-light); margin: 0;">${title}</h3>
            <button onclick="this.closest('.modal-overlay').remove()" style="background: none; border: none; color: var(--color-gray-light); font-size: 24px; cursor: pointer;">×</button>
        </div>
        <div style="color: var(--color-light);">${content}</div>
        <div style="margin-top: 30px; text-align: right;">
            <button class="btn btn-primary" onclick="this.closest('.modal-overlay').remove()">关闭</button>
        </div>
    `;

    modal.appendChild(modalContent);
    modal.className = 'modal-overlay';
    document.body.appendChild(modal);
}
