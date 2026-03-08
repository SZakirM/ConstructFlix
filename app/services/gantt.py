# app/services/gantt.py - Complete Gantt implementation
from datetime import timedelta
import json
import pandas as pd
import plotly.express as px
from app.models.task import Task
from app import db
class GanttChartService:
    """Professional Gantt chart with critical path analysis"""
    
    @staticmethod
    def generate_interactive_gantt(project_id):
        """Generate interactive Gantt chart with all features"""
        tasks = Task.query.filter_by(project_id=project_id).all()
        
        # Prepare data with all scheduling attributes
        df_data = []
        for task in tasks:
            # Calculate task metrics
            duration = (task.end_date - task.start_date).days
            progress = task.progress
            
            # Determine status colors
            if task.status == 'completed':
                color = '#28a745'
                progress_color = '#20c997'
            elif task.status == 'in_progress':
                color = '#007bff'
                progress_color = '#17a2b8'
            elif task.is_overdue:
                color = '#dc3545'
                progress_color = '#c82333'
            else:
                color = '#6c757d'
                progress_color = '#5a6268'
            
            # Get dependencies
            deps = [d.depends_on_id for d in task.dependencies]
            
            df_data.append({
                'Task': task.name,
                'Start': task.start_date,
                'Finish': task.end_date,
                'Duration': duration,
                'Progress': progress,
                'Status': task.status,
                'Assignee': task.assignee.full_name if task.assignee else 'Unassigned',
                'Priority': task.priority,
                'Color': color,
                'ProgressColor': progress_color,
                'Dependencies': deps,
                'ID': task.id,
                'ParentID': task.parent_id
            })
        
        df = pd.DataFrame(df_data)
        
        # Create main Gantt chart
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Status",
            hover_data=["Assignee", "Progress", "Priority"],
            title=f"Project Schedule - Gantt Chart",
            color_discrete_map={
                'completed': '#28a745',
                'in_progress': '#007bff',
                'delayed': '#dc3545',
                'not_started': '#6c757d'
            }
        )
        
        # Add progress bars
        for idx, row in df.iterrows():
            if row['Progress'] > 0:
                progress_end = row['Start'] + timedelta(days=row['Duration'] * row['Progress'] / 100)
                fig.add_shape(
                    type="line",
                    x0=row['Start'],
                    y0=idx,
                    x1=progress_end,
                    y1=idx,
                    line=dict(color=row['ProgressColor'], width=8)
                )
        
        # Calculate and highlight critical path
        critical_path = GanttChartService.calculate_critical_path(tasks)
        
        # Highlight critical path tasks
        for task_id in critical_path:
            task_idx = df[df['ID'] == task_id].index[0]
            fig.add_annotation(
                x=df.loc[task_idx, 'Start'],
                y=task_idx,
                text="⚠️ Critical",
                showarrow=True,
                arrowhead=1,
                ax=20,
                ay=-20
            )
        
        # Add dependency lines
        for _, row in df.iterrows():
            for dep_id in row['Dependencies']:
                if dep_id in df['ID'].values:
                    dep_idx = df[df['ID'] == dep_id].index[0]
                    fig.add_annotation(
                        x=df.loc[dep_idx, 'Finish'],
                        y=dep_idx,
                        xref="x",
                        yref="y",
                        ax=row['Start'],
                        ay=idx,
                        xanchor="center",
                        yanchor="middle",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=1,
                        arrowcolor="#888"
                    )
        
        # Professional formatting
        fig.update_layout(
            plot_bgcolor='#1f1f1f',
            paper_bgcolor='#1f1f1f',
            font_color='#fff',
            title_font_color='#fff',
            xaxis=dict(
                showgrid=True,
                gridcolor='#333',
                tickfont_color='#fff',
                title="Timeline"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#333',
                tickfont_color='#fff',
                title="Tasks"
            ),
            height=max(400, len(df_data) * 35),
            margin=dict(l=150, r=50, t=50, b=50),
            hoverlabel=dict(bgcolor="#333", font_size=12)
        )
        
        return json.loads(fig.to_json())