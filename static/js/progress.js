const motivationMessages = {
    0: "Start your journey today! Every master was once a beginner.",
    1: "Great start! You're building momentum. Keep it going!",
    2: "Two days strong! You're forming a habit. Don't stop now!",
    3: "Three days! You're on fire! 🔥",
    4: "Four days! Consistency is key!",
    5: "Five days! You're becoming unstoppable!",
    6: "A full week! You're building something amazing!",
    7: "One week strong! This is just the beginning!",
    10: "Double digits! You're a force to be reckoned with!",
    14: "Two weeks! You're halfway to a month!",
    21: "Three weeks! You've built a real habit!",
    30: "A full month! You're a true master of consistency!",
    50: "50 days! You're in the top 1% of achievers!",
    100: "100 DAYS! You're a legend! 🏆"
};

function getMotivationMessage(streak) {
    const keys = Object.keys(motivationMessages).map(Number).sort((a, b) => b - a);
    for (const key of keys) {
        if (streak >= key) {
            return motivationMessages[key];
        }
    }
    return motivationMessages[0];
}

document.addEventListener('DOMContentLoaded', async function() {
    try {
        const response = await fetch('/api/progress');
        const data = await response.json();
        
        if (response.ok) {
            displayProgress(data);
        } else {
            document.getElementById('history-list').innerHTML = 
                '<div class="loading">Error loading progress</div>';
        }
    } catch (error) {
        document.getElementById('history-list').innerHTML = 
            '<div class="loading">Error loading progress</div>';
    }
});

function displayProgress(data) {
    const { streak, sessions, skill_stats, daily_data } = data;
    
    // Update streak
    document.getElementById('streak-count').textContent = streak;
    document.getElementById('motivation-message').innerHTML = 
        `<p>${getMotivationMessage(streak)}</p>`;
    
    // Update stats
    document.getElementById('total-sessions').textContent = sessions.length;
    const totalMinutes = sessions.reduce((sum, s) => sum + (s.duration || 0), 0);
    document.getElementById('total-time').textContent = totalMinutes;
    document.getElementById('skills-count').textContent = skill_stats.length;
    
    // Display streak visual
    const streakVisual = document.getElementById('streak-visual');
    streakVisual.innerHTML = '';
    for (let i = 0; i < Math.min(streak, 30); i++) {
        const day = document.createElement('div');
        day.className = 'streak-day active';
        day.textContent = '🔥';
        day.title = `Day ${i + 1}`;
        streakVisual.appendChild(day);
    }
    
    // Display skills
    const skillsList = document.getElementById('skills-list');
    if (skill_stats.length === 0) {
        skillsList.innerHTML = '<div class="loading">No skills tracked yet. Start practicing!</div>';
    } else {
        skillsList.innerHTML = skill_stats.map(skill => `
            <div class="skill-item">
                <div class="skill-name">${escapeHtml(skill.skill_name)}</div>
                <div class="skill-stats">
                    <span>${skill.session_count || 0} sessions</span>
                    <span>${Math.floor((skill.total_time || 0) / 60)}h ${(skill.total_time || 0) % 60}m</span>
                </div>
            </div>
        `).join('');
    }
    
    // Display history
    const historyList = document.getElementById('history-list');
    if (sessions.length === 0) {
        historyList.innerHTML = '<div class="loading">No sessions yet. Complete your first practice session!</div>';
    } else {
        historyList.innerHTML = sessions.map(session => {
            const date = new Date(session.completed_at);
            const dateStr = date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric', 
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            let proofHtml = '';
            if (session.proof_file) {
                const fileUrl = `/uploads/${session.proof_file}`;
                const fileExt = session.proof_file.split('.').pop().toLowerCase();
                
                if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExt)) {
                    proofHtml = `
                        <div class="proof-preview">
                            <img src="${fileUrl}" alt="Proof" class="proof-image" onclick="openProofModal('${fileUrl}', 'image')">
                        </div>
                    `;
                } else if (['mp4', 'mov', 'avi'].includes(fileExt)) {
                    proofHtml = `
                        <div class="proof-preview">
                            <video controls class="proof-video" onclick="event.stopPropagation()">
                                <source src="${fileUrl}" type="video/${fileExt === 'mov' ? 'quicktime' : fileExt}">
                            </video>
                        </div>
                    `;
                } else if (fileExt === 'pdf') {
                    proofHtml = `
                        <div class="proof-preview">
                            <a href="${fileUrl}" target="_blank" class="proof-link">
                                <span class="proof-icon">📄</span>
                                <span>View PDF</span>
                            </a>
                        </div>
                    `;
                }
            }
            
            return `
                <div class="history-item">
                    <div class="history-info">
                        <div class="history-skill">${escapeHtml(session.skill_name)}</div>
                        <div class="history-date">${dateStr}</div>
                        ${proofHtml}
                    </div>
                    <div class="history-duration">${session.duration || 0} min</div>
                </div>
            `;
        }).join('');
    }

    renderCalendar(Array.isArray(daily_data) ? daily_data : []);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function openProofModal(fileUrl, type) {
    if (type === 'image') {
        const modal = document.createElement('div');
        modal.className = 'proof-modal';
        modal.innerHTML = `
            <div class="proof-modal-content">
                <span class="proof-modal-close" onclick="this.closest('.proof-modal').remove()">&times;</span>
                <img src="${fileUrl}" alt="Proof" class="proof-modal-image">
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
}

function renderCalendar(dailyData) {
    const calendarGrid = document.getElementById('calendar-grid');
    const rangeLabel = document.getElementById('calendar-range');
    if (!calendarGrid) return;

    const CALENDAR_WEEKS = 20;
    const DAYS_IN_WEEK = 7;
    const totalDays = CALENDAR_WEEKS * DAYS_IN_WEEK;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - (totalDays - 1));
    // Align to Monday
    const dayOfWeek = (startDate.getDay() + 6) % 7;
    startDate.setDate(startDate.getDate() - dayOfWeek);

    const startDateCopy = new Date(startDate);
    if (rangeLabel) {
        rangeLabel.textContent = `${formatRangeLabel(startDateCopy)} – ${formatRangeLabel(today, true)}`;
    }

    const activityMap = dailyData.reduce((acc, day) => {
        if (day.session_date) {
            acc[day.session_date] = day.session_count || 0;
        }
        return acc;
    }, {});

    const fragment = document.createDocumentFragment();
    const cursor = new Date(startDate);

    for (let i = 0; i < totalDays; i++) {
        const isoDate = cursor.toISOString().split('T')[0];
        const cell = document.createElement('div');
        cell.className = 'calendar-cell';
        cell.setAttribute('data-date', isoDate);

        if (cursor > today) {
            cell.classList.add('calendar-future');
            cell.title = `${isoDate} • Upcoming`;
        } else if (activityMap[isoDate] > 0) {
            const sessions = activityMap[isoDate];
            cell.classList.add('calendar-active');
            cell.title = `${isoDate} • ${sessions} session${sessions > 1 ? 's' : ''}`;
        } else {
            cell.classList.add('calendar-missed');
            cell.title = `${isoDate} • Missed`;
        }

        fragment.appendChild(cell);
        cursor.setDate(cursor.getDate() + 1);
    }

    calendarGrid.innerHTML = '';
    calendarGrid.appendChild(fragment);
}

function formatRangeLabel(date, includeYear = false) {
    const options = {
        month: 'short',
        day: 'numeric',
        year: includeYear ? 'numeric' : undefined
    };
    return date.toLocaleDateString('en-US', options);
}

