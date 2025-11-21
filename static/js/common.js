// 显示通知
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}-circle"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// 更新用户信息
function updateUserInfo() {
    // 从模板变量获取用户名
    const usernameElement = document.getElementById('userName');
    const username = usernameElement?.textContent || '管理员';

    // 头像取前两个字符
    const avatar = document.getElementById('userAvatar');
    if (avatar && username && username.length >= 2) {
        avatar.textContent = username.substring(0, 2).toUpperCase();
    }
}

// 初始化下拉菜单
function initDropdown() {
    const userAvatar = document.getElementById('userAvatar');
    const userDropdown = document.getElementById('userDropdown');

    if (!userAvatar || !userDropdown) return;

    // 用户头像点击事件 - 显示/隐藏下拉菜单
    userAvatar.addEventListener('click', function(e) {
        e.stopPropagation();

        // 切换显示状态
        if (userDropdown.style.display === 'none' || userDropdown.style.display === '') {
            userDropdown.style.display = 'block';

            // 添加展开动画
            setTimeout(() => {
                userDropdown.style.opacity = '1';
                userDropdown.style.transform = 'translateY(0) scale(1)';
            }, 10);
        } else {
            // 添加收起动画
            userDropdown.style.opacity = '0';
            userDropdown.style.transform = 'translateY(-10px) scale(0.95)';

            setTimeout(() => {
                userDropdown.style.display = 'none';
            }, 300);
        }
    });

    // 点击其他地方关闭下拉菜单
    document.addEventListener('click', function() {
        if (userDropdown.style.display === 'block') {
            // 添加收起动画
            userDropdown.style.opacity = '0';
            userDropdown.style.transform = 'translateY(-10px) scale(0.95)';

            setTimeout(() => {
                userDropdown.style.display = 'none';
            }, 300);
        }
    });

    // 阻止下拉菜单内部的点击事件冒泡
    userDropdown.addEventListener('click', function(e) {
        e.stopPropagation();
    });
}

// 初始化修改密码功能
function initChangePassword() {
    const changePasswordBtn = document.getElementById('changePasswordBtn');
    const userDropdown = document.getElementById('userDropdown');
    const changePasswordModal = document.getElementById('changePasswordModal');
    const changePasswordForm = document.getElementById('changePasswordForm');

    if (!changePasswordBtn || !changePasswordForm) return;

    // 修改密码按钮事件
    changePasswordBtn.addEventListener('click', function(e) {
        e.preventDefault();
        if (userDropdown) {
            userDropdown.style.display = 'none';
        }
        if (changePasswordModal) {
            changePasswordModal.style.display = 'flex';
        }
    });

    // 关闭模态框
    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', function() {
            if (changePasswordModal) {
                changePasswordModal.style.display = 'none';
            }
            if (changePasswordForm) {
                changePasswordForm.reset();
            }
        });
    });

    // 修改密码表单提交
    changePasswordForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (!currentPassword || !newPassword || !confirmPassword) {
            showNotification('请填写所有字段', 'error');
            return;
        }

        if (newPassword !== confirmPassword) {
            showNotification('新密码和确认密码不匹配', 'error');
            return;
        }

        if (newPassword.length < 6) {
            showNotification('新密码长度至少6位', 'error');
            return;
        }

        // 发送修改密码请求到后端
        fetch('/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `currentPassword=${encodeURIComponent(currentPassword)}&newPassword=${encodeURIComponent(newPassword)}&confirmPassword=${encodeURIComponent(confirmPassword)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (changePasswordModal) {
                    changePasswordModal.style.display = 'none';
                }
                if (changePasswordForm) {
                    changePasswordForm.reset();
                }
                showNotification(data.message, 'success');
            } else {
                showNotification(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('修改密码请求失败', 'error');
        });
    });
}

// 初始化退出登录功能
function initLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/logout';
        });
    }
}

// 初始化页面
function initPage() {
    // 显示主容器
    const mainContainer = document.querySelector('.main-container');
    if (mainContainer) {
        mainContainer.style.display = 'flex';
    }

    // 更新用户信息
    updateUserInfo();

    // 初始化各功能模块
    initDropdown();
    initChangePassword();
    initLogout();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initPage();
});