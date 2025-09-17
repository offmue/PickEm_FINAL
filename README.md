# NFL PickEm 2025/2026

🏈 **Complete NFL Pick'Em Application with Real Data Integration**

## Features

✅ **Login-Protected System** - Individual user accounts  
✅ **Real NFL Data** - ESPN API integration  
✅ **Vienna Timezone** - All times displayed in CEST/CET  
✅ **Team Usage Tracking** - Max 2x winner, 1x loser per team  
✅ **Historical Data** - Weeks 1-2 with real results  
✅ **Responsive Design** - Works on desktop and mobile  
✅ **Database Safety** - No duplicate picks, transactional updates  

## User Accounts

- **Manuel** / Manuel1
- **Daniel** / Daniel1  
- **Raff** / Raff1
- **Haunschi** / Haunschi1

## Deployment

### Render.com (Recommended)

1. Upload this repository to GitHub
2. Connect to Render.com
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python app_launcher.py`
5. Deploy!

### Local Development

```bash
pip install -r requirements.txt
python app.py
```

## Database Initialization

The app automatically initializes with:
- 32 NFL teams
- 4 user accounts  
- Historical games for weeks 1-2
- Test games for week 3

## Technical Details

- **Backend**: Flask + SQLAlchemy
- **Frontend**: Vanilla JavaScript + CSS
- **Database**: SQLite (auto-created)
- **Timezone**: Vienna (CEST/CET)
- **Python**: 3.11.9

## Created: 2025-09-17 16:18:49

🎉 **Ready for deployment!**
