// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadTasks();
    loadStats();
});

// ============ TASK CRUD OPERATIONS ============

async function addTask() {
    const title = document.getElementById('taskTitle').value;
    const description = document.getElementById('taskDescription').value;
    const dueDate = document.getElementById('taskDueDate').value;

    if (!title.trim()) {
        alert('Please enter a task title');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                description: description || null,
                due_date: dueDate ? new Date(dueDate).toISOString() : null
            })
        });

        if (response.ok) {
            // Clear form
            document.getElementById('taskTitle').value = '';
            document.getElementById('taskDescription').value = '';
            document.getElementById('taskDueDate').value = '';
            
            loadTasks();
            loadStats();
            alert('Task added successfully!');
        } else {
            alert('Failed to add task');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error adding task');
    }
}

async function loadTasks() {
    const status = document.getElementById('filterStatus').value;
    const url = status 
        ? `${API_BASE_URL}/tasks/?status=${status}` 
        : `${API_BASE_URL}/tasks/`;

    try {
        const response = await fetch(url);
        const tasks = await response.json();

        const container = document.getElementById('tasksContainer');
        if (tasks.length === 0) {
            container.innerHTML = '<p class="text-muted">No tasks found</p>';
            return;
        }

        container.innerHTML = tasks.map(task => `
            <div class="task-item priority-${getPriorityClass(task.priority)}">
                <div class="d-flex justify-content-between align-items-start">
                    <div style="flex: 1;">
                        <h6 class="mb-1">
                            ${task.title}
                            <span class="priority-badge ${getPriorityBadgeClass(task.priority)}">
                                ${formatPriority(task.priority)}
                            </span>
                        </h6>
                        ${task.description ? `<p class="text-muted small mb-2">${task.description}</p>` : ''}
                        <small class="text-muted">
                            Status: <strong>${task.status}</strong>
                            ${task.due_date ? `| Due: ${formatDate(task.due_date)}` : ''}
                            ${task.procrastination_flag ? '| ⚠️ Procrastination flag' : ''}
                        </small>
                    </div>
                    <div class="ms-2">
                        ${task.status !== 'completed' ? `
                            <button class="btn btn-sm btn-success" onclick="completeTask(${task.id})">✓</button>
                        ` : ''}
                        <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">✕</button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

async function completeTask(taskId) {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            loadTasks();
            loadStats();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadTasks();
            loadStats();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// ============ AI OPERATIONS ============

async function generateDailyPlan() {
    const container = document.getElementById('dailyPlanContainer');
    container.innerHTML = '<div class="spinner active"><div class="spinner-border text-primary"></div><p>Generating your daily plan...</p></div>';

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/analyze/daily-plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const plan = await response.json();

        if (plan.today_plan.length === 0) {
            container.innerHTML = '<p class="text-muted">No tasks to plan for today</p>';
            return;
        }

        let html = '<div class="daily-plan">';
        html += '<h6 class="mb-3">✨ AI-Optimized Schedule</h6>';
        
        if (plan.today_plan && plan.today_plan.length > 0) {
            html += '<strong>Today\'s Priority Order:</strong><ol>';
            plan.today_plan.forEach((task, index) => {
                html += `<li>${task}</li>`;
            });
            html += '</ol>';
        }

        if (plan.insights) {
            html += `<hr><strong>💡 AI Insights:</strong><p class="mb-0">${plan.insights}</p>`;
        }

        html += '</div>';
        container.innerHTML = html;
    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = '<p class="text-danger">Failed to generate plan</p>';
    }
}

async function generateWeeklyReport() {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/analyze/weekly-report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const report = await response.json();
        const aiReport = report.ai_report;

        let html = `
            <div class="alert alert-info">
                <h5>📊 Weekly Productivity Report</h5>
                <p><strong>Completion Rate:</strong> ${aiReport.completion_rate?.toFixed(1) || 0}%</p>
                <p><strong>Summary:</strong> ${aiReport.summary}</p>
                
                <hr>
                <h6>💪 Strengths:</h6>
                <ul>${(aiReport.strengths || []).map(s => `<li>${s}</li>`).join('')}</ul>
                
                <h6>📈 Areas for Improvement:</h6>
                <ul>${(aiReport.areas_for_improvement || []).map(a => `<li>${a}</li>`).join('')}</ul>
                
                <h6>✅ Recommended Actions:</h6>
                <ul>${(aiReport.recommended_actions || []).map(a => `<li>${a}</li>`).join('')}</ul>
            </div>
        `;

        alert(html);
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to generate report');
    }
}

// ============ STATS & DISPLAY ============

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/stats/summary`);
        const stats = await response.json();

        const container = document.getElementById('statsContainer');
        container.innerHTML = `
            <div class="row">
                <div class="col-6 mb-2">
                    <div class="stats-box">
                        <p class="small">Total</p>
                        <h3>${stats.total_tasks}</h3>
                    </div>
                </div>
                <div class="col-6 mb-2">
                    <div class="stats-box">
                        <p class="small">Completed</p>
                        <h3>${stats.completed}</h3>
                    </div>
                </div>
                <div class="col-6">
                    <div class="stats-box">
                        <p class="small">Rate</p>
                        <h3>${stats.completion_rate.toFixed(0)}%</h3>
                    </div>
                </div>
                <div class="col-6">
                    <div class="stats-box">
                        <p class="small">Urgent</p>
                        <h3>${stats.urgent_important}</h3>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ============ UTILITY FUNCTIONS ============

function formatPriority(priority) {
    const map = {
        'urgent_important': 'Urgent & Important',
        'important_not_urgent': 'Important',
        'urgent_not_important': 'Urgent',
        'neither': 'Low'
    };
    return map[priority] || priority;
}

function getPriorityClass(priority) {
    const map = {
        'urgent_important': 'urgent',
        'important_not_urgent': 'important',
        'urgent_not_important': 'normal',
        'neither': 'normal'
    };
    return map[priority] || 'normal';
}

function getPriorityBadgeClass(priority) {
    const map = {
        'urgent_important': 'urgent',
        'important_not_urgent': 'important',
        'urgent_not_important': 'normal',
        'neither': 'normal'
    };
    return map[priority] || 'normal';
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}
