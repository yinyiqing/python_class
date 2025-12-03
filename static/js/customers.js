// static/js/customers.js

let deleteCustomerId = null;

document.addEventListener('DOMContentLoaded', function() {
    loadCustomers();

    // 初始化所有模态框的关闭按钮 (class="close-modal")
    // 这对应了 HTML 中的 <button class="close-modal"> 和取消按钮
    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', function() {
            closeAllModals();
        });
    });
});

// 1. 加载客户列表
async function loadCustomers() {
    try {
        showLoading('customers-table-body');
        const response = await fetch('/api/customer/list');
        const data = await response.json();

        if (data.success) {
            renderCustomersTable(data.data);
        } else {
            renderCustomersTable([]); // 即使失败也清空表格防止显示旧数据
            // 过滤掉 "未找到" 这种非错误类型的提示
            if (data.message && !data.message.includes('未找到')) {
                showError(data.message);
            }
        }
    } catch (error) {
        console.error('加载失败:', error);
        showError('加载客户列表失败');
    }
}

// 2. 渲染表格 HTML
function renderCustomersTable(customers) {
    const tbody = document.getElementById('customers-table-body');
    const noDataDiv = document.getElementById('no-customers');

    if (!customers || customers.length === 0) {
        tbody.innerHTML = '';
        if (noDataDiv) noDataDiv.style.display = 'block';
        return;
    }

    if (noDataDiv) noDataDiv.style.display = 'none';
    let html = '';

    customers.forEach(customer => {
        // 防止 created_at 为空导致报错
        const createdDate = customer.created_at ? customer.created_at.split(' ')[0] : '-';
        html += `
            <tr>
                <td>${customer.id}</td>
                <td>${customer.name}</td>
                <td>${customer.phone}</td>
                <td>${customer.id_card}</td>
                <td>${createdDate}</td>
                <td>
                    <button class="btn btn-warning btn-sm" onclick="showEditCustomerModal('${customer.id}')">
                        <i class="fas fa-edit"></i> 编辑
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="confirmDeleteCustomer('${customer.id}', '${customer.name}')">
                        <i class="fas fa-trash"></i> 删除
                    </button>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

// 3. 点击“添加客户”按钮
function showAddCustomerModal() {
    document.getElementById('customer-modal-title').textContent = '添加客户';
    document.getElementById('customer-form').reset(); // 清空表单
    document.getElementById('edit-customer-id').value = ''; // 清空ID，表示新增
    document.getElementById('customer-modal').style.display = 'flex';
}

// 4. 点击“编辑”按钮
async function showEditCustomerModal(customerId) {
    try {
        // 先从后台获取最新数据，确保数据准确
        const response = await fetch(`/api/customer/${customerId}`);
        const data = await response.json();

        if (data.success) {
            const c = data.data;
            document.getElementById('customer-modal-title').textContent = '编辑客户';
            document.getElementById('edit-customer-id').value = c.id;

            // 填充表单
            document.getElementById('name').value = c.name;
            document.getElementById('phone').value = c.phone;
            document.getElementById('id_card').value = c.id_card;

            document.getElementById('customer-modal').style.display = 'flex';
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('获取客户详情失败');
    }
}

// 5. 点击“保存”按钮 (提交表单)
async function saveCustomer(event) {
    event.preventDefault(); // 阻止表单默认提交刷新页面

    const form = document.getElementById('customer-form');
    // 获取表单数据
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    const customerId = document.getElementById('edit-customer-id').value;

    // 判断是新增(POST)还是修改(PUT)
    const url = customerId ? `/api/customer/update/${customerId}` : '/api/customer/create';
    const method = customerId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('保存成功', 'success');
            closeAllModals();
            loadCustomers(); // 刷新列表
        } else {
            showError(result.message);
        }
    } catch (error) {
        showError('保存失败: ' + error.message);
    }
}

// 6. 删除相关功能
function confirmDeleteCustomer(id, name) {
    deleteCustomerId = id;
    const msgEl = document.getElementById('confirm-message');
    if(msgEl) msgEl.textContent = `确定要删除客户 "${name}" 吗？此操作不可恢复！`;
    document.getElementById('confirm-modal').style.display = 'flex';
}

// 绑定删除确认按钮点击事件
// 这里使用 if (confirmBtn) 检查，防止 JS 加载比 HTML 快导致找不到元素
const confirmBtn = document.getElementById('confirm-delete-btn');
if (confirmBtn) {
    confirmBtn.addEventListener('click', async function() {
        if (!deleteCustomerId) return;
        try {
            const response = await fetch(`/api/customer/delete/${deleteCustomerId}`, { method: 'DELETE' });
            const result = await response.json();
            if (result.success) {
                showNotification('删除成功', 'success');
                closeAllModals();
                loadCustomers();
            } else {
                showError(result.message);
            }
        } catch (error) {
            showError('删除失败');
        }
    });
}

// 辅助功能：搜索
function searchCustomers() {
    const keyword = document.getElementById('customer-search').value.trim();
    if (!keyword) {
        loadCustomers();
        return;
    }

    fetch(`/api/customer/search?keyword=${encodeURIComponent(keyword)}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) renderCustomersTable(data.data);
            else renderCustomersTable([]);
        })
        .catch(err => showError('搜索请求失败'));
}

function clearSearch() {
    document.getElementById('customer-search').value = '';
    loadCustomers();
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
    deleteCustomerId = null;
}

function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if(el) el.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> 加载中...</td></tr>';
}

// 统一通知处理：如果 window.showNotification 存在（来自 common.js）则使用它，否则使用 alert
function showNotification(msg, type) {
    if (window.showNotification) window.showNotification(msg, type);
    else alert(msg);
}
function showError(msg) { showNotification(msg, 'error'); }