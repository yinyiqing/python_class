// static/js/employees.js

// === 调试标记：V2025.12.05-FixEdit ===
console.log('%c 员工管理脚本已加载 - FixEdit ', 'background: #222; color: #bada55; font-size: 16px');

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
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    event.target.closest('.tab').classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');

    if (tabName === 'employees') loadEmployees();
    else if (tabName === 'departments') loadDepartments();
    else if (tabName === 'statistics') loadStatistics();
}

// ==================== 员工管理功能 ====================

// 加载员工列表
async function loadEmployees() {
    try {
        showLoading('employees-table-body');
        const response = await fetch(`/api/employee/list?t=${new Date().getTime()}`);
        const data = await response.json();

        if (data.success) {
            renderEmployeesTable(data.data);
        } else {
            if (data.message && data.message.includes('0名员工')) {
                renderEmployeesTable([]);
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
        // 确保ID是字符串处理，防止数字ID导致的引用错误
        const safeId = String(emp.employee_id);
        const safeName = String(emp.employee_name).replace(/'/g, "\\'"); // 防止名字里有单引号导致报错

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
                    <button class="btn btn-warning btn-sm btn-icon" onclick="showEditEmployeeModal('${safeId}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-danger btn-sm btn-icon" onclick="confirmDeleteEmployee('${safeId}', '${safeName}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// [核心修复] 显示编辑员工模态框 - 增强健壮性
async function showEditEmployeeModal(employeeId) {
    console.log(`点击编辑: ${employeeId}`); // 调试日志

    try {
        // 1. 获取最新数据
        const response = await fetch(`/api/employee/${employeeId}?t=${new Date().getTime()}`);
        if (!response.ok) throw new Error('网络请求失败');

        const data = await response.json();

        if (data.success) {
            const emp = data.data;

            document.getElementById('employee-modal-title').textContent = '编辑员工';

            // 2. 安全赋值函数 (防止某个ID不存在导致整个函数崩溃)
            const setVal = (id, val) => {
                const el = document.getElementById(id);
                if(el) el.value = (val === null || val === undefined) ? '' : val;
            };

            setVal('edit-employee-id', emp.employee_id);
            setVal('employee_name', emp.employee_name);
            setVal('gender', emp.gender);
            setVal('phone', emp.phone);
            setVal('email', emp.email);
            setVal('position_name', emp.position_name);
            setVal('hire_date', emp.hire_date);
            setVal('status', emp.status || '在职');
            setVal('salary', emp.salary);
            setVal('username', emp.username);
            setVal('password', ''); // 密码清空

            // 3. 加载部门，即使失败也要显示模态框
            try {
                await loadDepartmentOptions(emp.department_id);
            } catch (deptErr) {
                console.error("加载部门列表失败，但继续显示表单", deptErr);
            }

            // 4. 显示模态框
            const modal = document.getElementById('employee-modal');
            if(modal) {
                modal.style.display = 'flex';
                console.log("模态框已打开");
            } else {
                console.error("找不到模态框元素: employee-modal");
            }

        } else {
            showError(data.message || '获取员工信息失败');
        }
    } catch (error) {
        console.error('加载员工信息异常:', error);
        showError('加载员工信息失败，请检查控制台日志');
    }
}

// 搜索员工
async function searchEmployees() {
    const keyword = document.getElementById('employee-search').value.trim();
    if (!keyword) { loadEmployees(); return; }

    try {
        showLoading('employees-table-body');
        const response = await fetch(`/api/employee/list?t=${new Date().getTime()}`);
        const data = await response.json();

        if (data.success) {
            const filtered = data.data.filter(emp => {
                return String(emp.employee_id).includes(keyword) ||
                       String(emp.employee_name).includes(keyword) ||
                       (emp.phone && String(emp.phone).includes(keyword));
            });
            renderEmployeesTable(filtered);
        }
    } catch (error) {
        console.error('搜索员工失败:', error);
        showError('搜索员工失败');
    }
}

function clearSearch() {
    document.getElementById('employee-search').value = '';
    loadEmployees();
}

// 显示添加员工模态框
async function showAddEmployeeModal() {
    document.getElementById('employee-modal-title').textContent = '添加员工';
    document.getElementById('employee-form').reset();
    document.getElementById('edit-employee-id').value = '';

    const today = new Date().toISOString().split('T')[0];
    document.getElementById('hire_date').value = today;
    document.getElementById('status').value = '在职';

    await loadDepartmentOptions();
    document.getElementById('employee-modal').style.display = 'flex';
}

// 加载部门选项
async function loadDepartmentOptions(selectedId = null) {
    try {
        const response = await fetch('/api/department/list');
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('department_id');
            if(!select) return;

            select.innerHTML = '<option value="">请选择部门</option>';

            data.data.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.department_id;
                option.textContent = dept.department_name;
                // 宽松匹配 (防止 string vs int 问题)
                if (selectedId && String(dept.department_id) === String(selectedId)) {
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

    Object.keys(data).forEach(key => { if (data[key] === '') data[key] = null; });

    const employeeId = document.getElementById('edit-employee-id').value;
    const url = employeeId ? `/api/employee/update/${employeeId}` : '/api/employee/create';
    const method = employeeId ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();

        if (result.success) {
            showNotification('员工保存成功', 'success');
            closeAllModals();
            await loadEmployees();
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

    document.getElementById('confirm-message').textContent = `确定要删除员工 "${employeeName}" 吗？此操作不可恢复！`;
    document.getElementById('confirm-modal').style.display = 'flex';

    const btn = document.getElementById('confirm-delete-btn');
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);
    newBtn.addEventListener('click', executeDelete);
}

// 执行删除
async function executeDelete() {
    if (!deleteItemId || !deleteItemType) return;
    const currentType = deleteItemType;
    const currentId = deleteItemId;

    try {
        const url = currentType === 'employee' ?
                   `/api/employee/delete/${currentId}` :
                   `/api/department/delete/${currentId}`;

        const response = await fetch(url, { method: 'DELETE' });
        const result = await response.json();

        if (result.success) {
            showNotification('删除成功', 'success');
            closeConfirmModal();

            if (currentType === 'employee') await loadEmployees();
            else if (currentType === 'department') {
                await loadDepartments();
                if (currentTab === 'employees') await loadDepartmentOptions();
            }
        } else {
            showError(result.message);
        }
    } catch (error) {
        console.error('删除失败:', error);
        showError('删除失败');
    }
}

// ==================== 部门管理/统计/通用 ====================

async function loadDepartments() {
    try {
        showLoading('departments-table-body');
        const response = await fetch(`/api/department/list?t=${new Date().getTime()}`);
        const data = await response.json();
        if (data.success) {
            departmentsData = data.data;
            renderDepartmentsTable(data.data);
        } else showError('加载部门列表失败');
    } catch (error) { showError('加载部门列表失败'); }
}

function renderDepartmentsTable(departments) {
    const tbody = document.getElementById('departments-table-body');
    const noDataDiv = document.getElementById('no-departments');
    if (!departments || departments.length === 0) {
        tbody.innerHTML = ''; tbody.style.display = 'none'; noDataDiv.style.display = 'block'; return;
    }
    tbody.style.display = 'table-row-group'; noDataDiv.style.display = 'none';

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
                    <button class="btn btn-warning btn-sm btn-icon" onclick="showEditDepartmentModal('${dept.department_id}')"><i class="fas fa-edit"></i></button>
                    <button class="btn btn-danger btn-sm btn-icon" onclick="confirmDeleteDepartment('${dept.department_id}', '${dept.department_name}')"><i class="fas fa-trash"></i></button>
                </td>
            </tr>`;
    });
    tbody.innerHTML = html;
}

function showAddDepartmentModal() {
    document.getElementById('department-modal-title').textContent = '添加部门';
    document.getElementById('department-form').reset();
    document.getElementById('edit-department-id').value = '';
    document.getElementById('department-modal').style.display = 'flex';
}

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
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
            showNotification('部门保存成功', 'success');
            closeAllModals();
            await loadDepartments();
            if (currentTab === 'employees') await loadDepartmentOptions();
        } else showError(result.message);
    } catch (error) { showError('保存部门失败'); }
}

function confirmDeleteDepartment(departmentId, departmentName) {
    deleteItemId = departmentId; deleteItemType = 'department';
    document.getElementById('confirm-message').textContent = `确定要删除部门 "${departmentName}" 吗？此操作不可恢复！`;
    document.getElementById('confirm-modal').style.display = 'flex';
    const btn = document.getElementById('confirm-delete-btn');
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);
    newBtn.addEventListener('click', executeDelete);
}

async function loadStatistics() {
    try {
        const response = await fetch('/api/employee/statistics');
        const data = await response.json();
        if (data.success) {
            const stats = data.data;
            if(document.getElementById('total-employees')) {
                document.getElementById('total-employees').textContent = stats.total;
                document.getElementById('active-employees').textContent = stats.active;
                document.getElementById('terminated-employees').textContent = stats.terminated;
                document.getElementById('active-rate').textContent = stats.active_rate.toFixed(1) + '%';
                renderDepartmentChart(stats.by_department);
            }
        }
    } catch (error) { console.error('加载统计信息失败:', error); }
}

function renderDepartmentChart(departments) {
    const container = document.getElementById('department-chart');
    if (!container) return;
    if (!departments || departments.length === 0) {
        container.innerHTML = '<p style="color: var(--color-gray-light); text-align: center;">暂无部门数据</p>'; return;
    }
    let total = 0; departments.forEach(dept => total += dept.count);
    let html = '<div style="display: flex; flex-direction: column; gap: 10px;">';
    departments.forEach(dept => {
        const count = dept.count || 0;
        const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
        html += `
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="min-width: 120px; color: var(--color-light);">${dept.department_name}</div>
                <div style="flex: 1; height: 20px; background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden;">
                    <div style="height: 100%; width: ${Math.max(5, percentage)}%; background: linear-gradient(to right, var(--color-accent), #00c6ff); border-radius: 10px;"></div>
                </div>
                <div style="min-width: 60px; text-align: right; color: var(--color-accent); font-weight: bold;">${count} 人</div>
            </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
}

function closeConfirmModal() { document.getElementById('confirm-modal').style.display = 'none'; deleteItemId = null; deleteItemType = null; }
function closeAllModals() { document.querySelectorAll('.modal').forEach(modal => modal.style.display = 'none'); }
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) element.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 40px;"><i class="fas fa-spinner fa-spin"></i> 加载中...</td></tr>`;
}
function formatDate(dateString) { if (!dateString) return '-'; return new Date(dateString).toLocaleDateString('zh-CN'); }
function formatDateTime(dateTimeString) { if (!dateTimeString) return '-'; return new Date(dateTimeString).toLocaleString('zh-CN'); }
function showNotification(message, type = 'success') {
    if (typeof window.showNotification === 'function') window.showNotification(message, type);
    else { alert(message); console.log(`[${type}] ${message}`); }
}
function showError(message) { showNotification(message, 'error'); }