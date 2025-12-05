// static/js/employees.js

// 全局变量
let currentTab = 'employees';
let departmentsData = [];
let deleteCallback = null;
let deleteItemId = null;
let deleteItemType = null;

// 页面加载初始化
document.addEventListener('DOMContentLoaded', function() {
    switchTab('employees'); // 默认显示员工
    loadEmployees();
    loadDepartments();
    loadStatistics();

    // 初始化模态框关闭按钮
    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', closeAllModals);
    });
});

// 切换标签页
function switchTab(tabName, event) {
    currentTab = tabName;

    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    const tabElement = event ? event.currentTarget.closest('.tab') : document.querySelector(`.tab[onclick*="${tabName}"]`);
    if (tabElement) tabElement.classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// ==================== 员工管理 ====================

// 加载员工列表
async function loadEmployees() {
    const tbody = document.getElementById('employees-table-body');
    const noDataDiv = document.getElementById('no-employees');

    try {
        const response = await fetch('/api/employee/list');
        const data = await response.json();

        if (data.success) {
            if (!data.data || data.data.length === 0) {
                tbody.innerHTML = '';
                tbody.style.display = 'none';
                noDataDiv.style.display = 'block';
            } else {
                noDataDiv.style.display = 'none';
                tbody.style.display = 'table-row-group';

                tbody.innerHTML = data.data.map(emp => {
                    const statusClass = emp.status === '在职' ? 'active' : 'inactive';
                    const hireDate = emp.hire_date || '-';
                    return `
                        <tr>
                            <td>${emp.employee_id}</td>
                            <td>${emp.employee_name}</td>
                            <td>${emp.gender}</td>
                            <td>${emp.phone || '-'}</td>
                            <td>${emp.department_name || '-'}</td>
                            <td>${emp.position_name || '-'}</td>
                            <td>${hireDate}</td>
                            <td><span class="status-badge ${statusClass}">${emp.status}</span></td>
                            <td>
                                <button class="btn btn-warning btn-sm btn-icon" onclick="showEditEmployeeModal('${emp.employee_id}')">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-danger btn-sm btn-icon" onclick="confirmDeleteEmployee('${emp.employee_id}', '${emp.employee_name}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
            }
        } else {
            showNotification(data.message || '加载员工失败', 'error');
        }
    } catch (err) {
        console.error('加载员工失败', err);
        showNotification('加载员工失败', 'error');
    }
}

// 搜索员工
function searchEmployees() {
    const keyword = document.getElementById('employee-search').value.trim();
    if (!keyword) {
        loadEmployees();
        return;
    }

    const tbody = document.getElementById('employees-table-body');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.forEach(row => {
        const match = Array.from(row.children).some(td => td.textContent.includes(keyword));
        row.style.display = match ? '' : 'none';
    });
}

// 清空搜索
function clearSearch() {
    document.getElementById('employee-search').value = '';
    loadEmployees();
}

// 显示添加员工模态框
async function showAddEmployeeModal() {
    document.getElementById('employee-modal-title').textContent = '添加员工';
    document.getElementById('employee-form').reset();
    document.getElementById('edit-employee-id').value = '';
    document.getElementById('status').value = '在职';

    await loadDepartmentOptions();
    document.getElementById('employee-modal').style.display = 'flex';
}

// 显示编辑员工模态框
async function showEditEmployeeModal(employeeId) {
    try {
        const response = await fetch(`/api/employee/${employeeId}`);
        const data = await response.json();

        if (!data.success) {
            showNotification(data.message || '加载员工信息失败', 'error');
            return;
        }

        const emp = data.data;
        document.getElementById('employee-modal-title').textContent = '编辑员工';
        document.getElementById('edit-employee-id').value = emp.employee_id;
        document.getElementById('employee_name').value = emp.employee_name;
        document.getElementById('gender').value = emp.gender || '';
        document.getElementById('phone').value = emp.phone || '';
        document.getElementById('email').value = emp.email || '';
        document.getElementById('position_name').value = emp.position_name || '';
        document.getElementById('hire_date').value = emp.hire_date || '';
        document.getElementById('status').value = emp.status || '在职';
        document.getElementById('salary').value = emp.salary || '';
        document.getElementById('username').value = emp.username || '';
        document.getElementById('password').value = '';

        await loadDepartmentOptions(emp.department_id);

        document.getElementById('employee-modal').style.display = 'flex';
    } catch (err) {
        console.error('加载员工信息失败', err);
        showNotification('加载员工信息失败', 'error');
    }
}

// 加载部门选项
async function loadDepartmentOptions(selectedId = null) {
    try {
        const response = await fetch('/api/department/list');
        const data = await response.json();

        if (!data.success) return;

        const select = document.getElementById('employee_department_id');
        select.innerHTML = '<option value="">请选择部门</option>';

        data.data.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept.department_id;
            option.textContent = dept.department_name;
            if (selectedId && selectedId === dept.department_id) option.selected = true;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('加载部门列表失败', err);
    }
}

// 保存员工
async function saveEmployee(event) {
    event.preventDefault();

    const form = document.getElementById('employee-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    Object.keys(data).forEach(k => { if (data[k] === '') data[k] = null; });

    const employeeId = document.getElementById('edit-employee-id').value;
    const url = employeeId ? `/api/employee/update/${employeeId}` : '/api/employee/create';
    const method = employeeId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();

        if (result.success) {
            showNotification('员工保存成功', 'success');
            closeAllModals();
            loadEmployees();
        } else {
            showNotification(result.message || '保存失败', 'error');
        }
    } catch (err) {
        console.error('保存员工失败', err);
        showNotification('保存员工失败', 'error');
    }
}

// 显示删除员工确认框
function confirmDeleteEmployee(employeeId, employeeName) {
    deleteItemId = employeeId;
    deleteItemType = 'employee';
    document.getElementById('confirm-message').textContent = `确定要删除员工 "${employeeName}" 吗？`;
    document.getElementById('confirm-delete-btn').onclick = deleteItem;
    document.getElementById('confirm-modal').style.display = 'flex';
}

// 显示删除部门确认框
function confirmDeleteDepartment(departmentId, departmentName) {
    deleteItemId = departmentId;
    deleteItemType = 'department';
    document.getElementById('confirm-message').textContent = `确定要删除部门 "${departmentName}" 吗？`;
    document.getElementById('confirm-delete-btn').onclick = deleteItem;
    document.getElementById('confirm-modal').style.display = 'flex';
}

// 删除操作
async function deleteItem() {
    if (!deleteItemId || !deleteItemType) return;

    const url = deleteItemType === 'employee' 
        ? `/api/employee/delete/${deleteItemId}` 
        : `/api/department/delete/${deleteItemId}`;

    try {
        const response = await fetch(url, { method: 'DELETE' });
        const result = await response.json();

        if (result.success) {
            showNotification(`${deleteItemType === 'employee' ? '员工' : '部门'}删除成功`, 'success');
            if (deleteItemType === 'employee') loadEmployees();
            else loadDepartments();
        } else {
            showNotification(result.message || '删除失败', 'error');
        }
    } catch (err) {
        console.error('删除失败', err);
        showNotification('删除失败', 'error');
    } finally {
        closeConfirmModal();
    }
}

// 关闭确认框
function closeConfirmModal() {
    document.getElementById('confirm-modal').style.display = 'none';
    deleteItemId = null;
    deleteItemType = null;
}


// ==================== 部门管理 ====================

async function loadDepartments() {
    const tbody = document.getElementById('departments-table-body');
    const noDataDiv = document.getElementById('no-departments');

    try {
        const response = await fetch('/api/department/list');
        const data = await response.json();

        if (!data.success || !data.data.length) {
            tbody.innerHTML = '';
            tbody.style.display = 'none';
            noDataDiv.style.display = 'block';
            return;
        }

        noDataDiv.style.display = 'none';
        tbody.style.display = 'table-row-group';

        tbody.innerHTML = data.data.map(dept => {
            const created = dept.create_time || '-';
            const updated = dept.update_time || '-';
            return `
                <tr>
                    <td>${dept.department_id}</td>
                    <td>${dept.department_name}</td>
                    <td>${dept.description || '-'}</td>
                    <td>${created}</td>
                    <td>${updated}</td>
                    <td>
                        <button class="btn btn-warning btn-sm btn-icon" onclick="showEditDepartmentModal('${dept.department_id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger btn-sm btn-icon" onclick="confirmDeleteDepartment('${dept.department_id}', '${dept.department_name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        console.error('加载部门失败', err);
        showNotification('加载部门失败', 'error');
    }
}

// ==================== 统计数据 ====================

async function loadStatistics() {
    try {
        const response = await fetch('/api/employee/statistics');
        const data = await response.json();

        if (!data.success) return;

        document.getElementById('total-employees').textContent = data.total || 0;
        document.getElementById('active-employees').textContent = data.active || 0;
        document.getElementById('terminated-employees').textContent = data.terminated || 0;
        document.getElementById('active-rate').textContent = data.active_rate || '0%';

        // TODO: 渲染部门员工分布图
    } catch (err) {
        console.error('加载统计数据失败', err);
    }
}

// ==================== 模态框与通知 ====================

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => modal.style.display = 'none');
}

function showNotification(msg, type = 'success') {
    const container = document.createElement('div');
    container.className = `notification ${type}`;
    container.textContent = msg;
    Object.assign(container.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        background: type === 'success' ? '#2ecc71' : '#e74c3c',
        color: '#fff',
        padding: '10px 20px',
        borderRadius: '6px',
        zIndex: '9999',
    });
    document.body.appendChild(container);
    setTimeout(() => container.remove(), 3000);
}
