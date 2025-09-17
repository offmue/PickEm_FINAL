/**
 * Frontend JavaScript für NFL PickEm 2025 Picks-Sektion
 * Mit Team-Logos und vollständiger Pick-Funktionalität
 */

class PicksFrontend {
    constructor() {
        this.currentWeek = 3; // Default, wird von API überschrieben
        this.userPick = null;
        this.matches = [];
        this.teamAvailability = {};
        
        this.init();
    }
    
    async init() {
        console.log('🏈 Initializing Picks Frontend...');
        
        // Event Listeners
        this.setupEventListeners();
        
        // Lade aktuelle Woche
        await this.loadCurrentWeek();
        
        // Lade Picks-Daten
        await this.loadPicksData();
        
        console.log('✅ Picks Frontend initialized');
    }
    
    setupEventListeners() {
        // Week Selector
        const weekSelector = document.getElementById('week-selector');
        if (weekSelector) {
            weekSelector.addEventListener('change', (e) => {
                this.currentWeek = parseInt(e.target.value);
                this.loadPicksData();
            });
        }
    }
    
    async loadCurrentWeek() {
        try {
            const response = await fetch('/api/current-week');
            const data = await response.json();
            
            if (data.success) {
                this.currentWeek = data.current_week;
                
                // Week Selector aktualisieren
                const weekSelector = document.getElementById('week-selector');
                if (weekSelector) {
                    weekSelector.value = this.currentWeek;
                }
                
                console.log(`📅 Current week: ${this.currentWeek}`);
            }
        } catch (error) {
            console.error('❌ Error loading current week:', error);
        }
    }
    
    async loadPicksData() {
        try {
            console.log(`🔄 Loading picks data for week ${this.currentWeek}...`);
            
            // Parallel laden: Matches und Team Availability
            const [matchesResponse, teamsResponse] = await Promise.all([
                fetch(`/api/matches/${this.currentWeek}`),
                fetch(`/api/teams/available/${this.currentWeek}`)
            ]);
            
            const matchesData = await matchesResponse.json();
            const teamsData = await teamsResponse.json();
            
            if (matchesData.success) {
                this.matches = matchesData.matches;
                this.userPick = matchesData.user_pick;
            }
            
            if (teamsData.success) {
                this.teamAvailability = teamsData.teams;
            }
            
            // UI aktualisieren
            this.updatePicksUI();
            
        } catch (error) {
            console.error('❌ Error loading picks data:', error);
            this.showError('Fehler beim Laden der Picks-Daten');
        }
    }
    
    updatePicksUI() {
        // Week Status aktualisieren
        this.updateWeekStatus();
        
        // Matches anzeigen
        this.displayMatches();
        
        // User Pick Status anzeigen
        this.displayUserPickStatus();
    }
    
    updateWeekStatus() {
        const statusElement = document.getElementById('week-status');
        if (!statusElement) return;
        
        let statusText = '';
        let statusClass = '';
        
        if (this.currentWeek < 3) {
            statusText = `Woche ${this.currentWeek} ist bereits abgeschlossen`;
            statusClass = 'week-completed';
        } else if (this.currentWeek === 3) {
            statusText = `Woche ${this.currentWeek} - Picks möglich`;
            statusClass = 'week-active';
        } else {
            statusText = `Woche ${this.currentWeek} - Zukünftige Woche`;
            statusClass = 'week-future';
        }
        
        statusElement.textContent = statusText;
        statusElement.className = `week-status ${statusClass}`;
    }
    
    displayMatches() {
        const matchesContainer = document.getElementById('matches-container');
        if (!matchesContainer) return;
        
        if (this.matches.length === 0) {
            matchesContainer.innerHTML = '<p class=\"no-matches\">Keine Spiele für diese Woche gefunden.</p>';
            return;
        }
        
        const matchesHTML = this.matches.map(match => this.createMatchHTML(match)).join('');
        matchesContainer.innerHTML = matchesHTML;
        
        // Event Listeners für Team-Buttons
        this.setupMatchEventListeners();
    }
    
    createMatchHTML(match) {
        const isUserPick = match.is_user_pick;
        const canPick = match.can_pick;
        const isStarted = match.is_started;
        const isCompleted = match.is_completed;
        
        // Team Availability prüfen
        const homeTeamAvailable = this.isTeamAvailable(match.home_team.id);
        const awayTeamAvailable = this.isTeamAvailable(match.away_team.id);
        
        // Match Status
        let matchStatus = '';
        if (isCompleted) {
            const winner = match.winner_team_id === match.home_team.id ? match.home_team : match.away_team;
            matchStatus = `<div class=\"match-result\">Gewinner: ${winner.name} (${match.home_score}-${match.away_score})</div>`;
        } else if (isStarted) {
            matchStatus = '<div class=\"match-started\">Spiel läuft</div>';
        } else {
            const gameTime = new Date(match.start_time).toLocaleString('de-AT', {
                weekday: 'short',
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'Europe/Vienna'
            });
            matchStatus = `<div class=\"match-time\">${gameTime}</div>`;
        }
        
        return `
            <div class=\"match-card ${isUserPick ? 'user-pick' : ''} ${!canPick ? 'disabled' : ''}\" data-match-id=\"${match.id}\">
                ${matchStatus}
                
                <div class=\"match-teams\">
                    <div class=\"team-container\">
                        <button class=\"team-button away-team ${match.user_chosen_team_id === match.away_team.id ? 'selected' : ''} ${!canPick || !awayTeamAvailable ? 'disabled' : ''}\" 
                                data-team-id=\"${match.away_team.id}\" 
                                data-match-id=\"${match.id}\"
                                ${!canPick || !awayTeamAvailable ? 'disabled' : ''}>
                            <img src=\"${match.away_team.logo_url}\" alt=\"${match.away_team.name}\" class=\"team-logo\" onerror=\"this.style.display='none'\">
                            <div class=\"team-info\">
                                <div class=\"team-name\">${match.away_team.name}</div>
                                <div class=\"team-abbr\">${match.away_team.abbreviation}</div>
                            </div>
                            ${match.user_chosen_team_id === match.away_team.id ? '<div class=\"pick-checkmark\">✓</div>' : ''}
                        </button>
                        ${!awayTeamAvailable ? '<div class=\"team-unavailable\">Nicht verfügbar</div>' : ''}
                    </div>
                    
                    <div class=\"vs-separator\">@</div>
                    
                    <div class=\"team-container\">
                        <button class=\"team-button home-team ${match.user_chosen_team_id === match.home_team.id ? 'selected' : ''} ${!canPick || !homeTeamAvailable ? 'disabled' : ''}\" 
                                data-team-id=\"${match.home_team.id}\" 
                                data-match-id=\"${match.id}\"
                                ${!canPick || !homeTeamAvailable ? 'disabled' : ''}>
                            <img src=\"${match.home_team.logo_url}\" alt=\"${match.home_team.name}\" class=\"team-logo\" onerror=\"this.style.display='none'\">
                            <div class=\"team-info\">
                                <div class=\"team-name\">${match.home_team.name}</div>
                                <div class=\"team-abbr\">${match.home_team.abbreviation}</div>
                            </div>
                            ${match.user_chosen_team_id === match.home_team.id ? '<div class=\"pick-checkmark\">✓</div>' : ''}
                        </button>
                        ${!homeTeamAvailable ? '<div class=\"team-unavailable\">Nicht verfügbar</div>' : ''}
                    </div>
                </div>
                
                ${isUserPick ? '<div class=\"user-pick-indicator\">Dein Pick für diese Woche</div>' : ''}
            </div>
        `;
    }
    
    isTeamAvailable(teamId) {
        const teamInfo = this.teamAvailability[teamId];
        return teamInfo ? teamInfo.available : false;
    }
    
    setupMatchEventListeners() {
        const teamButtons = document.querySelectorAll('.team-button:not(.disabled)');
        
        teamButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                const teamId = parseInt(button.dataset.teamId);
                const matchId = parseInt(button.dataset.matchId);
                
                this.selectTeam(matchId, teamId);
            });
        });
    }
    
    async selectTeam(matchId, teamId) {
        try {
            // Bestätigung anzeigen
            const match = this.matches.find(m => m.id === matchId);
            const team = match.home_team.id === teamId ? match.home_team : match.away_team;
            
            const confirmed = confirm(`Möchtest du ${team.name} als Gewinner wählen?`);
            if (!confirmed) return;
            
            // Loading-State anzeigen
            this.showLoading('Pick wird gespeichert...');
            
            // Pick an Backend senden
            const response = await fetch('/api/picks/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    match_id: matchId,
                    chosen_team_id: teamId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(`Pick erfolgreich gespeichert: ${result.chosen_team}`);
                
                // Daten neu laden
                await this.loadPicksData();
            } else {
                this.showError(result.message || 'Fehler beim Speichern des Picks');
            }
            
        } catch (error) {
            console.error('❌ Error selecting team:', error);
            this.showError('Fehler beim Speichern des Picks');
        } finally {
            this.hideLoading();
        }
    }
    
    displayUserPickStatus() {
        const statusContainer = document.getElementById('user-pick-status');
        if (!statusContainer) return;
        
        if (this.userPick) {
            const match = this.matches.find(m => m.id === this.userPick.match_id);
            if (match) {
                statusContainer.innerHTML = `
                    <div class=\"user-pick-summary\">
                        <h4>Dein Pick für Woche ${this.currentWeek}:</h4>
                        <div class=\"pick-details\">
                            <strong>${this.userPick.chosen_team.name}</strong> gewinnt gegen ${this.userPick.loser_team.name}
                            ${this.userPick.can_change ? '<span class=\"can-change\">(Änderung möglich)</span>' : '<span class=\"cannot-change\">(Nicht mehr änderbar)</span>'}
                        </div>
                    </div>
                `;
            }
        } else {
            statusContainer.innerHTML = `
                <div class=\"no-pick-message\">
                    <p>Du hast noch keinen Pick für Woche ${this.currentWeek} abgegeben.</p>
                </div>
            `;
        }
    }
    
    showLoading(message = 'Lädt...') {
        const loadingElement = document.getElementById('loading-message');
        if (loadingElement) {
            loadingElement.textContent = message;
            loadingElement.style.display = 'block';
        }
    }
    
    hideLoading() {
        const loadingElement = document.getElementById('loading-message');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showMessage(message, type = 'info') {
        // Erstelle Message-Element falls nicht vorhanden
        let messageElement = document.getElementById('message-container');
        if (!messageElement) {
            messageElement = document.createElement('div');
            messageElement.id = 'message-container';
            messageElement.className = 'message-container';
            document.body.appendChild(messageElement);
        }
        
        messageElement.innerHTML = `
            <div class=\"message message-${type}\">
                ${message}
                <button class=\"message-close\" onclick=\"this.parentElement.parentElement.style.display='none'\">&times;</button>
            </div>
        `;
        messageElement.style.display = 'block';
        
        // Auto-hide nach 5 Sekunden
        setTimeout(() => {
            messageElement.style.display = 'none';
        }, 5000);
    }
}

// Initialisierung wenn DOM geladen
document.addEventListener('DOMContentLoaded', () => {
    // Nur initialisieren wenn wir auf der Picks-Seite sind
    if (document.getElementById('picks-content')) {
        window.picksFrontend = new PicksFrontend();
    }
});

// Export für andere Module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PicksFrontend;
}

