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
    chart_json = GanttChartService.create_gantt_chart(project_id)
    if chart_json:
        return jsonify({'chart': json.loads(chart_json)})
    return jsonify({'error': 'No data available'}), 404

@gantt_bp.route('/api/project/<int:project_id>/critical-path')
@login_required
def critical_path(project_id):
    """Get critical path data"""
    critical_path = GanttChartService.get_critical_path(project_id)
    return jsonify({'critical_path': critical_path})