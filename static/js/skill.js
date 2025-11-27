let currentSkillId = null;
let timerInterval = null;
let totalSeconds = 0;
let targetSeconds = 0;
let isPaused = false;
let timerRunning = false;

document.addEventListener('DOMContentLoaded', function() {
    const skillTypeInputs = document.querySelectorAll('input[name="skill-type"]');
    const othersInputGroup = document.getElementById('others-input-group');
    const skillNameInput = document.getElementById('skill-name');
    const challengesSection = document.getElementById('challenges-section');
    const challengesContainer = document.getElementById('challenges-container');
    
    // Handle skill type selection
    skillTypeInputs.forEach(input => {
        input.addEventListener('change', async () => {
            const selectedSkill = input.value;
            
            if (selectedSkill === 'Others') {
                othersInputGroup.style.display = 'block';
                skillNameInput.required = true;
                challengesSection.style.display = 'none';
            } else {
                othersInputGroup.style.display = 'none';
                skillNameInput.required = false;
                challengesSection.style.display = 'block';
                
                // Fetch challenges
                challengesContainer.innerHTML = '<div class="loading-small">Loading challenges...</div>';
                
                try {
                    const response = await fetch('/api/challenges', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            skill_type: selectedSkill
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success && data.challenges) {
                        challengesContainer.innerHTML = data.challenges.map((challenge, index) => `
                            <div class="challenge-item">
                                <div class="challenge-number">${index + 1}</div>
                                <div class="challenge-text">${escapeHtml(challenge)}</div>
                            </div>
                        `).join('');
                    } else {
                        challengesContainer.innerHTML = '<div class="loading-small">Unable to load challenges. You can still proceed!</div>';
                    }
                } catch (error) {
                    challengesContainer.innerHTML = '<div class="loading-small">Unable to load challenges. You can still proceed!</div>';
                }
            }
        });
    });
    
    // Skill form submission
    document.getElementById('skillForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const selectedSkillType = document.querySelector('input[name="skill-type"]:checked').value;
        let skillName;
        
        if (selectedSkillType === 'Others') {
            skillName = document.getElementById('skill-name').value.trim();
            if (!skillName) {
                alert('Please enter a skill name');
                return;
            }
        } else {
            skillName = selectedSkillType;
        }
        
        const targetTime = parseInt(document.querySelector('input[name="target-time"]:checked').value);
        
        try {
            const response = await fetch('/api/skills', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    skill_name: skillName,
                    target_time: targetTime
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                currentSkillId = data.skill_id;
                targetSeconds = targetTime * 60;
                totalSeconds = 0;
                
                // Hide form, show timer
                document.getElementById('skillForm').parentElement.style.display = 'none';
                document.getElementById('timer-section').style.display = 'block';
                document.getElementById('skill-display').textContent = skillName;
                
                startTimer();
            } else {
                alert(data.error || 'Failed to create skill');
            }
        } catch (error) {
            alert('An error occurred. Please try again.');
        }
    });
    
    // Timer controls
    document.getElementById('pause-btn').addEventListener('click', () => {
        if (isPaused) {
            resumeTimer();
        } else {
            pauseTimer();
        }
    });
    
    document.getElementById('stop-btn').addEventListener('click', () => {
        stopTimer();
    });
    
    // File upload
    const fileInput = document.getElementById('proof-file');
    const filePreview = document.getElementById('file-preview');
    
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            filePreview.classList.add('show');
            filePreview.innerHTML = '';
            
            if (file.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                filePreview.appendChild(img);
            } else if (file.type.startsWith('video/')) {
                const video = document.createElement('video');
                video.src = URL.createObjectURL(file);
                video.controls = true;
                video.style.maxWidth = '100%';
                filePreview.appendChild(video);
            } else {
                filePreview.innerHTML = `<p>📄 ${file.name}</p>`;
            }
        }
    });
    
    // Upload form
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fileInput = document.getElementById('proof-file');
        if (!fileInput.files[0]) {
            alert('Please select a file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        try {
            // Upload file
            const uploadResponse = await fetch('/api/upload-proof', {
                method: 'POST',
                body: formData
            });
            
            const uploadData = await uploadResponse.json();
            
            if (uploadData.success) {
                // Create session
                const sessionResponse = await fetch('/api/sessions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        skill_id: currentSkillId,
                        duration: Math.floor(totalSeconds / 60),
                        proof_file: uploadData.filename
                    })
                });
                
                const sessionData = await sessionResponse.json();
                
                if (sessionData.success) {
                    alert('🎉 Great job! Your session has been recorded!');
                    window.location.href = '/progress';
                } else {
                    alert('Failed to save session');
                }
            } else {
                alert(uploadData.error || 'Failed to upload file');
            }
        } catch (error) {
            alert('An error occurred. Please try again.');
        }
    });
});

function startTimer() {
    timerRunning = true;
    isPaused = false;
    document.getElementById('pause-btn').textContent = 'Pause';
    
    timerInterval = setInterval(() => {
        if (!isPaused) {
            totalSeconds++;
            updateTimerDisplay();
            
            if (totalSeconds >= targetSeconds) {
                completeTimer();
            }
        }
    }, 1000);
}

function pauseTimer() {
    isPaused = true;
    document.getElementById('pause-btn').textContent = 'Resume';
}

function resumeTimer() {
    isPaused = false;
    document.getElementById('pause-btn').textContent = 'Pause';
}

function stopTimer() {
    if (confirm('Are you sure you want to stop? Your progress will be lost.')) {
        clearInterval(timerInterval);
        timerRunning = false;
        window.location.reload();
    }
}

function completeTimer() {
    clearInterval(timerInterval);
    timerRunning = false;
    
    // Hide timer, show upload
    document.getElementById('timer-section').style.display = 'none';
    document.getElementById('upload-section').style.display = 'block';
}

function updateTimerDisplay() {
    const remaining = targetSeconds - totalSeconds;
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    
    document.getElementById('timer-minutes').textContent = 
        minutes.toString().padStart(2, '0');
    document.getElementById('timer-seconds').textContent = 
        seconds.toString().padStart(2, '0');
    
    // Update progress circle
    const progress = (totalSeconds / targetSeconds) * 565.48;
    const progressCircle = document.getElementById('timer-progress');
    progressCircle.style.strokeDashoffset = (565.48 - progress).toString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

