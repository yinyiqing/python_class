// static/js/employees.js

// 全局变量
let currentTab = 'employees';
let departmentsData = [];
let deleteCallback = null;
let deleteItemId = null;
let deleteItemType = null;

// 页面加载初始化
document.addEventListener('DOMContentLoaded', function() {
    loadEmployees();
    loadDepartments();
    loadStatistics();

    // 初始化模态框关闭按钮
    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', function() {
            closeAllModals();
        });
    });
});

// 切换标签页
function switchTab(tabName) {
    currentTab = tabName;

    // 更新标签页状态
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // 激活当前标签页
    event.target.closest('.tab').classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // 根据标签页加载数据
    if (tabName === 'employees') {
        loadEmployees();
    } else if (tabName === 'departments') {
        loadDepartments();
    } else if (tabName === 'statistics') {
        loadStatistics();
    }
}

// ==================== 员工管理功能 ====================

// 加载员工列表
async function loadEmployees() {
    try {
        showLoading('employees-table-body');

        const response = await fetch('/api/employee/list');
        const data = await response.json();

        if (data.success) {
            renderEmployeesTable(data.data);
        } else {
            // 如果是空数据，应该显示空状态而不是错误
            if (data.message && data.message.includes('0名员工')) {
                renderEmployeesTable([]);  // 传入空数组显示空状态
            } else {
                showError(data.message || '加载员工列表失败');
            }
        }
    } catch (error) {
        console.error('加载员工列表失败:', error);
        showError('加载员工列表失败');
    }
}

// 渲染员工表格
function renderEmployeesTable(employees) {
    const tbody = document.getElementById('employees-table-body');
    const noDataDiv = document.getElementById('no-employees');

    if (!employees || employees.length === 0) {
        tbody.innerHTML = '';
        tbody.style.display = 'none';
        noDataDiv.style.display = 'block';
        return;
    }

    tbody.style.display = 'table-row-group';
    noDataDiv.style.display = 'none';

    let html = '';
    employees.forEach(emp => {
        const statusClass = emp.status === '在职' ? 'active' : 'inactive';
        const hireDate = emp.hire_date ? formatDate(emp.hire_date) : '-';

        html += `
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
    });

    tbody.innerHTML = html;
}

// 搜索员工
async function searchEmployees() {
    const keyword = document.getElementById('employee-search').value.trim();

    if (!keyword) {
        loadEmployees();
        return;
    }

    try {
        showLoading('employees-table-body');

        // 这里可以调用搜索API，暂时用客户端过滤
        const response = await fetch('/api/employee/list');
        const data = await response.json();

        if (data.success) {
            const filtered = data.data.filter(emp => {
                return emp.employee_id.includes(keyword) ||
                       emp.employee_name.includes(keyword) ||
                       (emp.phone && emp.phone.includes(keyword));
            });

            renderEmployeesTable(filtered);
        }
    } catch (error) {
        console.error('搜索员工失败:', error);
        showError('搜索员工失败');
    }
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

    // 设置默认值
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('hire_date').value = today;
    document.getElementById('status').value = '在职';

    // 加载部门选项
    await loadDepartmentOptions();

    // 显示模态框
    document.getElementById('employee-modal').style.display = 'flex';
}

// 显示编辑员工模态框
async function showEditEmployeeModal(employeeId) {
    try {
        const response = await fetch(`/api/employee/${employeeId}`);
        const data = await response.json();

        if (data.success) {
            const emp = data.data;

            document.getElementById('employee-modal-title').textContent = '编辑员工';
            document.getElementById('edit-employee-id').value = emp.employee_id;

            // 填充表单
            document.getElementById('employee_name').value = emp.employee_name;
            document.getElementById('gender').value = emp.gender || '';
            document.getElementById('phone').value = emp.phone || '';
            document.getElementById('email').value = emp.email || '';
            document.getElementById('position_name').value = emp.position_name || '';
            document.getElementById('hire_date').value = emp.hire_date || '';
            document.getElementById('status').value = emp.status || '在职';
            document.getElementById('salary').value = emp.salary || '';
            document.getElementById('username').value = emp.username || '';

            // 清空密码字段
            document.getElementById('password').value = '';

            // 加载部门选项并选中当前部门
            await loadDepartmentOptions(emp.department_id);

            // 显示模态框
            document.getElementById('employee-modal').style.display = 'flex';
        } else {
            showError(data.message);
        }
    } catch (error) {
        console.error('加载员工信息失败:', error);
        showError('加载员工信息失败');
    }
}

// 加载部门选项
async function loadDepartmentOptions(selectedId = null) {
    try {
        const response = await fetch('/api/department/list');
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('department_id');
            select.innerHTML = '<option value="">请选择部门</option>';

            data.data.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.department_id;
                option.textContent = dept.department_name;
                if (selectedId && dept.department_id === selectedId) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载部门列表失败:', error);
    }
}

// 保存员工
async function saveEmployee(event) {
    event.preventDefault();

    const form = document.getElementById('employee-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // 处理空值
    Object.keys(data).forEach(key => {
        if (data[key] === '') data[key] = null;
    });

    const employeeId = document.getElementById('edit-employee-id').value;
    const url = employeeId ? `/api/employee/update/${employeeId}` : '/api/employee/create';
    const method = employeeId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('员工保存成功', 'success');
            closeAllModals();
            loadEmployees();
        } else {
            showError(result.message);
        }
    } catch (error) {
        console.error('保存员工失败:', error);
        showError('保存员工失败');
    }
}

// 确认删除员工
function confirmDeleteEmployee(employeeId, employeeName) {
    deleteItemId = employeeId;
    deleteItemType = 'employee';

    document.getElementById('confirm-message').textContent =
        `确定要删除员工 "${employeeName}" 吗？此操作不可恢复！`;

    document.getElementById('confirm-modal').style.display = 'flex';
    // 移除之前的监听器以防止重复绑定（更安全的做法）
    const btn = document.getElementById('confirm-delete-btn');
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);
    newBtn.addEventListener('click', executeDelete);
}

// 执行删除 (提取为单独函数)
async function executeDelete() {
    if (!deleteItemId || !deleteItemType) return;

    try {
        let url, method = 'DELETE';

        if (deleteItemType === 'employee') {
            url = `/api/employee/delete/${deleteItemId}`;
        } else if (deleteItemType === 'department') {
            url = `/api/department/delete/${deleteItemId}`;
        }

        const response = await fetch(url, { method: method });
        const result = await response.json();

        if (result.success) {
            showNotification('删除成功', 'success');
            closeConfirmModal();

            if (deleteItemType === 'employee') {
                loadEmployees();
            } else if (deleteItemType === 'department') {
                loadDepartments();
                if (currentTab === 'employees') {
                    await loadDepartmentOptions();
                }
            }
        } else {
            showError(result.message);
        }
    } catch (error) {
        console.error('删除失败:', error);
        showError('删除失败');
    }

    deleteItemId = null;
    deleteItemType = null;
}

// ==================== 部门管理功能 ====================

// 加载部门列表
async function loadDepartments() {
    try {
        showLoading('departments-table-body');

        const response = await fetch('/api/department/list');
        const data = await response.json();

        if (data.success) {
            departmentsData = data.data;
            renderDepartmentsTable(data.data);
        } else {
            showError('加载部门列表失败');
        }
    } catch (error) {
        console.error('加载部门列表失败:', error);
        showError('加载部门列表失败');
    }
}

// 渲染部门表格
function renderDepartmentsTable(departments) {
    const tbody = document.getElementById('departments-table-body');
    const noDataDiv = document.getElementById('no-departments');

    if (!departments || departments.length === 0) {
        tbody.innerHTML = '';
        tbody.style.display = 'none';
        noDataDiv.style.display = 'block';
        return;
    }

    tbody.style.display = 'table-row-group';
    noDataDiv.style.display = 'none';

    let html = '';
    departments.forEach(dept => {
        const createdAt = dept.created_at ? formatDateTime(dept.created_at) : '-';
        const updatedAt = dept.updated_at ? formatDateTime(dept.updated_at) : '-';

        html += `
            <tr>
                <td>${dept.department_id}</td>
                <td>${dept.department_name}</td>
                <td>${dept.description || '-'}</td>
                <td>${createdAt}</td>
                <td>${updatedAt}</td>
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
    });

    tbody.innerHTML = html;
}

// 显示添加部门模态框
function showAddDepartmentModal() {
    document.getElementById('department-modal-title').textContent = '添加部门';
    document.getElementById('department-form').reset();
    document.getElementById('edit-department-id').value = '';

    document.getElementById('department-modal').style.display = 'flex';
}

// 显示编辑部门模态框
function showEditDepartmentModal(departmentId) {
    const dept = departmentsData.find(d => d.department_id === departmentId);
    if (dept) {
        document.getElementById('department-modal-title').textContent = '编辑部门';
        document.getElementById('edit-department-id').value = dept.department_id;

        document.getElementById('department_id').value = dept.department_id;
        document.getElementById('department_name').value = dept.department_name;
        document.getElementById('description').value = dept.description || '';

        document.getElementById('department-modal').style.display = 'flex';
    }
}

// 保存部门
async function saveDepartment(event) {
    event.preventDefault();

    const form = document.getElementById('department-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    const departmentId = document.getElementById('edit-department-id').value;
    const url = departmentId ? `/api/department/update/${departmentId}` : '/api/department/create';
    const method = departmentId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('部门保存成功', 'success');
            closeAllModals();
            loadDepartments();

            // 如果当前在员工管理标签页，重新加载部门选项
            if (currentTab === 'employees') {
                await loadDepartmentOptions();
            }
        } else {
            showError(result.message);
        }
    } catch (error) {
        console.error('保存部门失败:', error);
        showError('保存部门失败');
    }
}

// 确认删除部门
function confirmDeleteDepartment(departmentId, departmentName) {
    deleteItemId = departmentId;
    deleteItemType = 'department';

    document.getElementById('confirm-message').textContent =
        `确定要删除部门 "${departmentName}" 吗？此操作不可恢复！`;

    document.getElementById('confirm-modal').style.display = 'flex';
    // 绑定删除执行
    const btn = document.getElementById('confirm-delete-btn');
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);
    newBtn.addEventListener('click', executeDelete);
}

// ==================== 统计功能 ====================

// 加载统计信息
async function loadStatistics() {
    try {
        const response = await fetch('/api/employee/statistics');
        const data = await response.json();

        if (data.success) {
            const stats = data.data;

            // 更新统计卡片
            if(document.getElementById('total-employees')) {
                document.getElementById('total-employees').textContent = stats.total;
                document.getElementById('active-employees').textContent = stats.active;
                document.getElementById('terminated-employees').textContent = stats.terminated;
                document.getElementById('active-rate').textContent = stats.active_rate.toFixed(1) + '%';
                // 渲染部门分布
                renderDepartmentChart(stats.by_department);
            }
        }
    } catch (error) {
        console.error('加载统计信息失败:', error);
    }
}

// 渲染部门分布图表
function renderDepartmentChart(departments) {
    const container = document.getElementById('department-chart');
    if (!container) return;

    if (!departments || departments.length === 0) {
        container.innerHTML = '<p style="color: var(--color-gray-light); text-align: center;">暂无部门数据</p>';
        return;
    }

    // 计算总人数用于百分比
    let total = 0;
    departments.forEach(dept => total += dept.count);

    let html = '<div style="display: flex; flex-direction: column; gap: 10px;">';

    departments.forEach(dept => {
        const count = dept.count || 0;
        const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
        const width = Math.max(5, percentage); // 最小宽度

        html += `
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="min-width: 120px; color: var(--color-light);">${dept.department_name}</div>
                <div style="flex: 1; height: 20px; background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden;">
                    <div style="height: 100%; width: ${width}%; background: linear-gradient(to right, var(--color-accent), #00c6ff); border-radius: 10px;"></div>
                </div>
                <div style="min-width: 60px; text-align: right; color: var(--color-accent); font-weight: bold;">
                    ${count} 人
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

// ==================== 通用功能 ====================

// 关闭确认模态框
function closeConfirmModal() {
    document.getElementById('confirm-modal').style.display = 'none';
    deleteItemId = null;
    deleteItemType = null;
}

// 关闭所有模态框
function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

// 显示加载状态
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 40px;">
                    <i class="fas fa-spinner fa-spin"></i> 加载中...
                </td>
            </tr>
        `;
    }
}

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

// 格式化日期时间
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '-';
    const date = new Date(dateTimeString);
    return date.toLocaleString('zh-CN');
}

// [核心修复] 显示通知 - 增加保底逻辑
function showNotification(message, type = 'success') {
    // 检查 window.showNotification 是否存在 (common.js 是否加载)
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        // 如果 common.js 没加载，使用 alert 作为保底
        // 只有 success 类型才 alert，避免 error 类型的 alert 太烦人（但这里为了确保看到反馈，都 alert）
        alert(message);
        console.log(`[${type}] ${message}`);
    }
}

// 显示错误
function showError(message) {
    showNotification(message, 'error');
}