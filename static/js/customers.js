// static/js/customers.js

let deleteCustomerId = null;

document.addEventListener('DOMContentLoaded', function() {
    loadCustomers();

    // 初始化所有模态框的关闭按钮
    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', function() {
            closeAllModals();
        });
    });

    // [新增] 监听搜索框的"回车"按键事件
    const searchInput = document.getElementById('customer-search');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchCustomers();
            }
        });
    }
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
            renderCustomersTable([]);
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
        const createdDate = customer.created_at ? customer.created_at.split(' ')[0] : '-';
        html += `
            <tr>
                <td>${customer.id}</td>
                <td>${customer.name}</td>
                <td>${customer.phone}</td>
                <td>${customer.id_card}</td>
                <td>${createdDate}</td>
                <td>
                    <button class="btn btn-warning btn-sm btn-icon" onclick="showEditCustomerModal('${customer.id}')">
                        <i class="fas fa-edit"></i> 编辑
                    </button>
                    <button class="btn btn-danger btn-sm btn-icon" onclick="confirmDeleteCustomer('${customer.id}', '${customer.name}')">
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
    document.getElementById('customer-form').reset();
    document.getElementById('edit-customer-id').value = '';
    document.getElementById('customer-modal').style.display = 'flex';
}

// 4. 点击“编辑”按钮
async function showEditCustomerModal(customerId) {
    try {
        const response = await fetch(`/api/customer/${customerId}`);
        const data = await response.json();

        if (data.success) {
            const c = data.data;
            document.getElementById('customer-modal-title').textContent = '编辑客户';
            document.getElementById('edit-customer-id').value = c.id;
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

// 5. 点击“保存”按钮
async function saveCustomer(event) {
    event.preventDefault();

    const form = document.getElementById('customer-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const customerId = document.getElementById('edit-customer-id').value;

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
            loadCustomers();
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

// 7. 搜索功能 (这就是你之前点击没反应的函数)
function searchCustomers() {
    const keyword = document.getElementById('customer-search').value.trim();
    if (!keyword) {
        loadCustomers();
        return;
    }

    // 显示加载状态，提升体验
    showLoading('customers-table-body');

    fetch(`/api/customer/search?keyword=${encodeURIComponent(keyword)}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderCustomersTable(data.data);
            } else {
                renderCustomersTable([]);
                showError(data.message || '搜索未返回结果');
            }
        })
        .catch(err => {
            console.error(err);
            showError('搜索请求失败');
            // 如果失败，恢复显示原列表或保持空
            loadCustomers();
        });
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

function showNotification(msg, type) {
    if (window.showNotification) window.showNotification(msg, type);
    else alert(msg);
}

function showError(msg) {
    showNotification(msg, 'error');
}