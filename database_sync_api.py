"""
NFL PickEm Database Sync API
Provides endpoints for real-time database synchronization
"""

import sqlite3
import json
import os
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file
import tempfile
import zipfile

# Create blueprint for database sync
db_sync_bp = Blueprint('db_sync', __name__)

def get_database_path():
    """Get the database path dynamically"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'instance', 'nfl_pickem.db')

@db_sync_bp.route('/api/database/export', methods=['GET'])
def export_database():
    """Export complete database as JSON"""
    try:
        db_path = get_database_path()
        
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 404
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Export all tables
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if table_name == 'sqlite_sequence':
                continue
                
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            export_data['tables'][table_name] = []
            for row in rows:
                export_data['tables'][table_name].append(dict(row))
        
        conn.close()
        
        return jsonify(export_data)
        
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@db_sync_bp.route('/api/database/download', methods=['GET'])
def download_database():
    """Download the database file directly"""
    try:
        db_path = get_database_path()
        
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 404
        
        return send_file(
            db_path,
            as_attachment=True,
            download_name=f'nfl_pickem_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db',
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@db_sync_bp.route('/api/database/backup', methods=['GET'])
def create_backup_package():
    """Create a complete backup package with database and key files"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = get_database_path()
        
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 404
        
        # Create temporary zip file
        temp_dir = tempfile.mkdtemp()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(temp_dir, f'nfl_pickem_backup_{timestamp}.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add database
            zipf.write(db_path, 'nfl_pickem.db')
            
            # Add key configuration files
            key_files = [
                'app.py',
                'requirements.txt',
                'static/app.js',
                'static/styles.css',
                'templates/index.html' if os.path.exists(os.path.join(current_dir, 'templates/index.html')) else None
            ]
            
            for file_path in key_files:
                if file_path and os.path.exists(os.path.join(current_dir, file_path)):
                    zipf.write(os.path.join(current_dir, file_path), file_path)
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f'nfl_pickem_backup_{timestamp}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': f'Backup creation failed: {str(e)}'}), 500

@db_sync_bp.route('/api/database/status', methods=['GET'])
def database_status():
    """Get database status and statistics"""
    try:
        db_path = get_database_path()
        
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 404
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get statistics
        stats = {}
        
        # Count records in each table
        tables = ['user', 'team', 'match', 'pick', 'eliminated_team', 'team_winner_usage']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            except:
                stats[f'{table}_count'] = 0
        
        # Get current week info
        cursor.execute("SELECT MAX(week) FROM match")
        max_week = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(DISTINCT week) FROM match")
        weeks_available = cursor.fetchone()[0] or 0
        
        # Get recent picks
        cursor.execute("""
            SELECT COUNT(*) FROM pick p
            JOIN match m ON p.match_id = m.id
            WHERE m.week = (SELECT MAX(week) FROM match WHERE week <= ?)
        """, (max_week,))
        current_week_picks = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database_path': db_path,
            'last_modified': datetime.fromtimestamp(os.path.getmtime(db_path)).isoformat(),
            'file_size_mb': round(os.path.getsize(db_path) / (1024 * 1024), 2),
            'statistics': stats,
            'current_week': max_week,
            'weeks_available': weeks_available,
            'current_week_picks': current_week_picks,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

@db_sync_bp.route('/api/database/picks/summary', methods=['GET'])
def picks_summary():
    """Get a summary of all picks by week and user"""
    try:
        db_path = get_database_path()
        
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 404
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get picks summary
        cursor.execute("""
            SELECT 
                m.week,
                u.username,
                t.name as chosen_team,
                m.id as match_id,
                at.name as away_team,
                ht.name as home_team,
                m.start_time
            FROM pick p
            JOIN user u ON p.user_id = u.id
            JOIN match m ON p.match_id = m.id
            JOIN team t ON p.chosen_team_id = t.id
            JOIN team at ON m.away_team_id = at.id
            JOIN team ht ON m.home_team_id = ht.id
            ORDER BY m.week, u.username
        """)
        
        picks = cursor.fetchall()
        
        # Organize by week
        picks_by_week = {}
        for pick in picks:
            week = pick['week']
            if week not in picks_by_week:
                picks_by_week[week] = []
            
            picks_by_week[week].append({
                'username': pick['username'],
                'chosen_team': pick['chosen_team'],
                'match': f"{pick['away_team']} @ {pick['home_team']}",
                'match_id': pick['match_id'],
                'start_time': pick['start_time']
            })
        
        conn.close()
        
        return jsonify({
            'picks_by_week': picks_by_week,
            'total_picks': len(picks),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Picks summary failed: {str(e)}'}), 500

# Helper function to register the blueprint
def register_database_sync_api(app):
    """Register the database sync API with the Flask app"""
    app.register_blueprint(db_sync_bp)
    return db_sync_bp

