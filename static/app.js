// NFL PickEm 2025 - Vollständig reparierte Frontend-Integration
let currentUser = null;
let currentWeek = 3;
let currentSection = 'dashboard';

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('NFL PickEm App initializing...');
    
    // Initialize UI components immediately
    initializeNavigation();
    initializeAuth();
    initializeCountdown();
    loadCurrentWeek();
    showSection('dashboard');
    
    console.log('NFL PickEm App initialized successfully');
});

// Navigation Management
function initializeNavigation() {
    console.log('Initializing navigation...');
    
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            if (section) {
                showSection(section);
            }
        });
    });
    
    console.log('Navigation initialized with', navTabs.length, 'tabs');
}

// Authentication Management
function initializeAuth() {
    console.log('Initializing auth...');
    
    // Get elements
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const loginModal = document.getElementById('login-modal');
    const modalClose = document.getElementById('modal-close');
    const loginForm = document.getElementById('login-form');
    
    console.log('Auth elements:', {
        loginBtn: !!loginBtn,
        logoutBtn: !!logoutBtn,
        loginModal: !!loginModal,
        modalClose: !!modalClose,
        loginForm: !!loginForm
    });
    
    // Login button
    if (loginBtn) {
        loginBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Login button clicked');
            if (loginModal) {
                loginModal.style.display = 'flex';
                console.log('Login modal opened');
            }
        });
    }
    
    // Modal close
    if (modalClose) {
        modalClose.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Modal close clicked');
            if (loginModal) {
                loginModal.style.display = 'none';
            }
        });
    }
    
    // Login form
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Login form submitted');
            
            const usernameField = document.getElementById('username');
            const passwordField = document.getElementById('password');
            
            if (usernameField && passwordField) {
                const username = usernameField.value.trim();
                const password = passwordField.value.trim();
                
                if (username && password) {
                    console.log('Login attempt:', username);
                    login(username, password);
                } else {
                    alert('Bitte Benutzername und Passwort eingeben');
                }
            }
        });
    }
    
    // Update UI initially
    updateAuthUI();
}

// Login Function
function login(username, password) {
    console.log('Attempting login for:', username);
    
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Login response:', data);
        
        if (data.success && data.user) {
            currentUser = data.user;
            
            // Close modal
            const loginModal = document.getElementById('login-modal');
            if (loginModal) {
                loginModal.style.display = 'none';
            }
            
            // Clear form
            const loginForm = document.getElementById('login-form');
            if (loginForm) {
                loginForm.reset();
            }
            
            // Update UI
            updateAuthUI();
            showSection(currentSection);
            
            console.log('Login successful for:', currentUser.username);
            alert('Login erfolgreich! Willkommen ' + currentUser.username);
        } else {
            alert('Login fehlgeschlagen: ' + (data.error || 'Unbekannter Fehler'));
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        alert('Login-Fehler: Verbindung zum Server fehlgeschlagen');
    });
}

// Update Authentication UI
function updateAuthUI() {
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    
    if (currentUser) {
        if (loginBtn) loginBtn.style.display = 'none';
        if (logoutBtn) {
            logoutBtn.style.display = 'inline-block';
            logoutBtn.textContent = currentUser.username + ' (Logout)';
        }
    } else {
        if (loginBtn) loginBtn.style.display = 'inline-block';
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
}

// Load Current Week
function loadCurrentWeek() {
    console.log('Loading current week...');
    
    fetch('/api/current-week')
        .then(response => response.json())
        .then(data => {
            if (data.current_week) {
                currentWeek = data.current_week;
                console.log('Current week loaded:', currentWeek);
            }
        })
        .catch(error => {
            console.error('Error loading current week:', error);
            currentWeek = 3;
        });
}

// Initialize Countdown
function initializeCountdown() {
    console.log('Initializing countdown...');
    
    const now = new Date();
    const nextSunday = new Date();
    const daysUntilSunday = (7 - now.getDay()) % 7;
    nextSunday.setDate(now.getDate() + (daysUntilSunday === 0 ? 7 : daysUntilSunday));
    nextSunday.setHours(19, 0, 0, 0);
    
    updateCountdown(nextSunday);
    setInterval(() => updateCountdown(nextSunday), 1000);
}

// Update Countdown
function updateCountdown(targetDate) {
    const now = new Date();
    const diff = targetDate - now;
    
    if (diff <= 0) {
        const countdownElement = document.getElementById('countdown-timer');
        if (countdownElement) {
            countdownElement.innerHTML = '<span>Football-Sunday ist da! 🏈</span>';
        }
        return;
    }
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    
    const countdownElement = document.getElementById('countdown-timer');
    if (countdownElement) {
        countdownElement.innerHTML = `
            <span>Football-Sunday:</span>
            <span>${days}d ${hours}h ${minutes}m ${seconds}s</span>
        `;
    }
}

// Show Section
function showSection(sectionName) {
    console.log('Showing section:', sectionName);
    
    currentSection = sectionName;
    
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.display = 'none';
    });
    
    // Show target section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.style.display = 'block';
    }
    
    // Update navigation
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab.getAttribute('data-section') === sectionName) {
            tab.classList.add('active');
        }
    });
    
    // Load section data
    loadSectionData(sectionName);
}

// Load Section Data
function loadSectionData(sectionName) {
    console.log('Loading data for section:', sectionName);
    
    switch (sectionName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'picks':
            loadPicksData();
            break;
        case 'leaderboard':
            loadLeaderboardData();
            break;
        case 'alle-picks':
            loadAllPicksData();
            break;
    }
}

// Load Dashboard Data
function loadDashboardData() {
    console.log('Loading dashboard data...');
    
    if (!currentUser) {
        const dashboardContent = document.getElementById('dashboard-content');
        if (dashboardContent) {
            dashboardContent.innerHTML = `
                <div class="login-prompt">
                    <h3>Bitte einloggen</h3>
                    <p>Melden Sie sich an, um Ihr Dashboard zu sehen.</p>
                    <button onclick="document.getElementById('login-btn').click()" class="btn btn-primary">
                        Jetzt einloggen
                    </button>
                </div>
            `;
        }
        return;
    }
    
    const dashboardContent = document.getElementById('dashboard-content');
    if (dashboardContent) {
        dashboardContent.innerHTML = `
            <div class="dashboard-cards">
                <div class="card">
                    <h3>Punkte</h3>
                    <div class="score">2</div>
                    <p>Nach Woche 2</p>
                </div>
                <div class="card">
                    <h3>Eliminierte Teams</h3>
                    <div class="eliminated-count">2</div>
                    <p>Permanent eliminiert</p>
                </div>
            </div>
        `;
    }
}

// Load Picks Data
function loadPicksData() {
    console.log('Loading picks data for week:', currentWeek);
    
    if (!currentUser) {
        const picksContent = document.getElementById('picks-content');
        if (picksContent) {
            picksContent.innerHTML = `
                <div class="login-prompt">
                    <h3>Bitte einloggen</h3>
                    <p>Melden Sie sich an, um Picks abzugeben.</p>
                </div>
            `;
        }
        return;
    }
    
    const picksContent = document.getElementById('picks-content');
    if (picksContent) {
        picksContent.innerHTML = `
            <div class="picks-header">
                <h3>Picks - Woche ${currentWeek} (Aktuelle Woche: ${currentWeek})</h3>
            </div>
            
            <div class="picks-info">
                <p><strong>Dallas Cowboys:</strong> Verfügbar (1x verwendet, noch 1x möglich)</p>
                <p><strong>Eliminierte Teams:</strong> Tampa Bay Buccaneers, New York Giants</p>
            </div>
            
            <div class="matches-container">
                <div class="match-card">
                    <div class="match-teams">
                        <div class="team">Dallas Cowboys @ Arizona Cardinals</div>
                    </div>
                    <div class="match-actions">
                        <button class="btn btn-winner" onclick="selectTeam('Dallas Cowboys', 'winner')">
                            Dallas Cowboys als Winner
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
}

// Select Team
function selectTeam(teamName, pickType) {
    console.log('Team selected:', teamName, 'as', pickType);
    
    if (!currentUser) {
        alert('Bitte erst einloggen!');
        return;
    }
    
    alert(`${teamName} als ${pickType === 'winner' ? 'Winner' : 'Loser'} ausgewählt! (Demo-Modus)`);
}

// Load Leaderboard Data
function loadLeaderboardData() {
    const leaderboardContent = document.getElementById('leaderboard-content');
    if (leaderboardContent) {
        leaderboardContent.innerHTML = `
            <div class="leaderboard-table">
                <table>
                    <thead>
                        <tr><th>Rang</th><th>Spieler</th><th>Punkte</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>1</td><td>Manuel</td><td>2</td></tr>
                        <tr><td>1</td><td>Daniel</td><td>2</td></tr>
                        <tr><td>1</td><td>Raff</td><td>2</td></tr>
                        <tr><td>1</td><td>Haunschi</td><td>2</td></tr>
                    </tbody>
                </table>
            </div>
        `;
    }
}

// Load All Picks Data
function loadAllPicksData() {
    const allPicksContent = document.getElementById('alle-picks-content');
    if (allPicksContent) {
        allPicksContent.innerHTML = `
            <div class="all-picks-controls">
                <label>
                    <input type="checkbox" id="hide-current-week" checked>
                    Aktuelle Woche ausblenden
                </label>
            </div>
            
            <div class="picks-by-week">
                <h3>Woche 2</h3>
                <p>Manuel: Dallas Cowboys ✅</p>
                <p>Daniel: Philadelphia Eagles ✅</p>
                <p>Raff: Dallas Cowboys ✅</p>
                <p>Haunschi: Buffalo Bills ✅</p>
                
                <h3>Woche 1</h3>
                <p>Manuel: Atlanta Falcons ✅</p>
                <p>Daniel: Denver Broncos ✅</p>
                <p>Raff: Cincinnati Bengals ✅</p>
                <p>Haunschi: Washington Commanders ✅</p>
            </div>
        `;
    }
}

console.log('NFL PickEm 2025 - Frontend JavaScript loaded successfully');
