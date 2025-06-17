/* 管理画面用JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    // サイドバートグル機能
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarMenu = document.getElementById('sidebarMenu');
    
    if (sidebarToggle && sidebarMenu) {
        sidebarToggle.addEventListener('click', function() {
            // モバイルでのサイドバー表示/非表示
            if (window.innerWidth < 768) {
                sidebarMenu.classList.toggle('show');
            }
        });
    }
    
    // アクティブなサブメニューを開く
    const activeNavLink = document.querySelector('.sidebar .nav-link.active');
    if (activeNavLink) {
        const parentCollapse = activeNavLink.closest('.collapse');
        if (parentCollapse) {
            parentCollapse.classList.add('show');
        }
    }
    
    // アラートの自動非表示
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.querySelector('.btn-close')) {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.remove();
                }, 300);
            }, 5000);
        }
    });
    
    // フォームの送信確認
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
    
    // テーブルの行選択機能
    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="selected_items"]');
    const selectAllCheckbox = document.getElementById('selectAll');
    
    if (selectAllCheckbox && checkboxes.length > 0) {
        selectAllCheckbox.addEventListener('change', function() {
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionButtons();
        });
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateSelectAllState();
                updateBulkActionButtons();
            });
        });
    }
    
    function updateSelectAllState() {
        if (selectAllCheckbox) {
            const checkedCount = document.querySelectorAll('input[type="checkbox"][name="selected_items"]:checked').length;
            selectAllCheckbox.checked = checkedCount === checkboxes.length;
            selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
        }
    }
    
    function updateBulkActionButtons() {
        const selectedCount = document.querySelectorAll('input[type="checkbox"][name="selected_items"]:checked').length;
        const bulkActionButtons = document.querySelectorAll('.bulk-action-btn');
        
        bulkActionButtons.forEach(button => {
            button.style.display = selectedCount > 0 ? 'inline-block' : 'none';
        });
        
        // 選択数を表示
        const selectedCountElement = document.getElementById('selectedCount');
        if (selectedCountElement) {
            selectedCountElement.textContent = selectedCount;
        }
    }
    
    // ツールチップの初期化
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // ポップオーバーの初期化
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// ダッシュボード統計のアニメーション
function animateNumbers() {
    const numberElements = document.querySelectorAll('.stats-number[data-value]');
    
    numberElements.forEach(element => {
        const finalValue = parseInt(element.getAttribute('data-value'));
        const duration = 2000;
        const stepTime = 50;
        const steps = duration / stepTime;
        const increment = finalValue / steps;
        
        let currentValue = 0;
        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= finalValue) {
                currentValue = finalValue;
                clearInterval(timer);
            }
            element.textContent = Math.floor(currentValue).toLocaleString();
        }, stepTime);
    });
}

// ページ読み込み完了時に数字アニメーションを実行
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', animateNumbers);
} else {
    animateNumbers();
}