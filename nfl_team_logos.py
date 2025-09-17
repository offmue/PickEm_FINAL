#!/usr/bin/env python3
"""
NFL Team-Logo Mapping für NFL PickEm 2025
Hochqualitative Team-Logos für Frontend-Integration
"""

# NFL Team-Logo URLs (hochqualitativ und konsistent)
NFL_TEAM_LOGOS = {
    # AFC East
    'BUF': 'https://a.espncdn.com/i/teamlogos/nfl/500/buf.png',
    'MIA': 'https://a.espncdn.com/i/teamlogos/nfl/500/mia.png',
    'NE': 'https://a.espncdn.com/i/teamlogos/nfl/500/ne.png',
    'NYJ': 'https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png',
    
    # AFC North
    'BAL': 'https://a.espncdn.com/i/teamlogos/nfl/500/bal.png',
    'CIN': 'https://a.espncdn.com/i/teamlogos/nfl/500/cin.png',
    'CLE': 'https://a.espncdn.com/i/teamlogos/nfl/500/cle.png',
    'PIT': 'https://a.espncdn.com/i/teamlogos/nfl/500/pit.png',
    
    # AFC South
    'HOU': 'https://a.espncdn.com/i/teamlogos/nfl/500/hou.png',
    'IND': 'https://a.espncdn.com/i/teamlogos/nfl/500/ind.png',
    'JAX': 'https://a.espncdn.com/i/teamlogos/nfl/500/jax.png',
    'TEN': 'https://a.espncdn.com/i/teamlogos/nfl/500/ten.png',
    
    # AFC West
    'DEN': 'https://a.espncdn.com/i/teamlogos/nfl/500/den.png',
    'KC': 'https://a.espncdn.com/i/teamlogos/nfl/500/kc.png',
    'LV': 'https://a.espncdn.com/i/teamlogos/nfl/500/lv.png',
    'LAC': 'https://a.espncdn.com/i/teamlogos/nfl/500/lac.png',
    
    # NFC East
    'DAL': 'https://a.espncdn.com/i/teamlogos/nfl/500/dal.png',
    'NYG': 'https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png',
    'PHI': 'https://a.espncdn.com/i/teamlogos/nfl/500/phi.png',
    'WAS': 'https://a.espncdn.com/i/teamlogos/nfl/500/was.png',
    
    # NFC North
    'CHI': 'https://a.espncdn.com/i/teamlogos/nfl/500/chi.png',
    'DET': 'https://a.espncdn.com/i/teamlogos/nfl/500/det.png',
    'GB': 'https://a.espncdn.com/i/teamlogos/nfl/500/gb.png',
    'MIN': 'https://a.espncdn.com/i/teamlogos/nfl/500/min.png',
    
    # NFC South
    'ATL': 'https://a.espncdn.com/i/teamlogos/nfl/500/atl.png',
    'CAR': 'https://a.espncdn.com/i/teamlogos/nfl/500/car.png',
    'NO': 'https://a.espncdn.com/i/teamlogos/nfl/500/no.png',
    'TB': 'https://a.espncdn.com/i/teamlogos/nfl/500/tb.png',
    
    # NFC West
    'ARI': 'https://a.espncdn.com/i/teamlogos/nfl/500/ari.png',
    'LAR': 'https://a.espncdn.com/i/teamlogos/nfl/500/lar.png',
    'SF': 'https://a.espncdn.com/i/teamlogos/nfl/500/sf.png',
    'SEA': 'https://a.espncdn.com/i/teamlogos/nfl/500/sea.png',
}

# Alternative hochqualitative Logo-URLs (Fallback)
NFL_TEAM_LOGOS_ALT = {
    # AFC East
    'BUF': 'https://logos-world.net/wp-content/uploads/2020/05/Buffalo-Bills-Logo.png',
    'MIA': 'https://logos-world.net/wp-content/uploads/2020/05/Miami-Dolphins-Logo.png',
    'NE': 'https://logos-world.net/wp-content/uploads/2020/05/New-England-Patriots-Logo.png',
    'NYJ': 'https://logos-world.net/wp-content/uploads/2020/05/New-York-Jets-Logo.png',
    
    # AFC North
    'BAL': 'https://logos-world.net/wp-content/uploads/2020/05/Baltimore-Ravens-Logo.png',
    'CIN': 'https://logos-world.net/wp-content/uploads/2020/05/Cincinnati-Bengals-Logo.png',
    'CLE': 'https://logos-world.net/wp-content/uploads/2020/05/Cleveland-Browns-Logo.png',
    'PIT': 'https://logos-world.net/wp-content/uploads/2020/05/Pittsburgh-Steelers-Logo.png',
    
    # AFC South
    'HOU': 'https://logos-world.net/wp-content/uploads/2020/05/Houston-Texans-Logo.png',
    'IND': 'https://logos-world.net/wp-content/uploads/2020/05/Indianapolis-Colts-Logo.png',
    'JAX': 'https://logos-world.net/wp-content/uploads/2020/05/Jacksonville-Jaguars-Logo.png',
    'TEN': 'https://logos-world.net/wp-content/uploads/2020/05/Tennessee-Titans-Logo.png',
    
    # AFC West
    'DEN': 'https://logos-world.net/wp-content/uploads/2020/05/Denver-Broncos-Logo.png',
    'KC': 'https://logos-world.net/wp-content/uploads/2020/05/Kansas-City-Chiefs-Logo.png',
    'LV': 'https://logos-world.net/wp-content/uploads/2020/05/Las-Vegas-Raiders-Logo.png',
    'LAC': 'https://logos-world.net/wp-content/uploads/2020/05/Los-Angeles-Chargers-Logo.png',
    
    # NFC East
    'DAL': 'https://logos-world.net/wp-content/uploads/2020/05/Dallas-Cowboys-Logo.png',
    'NYG': 'https://logos-world.net/wp-content/uploads/2020/05/New-York-Giants-Logo.png',
    'PHI': 'https://logos-world.net/wp-content/uploads/2020/05/Philadelphia-Eagles-Logo.png',
    'WAS': 'https://logos-world.net/wp-content/uploads/2020/05/Washington-Commanders-Logo.png',
    
    # NFC North
    'CHI': 'https://logos-world.net/wp-content/uploads/2020/05/Chicago-Bears-Logo.png',
    'DET': 'https://logos-world.net/wp-content/uploads/2020/05/Detroit-Lions-Logo.png',
    'GB': 'https://logos-world.net/wp-content/uploads/2020/05/Green-Bay-Packers-Logo.png',
    'MIN': 'https://logos-world.net/wp-content/uploads/2020/05/Minnesota-Vikings-Logo.png',
    
    # NFC South
    'ATL': 'https://logos-world.net/wp-content/uploads/2020/05/Atlanta-Falcons-Logo.png',
    'CAR': 'https://logos-world.net/wp-content/uploads/2020/05/Carolina-Panthers-Logo.png',
    'NO': 'https://logos-world.net/wp-content/uploads/2020/05/New-Orleans-Saints-Logo.png',
    'TB': 'https://logos-world.net/wp-content/uploads/2020/05/Tampa-Bay-Buccaneers-Logo.png',
    
    # NFC West
    'ARI': 'https://logos-world.net/wp-content/uploads/2020/05/Arizona-Cardinals-Logo.png',
    'LAR': 'https://logos-world.net/wp-content/uploads/2020/05/Los-Angeles-Rams-Logo.png',
    'SF': 'https://logos-world.net/wp-content/uploads/2020/05/San-Francisco-49ers-Logo.png',
    'SEA': 'https://logos-world.net/wp-content/uploads/2020/05/Seattle-Seahawks-Logo.png',
}

def get_team_logo_url(team_abbreviation: str, use_alt: bool = False) -> str:
    """
    Holt die Logo-URL für ein NFL Team
    
    Args:
        team_abbreviation: Team-Abkürzung (z.B. 'KC', 'SF')
        use_alt: Verwende alternative Logo-URLs
        
    Returns:
        str: Logo-URL
    """
    logo_dict = NFL_TEAM_LOGOS_ALT if use_alt else NFL_TEAM_LOGOS
    return logo_dict.get(team_abbreviation.upper(), '')

def update_team_logos_in_database():
    """
    Aktualisiert alle Team-Logos in der Datenbank
    """
    try:
        from app import app, db, Team
        
        with app.app_context():
            teams = Team.query.all()
            
            for team in teams:
                logo_url = get_team_logo_url(team.abbreviation)
                if logo_url and team.logo_url != logo_url:
                    team.logo_url = logo_url
                    print(f"✅ Updated logo for {team.name}: {logo_url}")
            
            db.session.commit()
            print("✅ All team logos updated successfully!")
            
    except Exception as e:
        print(f"❌ Error updating team logos: {e}")

if __name__ == '__main__':
    # Test Logo-URLs
    print("Testing NFL Team Logo URLs:")
    for abbr, url in list(NFL_TEAM_LOGOS.items())[:5]:
        print(f"{abbr}: {url}")
    
    # Update database
    update_team_logos_in_database()

