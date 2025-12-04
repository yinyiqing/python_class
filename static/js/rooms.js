// static/js/rooms.js
let allRooms = [];

document.addEventListener('DOMContentLoaded', function() {
    loadRooms();

    // 绑定关闭按钮
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = document.getElementById('room-modal');
            if(modal) modal.style.display = 'none';
        });
    });
});

async function loadRooms() {
    const tbody = document.getElementById('rooms-table-body');
    const loading = document.getElementById('loading-msg');
    const noData = document.getElementById('no-data-msg');

    // 1. 安全检查：如果找不到元素，在控制台报错但不要卡死页面
    if (!tbody || !loading) {
        console.error("Critical Error: HTML elements not found!");
        return;
    }

    // 显示加载圈
    loading.style.display = 'block';
    tbody.innerHTML = '';
    if(noData) noData.style.display = 'none';

    try {
        const res = await fetch('/api/rooms/list');
        const data = await res.json();

        // 隐藏加载圈
        loading.style.display = 'none';

        if (data.success) {
            allRooms = data.data;
            renderTable(allRooms);
        } else {
            alert('加载失败: ' + (data.message || '未知错误'));
        }
    } catch (e) {
        loading.style.display = 'none';
        console.error("Fetch error:", e);
        // 如果出错，至少让用户知道，而不是一直转圈
        alert('网络请求失败，请检查后台服务是否启动');
    }
}

function renderTable(rooms) {
    const tbody = document.getElementById('rooms-table-body');
    const noData = document.getElementById('no-data-msg');

    tbody.innerHTML = '';

    if (!rooms || rooms.length === 0) {
        if(noData) noData.style.display = 'block';
        return;
    }

    rooms.forEach(room => {
        // 状态颜色逻辑
        let statusHtml = `<span class="status-badge status-free">空闲</span>`;
        let btnsHtml = `
            <button class="btn btn-warning btn-sm action-btn" onclick="updateStatus('${room.room_number}', 'reserve')">预订</button>
            <button class="btn btn-success btn-sm action-btn" onclick="updateStatus('${room.room_number}', 'checkin')">入住</button>
            <button class="btn btn-secondary btn-sm action-btn" onclick="openEditModal('${room.room_number}')">编辑</button>
            <button class="btn btn-danger btn-sm action-btn" onclick="deleteRoom('${room.room_number}')">删除</button>
        `;

        if (room.status === '已入住') {
            statusHtml = `<span class="status-badge status-occupied">已入住</span>`;
            btnsHtml = `
                <button class="btn btn-warning btn-sm action-btn" onclick="updateStatus('${room.room_number}', 'checkout')">退房</button>
                <button class="btn btn-secondary btn-sm action-btn" onclick="openEditModal('${room.room_number}')">编辑</button>
            `;
        } else if (room.status === '已预订') {
            statusHtml = `<span class="status-badge status-reserved">已预订</span>`;
            btnsHtml = `
                <button class="btn btn-success btn-sm action-btn" onclick="updateStatus('${room.room_number}', 'checkin')">入住</button>
                <button class="btn btn-danger btn-sm action-btn" onclick="updateStatus('${room.room_number}', 'cancel')">取消</button>
            `;
        }

        const windowIcon = room.has_window ? '<span style="color:#1890ff">✔ 有窗</span>' : '<span style="color:#aaa">无</span>';

        const tr = document.createElement('tr');
        tr.style.borderBottom = "1px solid rgba(255,255,255,0.1)";
        tr.innerHTML = `
            <td style="padding:12px;"><strong>${room.room_number}</strong></td>
            <td style="padding:12px;">${room.room_type}</td>
            <td style="padding:12px;">${statusHtml}</td>
            <td style="padding:12px;">${windowIcon}</td>
            <td style="padding:12px;">${room.area || 23} m²</td>
            <td style="padding:12px;">${room.capacity || 2} 人</td>
            <td style="padding:12px; color: #00c6ff;">¥${room.price}</td>
            <td style="padding:12px;">${btnsHtml}</td>
        `;
        tbody.appendChild(tr);
    });
}

function showAddRoomModal() {
    const modal = document.getElementById('room-modal');
    document.getElementById('modal-title').innerText = "添加房间";
    document.getElementById('room-form').reset();
    document.getElementById('room_number').readOnly = false;
    document.getElementById('is_edit').value = 'false';
    // 默认值
    document.getElementById('area').value = "23";
    document.getElementById('capacity').value = "2";

    modal.style.display = 'flex';
}

function openEditModal(roomNum) {
    const room = allRooms.find(r => r.room_number === roomNum);
    if (!room) return;

    document.getElementById('modal-title').innerText = "编辑房间";
    document.getElementById('is_edit').value = 'true';

    document.getElementById('room_number').value = room.room_number;
    document.getElementById('room_number').readOnly = true;
    document.getElementById('room_type').value = room.room_type;
    document.getElementById('price').value = room.price;
    document.getElementById('description').value = room.description || '';

    // 填充新字段，防止为空
    document.getElementById('area').value = room.area || 23;
    document.getElementById('capacity').value = room.capacity || 2;
    document.getElementById('has_window').checked = (room.has_window === 1);

    document.getElementById('room-modal').style.display = 'flex';
}

async function handleRoomSave(e) {
    e.preventDefault();
    const isEdit = document.getElementById('is_edit').value === 'true';
    const roomNum = document.getElementById('room_number').value;

    const data = {
        room_number: roomNum,
        room_type: document.getElementById('room_type').value,
        price: document.getElementById('price').value,
        description: document.getElementById('description').value,
        area: document.getElementById('area').value,
        capacity: document.getElementById('capacity').value,
        has_window: document.getElementById('has_window').checked ? 1 : 0
    };

    const url = isEdit ? `/api/rooms/update/${roomNum}` : '/api/rooms/add';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await res.json();

        if (result.success) {
            document.getElementById('room-modal').style.display = 'none';
            if(window.showNotification) window.showNotification('保存成功', 'success');
            else alert('保存成功');
            loadRooms();
        } else {
            alert(result.message);
        }
    } catch (err) {
        alert('保存失败');
    }
}

async function deleteRoom(roomNum) {
    if (!confirm(`确认删除房间 ${roomNum} 吗？`)) return;
    const res = await fetch(`/api/rooms/delete/${roomNum}`, {method: 'DELETE'});
    const result = await res.json();
    if (result.success) loadRooms();
    else alert(result.message);
}

async function updateStatus(roomNum, action) {
    const res = await fetch('/api/rooms/status', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({room_number: roomNum, action: action})
    });
    const result = await res.json();
    if (result.success) loadRooms();
    else alert(result.message);
}

function searchRooms() {
    const key = document.getElementById('room-search').value.trim();
    if(!key) { renderTable(allRooms); return; }
    renderTable(allRooms.filter(r => r.room_number.includes(key)));
}