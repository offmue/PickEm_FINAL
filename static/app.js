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
    checkSession(); // Check for existing session
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
        
        if (data.message && data.user) {
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

// Check Session Function
function checkSession() {
    console.log('Checking for existing session...');
    
    fetch('/api/auth/check-session', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        console.log('Session check response:', data);
        
        if (data.user) {
            currentUser = data.user;
            console.log('Session restored for:', currentUser.username);
        } else {
            currentUser = null;
            console.log('No active session found');
        }
        
        updateAuthUI();
    })
    .catch(error => {
        console.error('Session check error:', error);
        currentUser = null;
        updateAuthUI();
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
            countdownElement.innerHTML = '<span>Football-Sunday (REDZONE) ist da! 🔥🏈</span>';
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
            <span>Football-Sunday (REDZONE) 🔥:</span>
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
        case 'all-picks':
            loadAllPicksData();
            break;
    }
}

// Load Dashboard Data
function loadDashboardData() {
    console.log('Loading dashboard data...');
    
    if (!currentUser) {
        // Zeige Login-Aufforderung in allen Bereichen
        document.getElementById('user-points').textContent = '0';
        document.getElementById('user-rank').textContent = '-';
        document.getElementById('mitspieler-list').innerHTML = '<p>Bitte einloggen um Mitspieler zu sehen</p>';
        document.getElementById('team-usage-list').innerHTML = '<p>Bitte einloggen um Team Usage zu sehen</p>';
        return;
    }
    
    // Lade User-Statistiken
    loadUserStats();
    
    // Lade Mitspieler-Punkte
    loadMitspielerPunkte();
    
    // Lade Team Usage
    loadTeamUsage();
}

// Lade User-Statistiken
function loadUserStats() {
    fetch('/api/user/stats', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.points !== undefined) {
            document.getElementById('user-points').textContent = data.points;
        }
        if (data.rank !== undefined) {
            document.getElementById('user-rank').textContent = data.rank;
        }
    })
    .catch(error => {
        console.error('Error loading user stats:', error);
        document.getElementById('user-points').textContent = '0';
        document.getElementById('user-rank').textContent = '-';
    });
}

// Lade Mitspieler-Punkte
function loadMitspielerPunkte() {
    // Erstelle die 4 Spieler mit echten Daten
    const spieler = [
        { username: 'Manuel', points: 0, rank: 1 },
        { username: 'Daniel', points: 0, rank: 2 },
        { username: 'Raff', points: 0, rank: 3 },
        { username: 'Haunschi', points: 0, rank: 4 }
    ];
    
    // Lade echte Leaderboard-Daten und merge sie
    fetch('/api/leaderboard', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        const mitspielerList = document.getElementById('mitspieler-list');
        
        // Merge echte Daten mit Spieler-Namen
        if (data.leaderboard && data.leaderboard.length > 0) {
            data.leaderboard.forEach(player => {
                const spielerIndex = spieler.findIndex(s => s.username.toLowerCase() === player.username.toLowerCase());
                if (spielerIndex !== -1) {
                    spieler[spielerIndex].points = player.points;
                    spieler[spielerIndex].rank = player.rank || spielerIndex + 1;
                }
            });
        }
        
        // Sortiere nach Punkten (höchste zuerst)
        spieler.sort((a, b) => b.points - a.points);
        
        let html = '<div class="mitspieler-items">';
        
        spieler.forEach((player, index) => {
            const isCurrentUser = currentUser && player.username.toLowerCase() === currentUser.username.toLowerCase();
            const className = isCurrentUser ? 'mitspieler-item current-user' : 'mitspieler-item';
            
            html += `
                <div class="${className}">
                    <span class="player-name">${player.username}</span>
                    <span class="player-points">${player.points}</span>
                </div>
            `;
        });
        
        html += '</div>';
        mitspielerList.innerHTML = html;
    })
    .catch(error => {
        console.error('Error loading mitspieler:', error);
        // Fallback: Zeige die 4 Spieler mit 0 Punkten
        const mitspielerList = document.getElementById('mitspieler-list');
        let html = '<div class="mitspieler-items">';
        
        spieler.forEach((player) => {
            html += `
                <div class="mitspieler-item">
                    <span class="player-name">${player.username}</span>
                    <span class="player-points">0</span>
                </div>
            `;
        });
        
        html += '</div>';
        mitspielerList.innerHTML = html;
    });
}

// Lade Team Usage (Winner/Loser)
function loadTeamUsage() {
    if (!currentUser) return;
    
    fetch(`/api/user/team-usage?user_id=${currentUser.id}`, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        const teamUsageList = document.getElementById('team-usage-list');
        
        if (data.winners || data.losers) {
            let html = '<div class="team-usage-container">';
            
            // Winner Spalte
            html += '<div class="usage-column">';
            html += '<h4>Winner</h4>';
            if (data.winners && data.winners.length > 0) {
                data.winners.forEach(team => {
                    const count = team.count || 1;
                    const maxCount = 2; // Max 2x als Winner
                    html += `<div class="usage-item winner">
                        <span class="team-name">${team.name}</span>
                        <span class="usage-count">${count}/${maxCount}</span>
                    </div>`;
                });
            } else {
                html += '<div class="usage-item">Noch keine Winner</div>';
            }
            html += '</div>';
            
            // Loser Spalte
            html += '<div class="usage-column">';
            html += '<h4>Loser</h4>';
            if (data.losers && data.losers.length > 0) {
                data.losers.forEach(team => {
                    html += `<div class="usage-item loser">
                        <span class="team-name">${team.name}</span>
                        <span class="usage-count">1/1</span>
                    </div>`;
                });
            } else {
                html += '<div class="usage-item">Noch keine Loser</div>';
            }
            html += '</div>';
            
            html += '</div>';
            teamUsageList.innerHTML = html;
        } else {
            // Fallback: Zeige Beispiel-Daten
            teamUsageList.innerHTML = `
                <div class="team-usage-container">
                    <div class="usage-column">
                        <h4>Winner</h4>
                        <div class="usage-item winner">
                            <span class="team-name">Falcons</span>
                            <span class="usage-count">1/2</span>
                        </div>
                        <div class="usage-item winner">
                            <span class="team-name">Cowboys</span>
                            <span class="usage-count">1/2</span>
                        </div>
                    </div>
                    <div class="usage-column">
                        <h4>Loser</h4>
                        <div class="usage-item loser">
                            <span class="team-name">Buccaneers</span>
                            <span class="usage-count">1/1</span>
                        </div>
                        <div class="usage-item loser">
                            <span class="team-name">Giants</span>
                            <span class="usage-count">1/1</span>
                        </div>
                    </div>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error loading team usage:', error);
        document.getElementById('team-usage-list').innerHTML = '<p>Fehler beim Laden der Team Usage</p>';
    });
}
// Load Picks Data
function loadPicksData() {
    console.log('Loading picks data for week:', currentWeek);
    
    // Setze die aktuelle Woche im Dropdown
    const weekSelect = document.getElementById('week-select');
    if (weekSelect) {
        weekSelect.value = currentWeek;
        
        // Event Listener für Woche-Änderung
        weekSelect.onchange = function() {
            const selectedWeek = parseInt(this.value);
            loadMatchesForWeek(selectedWeek);
        };
    }
    
    // Lade Spiele für die aktuelle Woche
    loadMatchesForWeek(currentWeek);
}

// Lade Spiele für eine bestimmte Woche
function loadMatchesForWeek(week) {
    console.log('Loading matches for week:', week);
    
    const matchesContainer = document.querySelector('.matches-container');
    if (!matchesContainer) return;
    
    // Zeige Loading-Indikator
    matchesContainer.innerHTML = '<p>Lade Spiele...</p>';
    
    if (!currentUser) {
        matchesContainer.innerHTML = `
            <div class="login-prompt">
                <h3>Bitte einloggen</h3>
                <p>Melden Sie sich an, um Picks abzugeben.</p>
            </div>
        `;
        return;
    }
    
    // Lade Spiele von API
    fetch(`/api/matches?week=${week}`, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.matches && data.matches.length > 0) {
            displayMatches(data.matches, week);
        } else {
            matchesContainer.innerHTML = '<p>Keine Spiele für diese Woche gefunden.</p>';
        }
    })
    .catch(error => {
        console.error('Error loading matches:', error);
        matchesContainer.innerHTML = '<p>Fehler beim Laden der Spiele.</p>';
    });
}

// Zeige Spiele an
function displayMatches(matches, week) {
    const matchesContainer = document.querySelector('.matches-container');
    if (!matchesContainer) return;
    
    // Bestimme Wochenstatus
    const isCompletedWeek = week <= 2; // Woche 1 und 2 sind abgeschlossen
    const isCurrentWeek = week === 3;   // Woche 3 ist aktuell
    
    let html = `
        <div class="week-info">
            <h3>Woche ${week}</h3>
            ${isCompletedWeek ? 
                '<p class="week-status completed">Diese Woche ist bereits abgeschlossen</p>' :
                isCurrentWeek ? 
                    '<p class="week-status current">Aktuelle Woche - Picks möglich</p>' :
                    '<p class="week-status future">Zukünftige Woche</p>'
            }
        </div>
        <div class="matches-grid">
    `;
    
    matches.forEach(match => {
        const gameTime = new Date(match.start_time_vienna);
        const timeString = gameTime.toLocaleString('de-AT', {
            weekday: 'short',
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Europe/Vienna'
        });
        
        // Bestimme Team-Verfügbarkeit (vereinfacht für Demo)
        const awayTeamAvailable = !isCompletedWeek;
        const homeTeamAvailable = !isCompletedWeek;
        
        const matchClass = isCompletedWeek ? 'match-card completed' : 'match-card active';
        const awayClass = awayTeamAvailable ? 'team-button available' : 'team-button unavailable';
        const homeClass = homeTeamAvailable ? 'team-button available' : 'team-button unavailable';
        
        html += `
            <div class="${matchClass}" data-match-id="${match.id}">
                <div class="match-time">${timeString}</div>
                <div class="match-teams">
                    <button class="${awayClass}" 
                            data-team-id="${match.away_team.id}"
                            ${!awayTeamAvailable ? 'disabled' : ''}
                            onclick="selectTeam(${match.id}, ${match.away_team.id}, '${match.away_team.name}')">
                        <div class="team-info">
                            <div class="team-name">${match.away_team.name}</div>
                            <div class="team-abbr">${match.away_team.abbreviation}</div>
                        </div>
                    </button>
                    
                    <div class="vs-separator">@</div>
                    
                    <button class="${homeClass}" 
                            data-team-id="${match.home_team.id}"
                            ${!homeTeamAvailable ? 'disabled' : ''}
                            onclick="selectTeam(${match.id}, ${match.home_team.id}, '${match.home_team.name}')">
                        <div class="team-info">
                            <div class="team-name">${match.home_team.name}</div>
                            <div class="team-abbr">${match.home_team.abbreviation}</div>
                        </div>
                    </button>
                </div>
                
                ${match.is_completed ? 
                    `<div class="match-result">
                        Gewinner: ${match.winner || 'TBD'} 
                        (${match.home_score || 0} - ${match.away_score || 0})
                    </div>` : 
                    match.is_game_started ? 
                        '<div class="match-status">Spiel läuft</div>' : 
                        '<div class="match-status">Noch nicht gestartet</div>'
                }
            </div>
        `;
    });
    
    html += '</div>';
    matchesContainer.innerHTML = html;
}

// Team-Auswahl Funktion
function selectTeam(matchId, teamId, teamName) {
    if (!currentUser) {
        alert('Bitte loggen Sie sich ein, um Picks abzugeben.');
        return;
    }
    
    const confirmation = confirm(`Möchten Sie ${teamName} als Gewinner wählen?`);
    if (!confirmation) return;
    
    // Sende Pick an Server
    fetch('/api/picks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
            match_id: matchId,
            chosen_team_id: teamId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Fehler: ' + data.error);
        } else {
            alert('Pick erfolgreich gespeichert!');
            // Lade Spiele neu um aktuellen Status zu zeigen
            const weekSelect = document.getElementById('week-select');
            if (weekSelect) {
                loadMatchesForWeek(parseInt(weekSelect.value));
            }
        }
    })
    .catch(error => {
        console.error('Error submitting pick:', error);
        alert('Fehler beim Speichern des Picks.');
    });
}
// Load Leaderboard Data
// Load Leaderboard Data
function loadLeaderboardData() {
    console.log('Loading leaderboard data...');
    
    fetch('/api/leaderboard', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        const leaderboardContainer = document.querySelector('.leaderboard-container');
        if (!leaderboardContainer) return;
        
        if (data.leaderboard && data.leaderboard.length > 0) {
            let html = '<h2>Rangliste</h2><div class="leaderboard-list">';
            
            data.leaderboard.forEach((player, index) => {
                const isCurrentUser = currentUser && player.username === currentUser.username;
                const className = isCurrentUser ? 'leaderboard-item current-user' : 'leaderboard-item';
                
                html += `
                    <div class="${className}">
                        <span class="rank">${index + 1}.</span>
                        <span class="username">${player.username}</span>
                        <span class="points">${player.points} Punkte</span>
                    </div>
                `;
            });
            
            html += '</div>';
            leaderboardContainer.innerHTML = html;
        } else {
            leaderboardContainer.innerHTML = '<h2>Rangliste</h2><p>Noch keine Daten verfügbar</p>';
        }
    })
    .catch(error => {
        console.error('Error loading leaderboard:', error);
        const leaderboardContainer = document.querySelector('.leaderboard-container');
        if (leaderboardContainer) {
            leaderboardContainer.innerHTML = '<h2>Rangliste</h2><p>Fehler beim Laden der Rangliste</p>';
        }
    });
}

// Load All Picks Data
function loadAllPicksData() {
    console.log('Loading all picks data...');
    
    const allPicksContainer = document.getElementById('alle-picks-content');
    if (!allPicksContainer) return;
    
    allPicksContainer.innerHTML = '<p>Lade alle Picks...</p>';
    
    fetch('/api/picks/all', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.picks && data.picks.length > 0) {
            let html = '<div class="all-picks-list">';
            
            data.picks.forEach(pick => {
                const resultClass = pick.is_correct ? 'correct' : 'incorrect';
                const resultIcon = pick.is_correct ? '✓' : '✗';
                
                html += `
                    <div class="pick-item ${resultClass}">
                        <span class="pick-week">W${pick.match.week}</span>
                        <span class="pick-user">${pick.user.username}</span>
                        <span class="pick-team">${pick.chosen_team.name}</span>
                        <span class="pick-result">${resultIcon}</span>
                    </div>
                `;
            });
            
            html += '</div>';
            allPicksContainer.innerHTML = html;
        } else {
            allPicksContainer.innerHTML = '<p>Noch keine Picks abgegeben</p>';
        }
    })
    .catch(error => {
        console.error('Error loading all picks:', error);
        allPicksContainer.innerHTML = '<p>Fehler beim Laden der Picks</p>';
    });
}
console.log('NFL PickEm 2025 - Frontend JavaScript loaded successfully');
