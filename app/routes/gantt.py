# app/routes/gantt.py
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.services.gantt import GanttChartService
import json

gantt_bp = Blueprint('gantt', __name__)

@gantt_bp.route('/project/<int:project_id>/gantt')
@login_required
def gantt_view(project_id):
    """Render Gantt chart view"""
    return render_template('gantt.html', project_id=project_id)

@gantt_bp.route('/api/project/<int:project_id>/gantt/data')
@login_required
def gantt_data(project_id):
    """Get Gantt chart data as JSON"""
    chart_data = GanttChartService.generate_interactive_gantt(project_id)
    if chart_data:
        return jsonify({'chart': chart_data})
    return jsonify({'error': 'No data available'}), 404

# Temporarily disable critical path until implemented
@gantt_bp.route('/api/project/<int:project_id>/critical-path')
@login_required
def critical_path(project_id):
    """Get critical path data"""
    return jsonify({'critical_path': [], 'message': 'Critical path analysis coming soon'})
