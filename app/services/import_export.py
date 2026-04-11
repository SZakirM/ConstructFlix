# app/services/import_export.py
import csv
import json
import pandas as pd
from io import StringIO, BytesIO
from datetime import datetime
from app import db
from app.models.task import Task, Milestone
from app.models.project import Project
from app.models.resource import Resource

class ImportExportService:
    """Data import/export in multiple formats"""
    
    @staticmethod
    def export_to_csv(project_id, data_type='tasks'):
        """Export project data to CSV"""
        if data_type == 'tasks':
            tasks = Task.query.filter_by(project_id=project_id).all()
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['ID', 'Name', 'Description', 'Start Date', 'End Date', 
                           'Progress', 'Status', 'Priority', 'Assignee', 'Cost Estimate'])
            
            # Write data
            for task in tasks:
                writer.writerow([
                    task.id,
                    task.name,
                    task.description,
                    task.start_date.isoformat(),
                    task.end_date.isoformat(),
                    task.progress,
                    task.status,
                    task.priority,
                    task.assignee.full_name if task.assignee else '',
                    float(task.cost_estimate) if task.cost_estimate else ''
                ])
            
            return output.getvalue()
        
        elif data_type == 'resources':
            resources = Resource.query.filter_by(project_id=project_id).all()
            
            output = StringIO()
            writer = csv.writer(output)
            
            writer.writerow(['ID', 'Name', 'Type', 'Total Quantity', 'Available', 
                           'Unit', 'Cost Per Unit', 'Supplier'])
            
            for resource in resources:
                writer.writerow([
                    resource.id,
                    resource.name,
                    resource.resource_type,
                    resource.total_quantity,
                    resource.available_quantity,
                    resource.unit,
                    float(resource.cost_per_unit) if resource.cost_per_unit else '',
                    resource.supplier.name if resource.supplier else ''
                ])
            
            return output.getvalue()
    
    @staticmethod
    def export_to_excel(project_id):
        """Export complete project to Excel"""
        # Get all data
        project = Project.query.get(project_id)
        tasks = Task.query.filter_by(project_id=project_id).all()
        resources = Resource.query.filter_by(project_id=project_id).all()
        milestones = Milestone.query.filter_by(project_id=project_id).all()
        
        # Create Excel file
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Project info
            project_df = pd.DataFrame([{
                'Name': project.name,
                'Description': project.description,
                'Start Date': project.start_date,
                'End Date': project.end_date,
                'Status': project.status,
                'Progress': project.progress,
                'Budget': float(project.budget) if project.budget else None,
                'Actual Cost': float(project.actual_cost) if project.actual_cost else None
            }])
            project_df.to_excel(writer, sheet_name='Project', index=False)
            
            # Tasks
            if tasks:
                tasks_df = pd.DataFrame([{
                    'ID': t.id,
                    'Name': t.name,
                    'Start Date': t.start_date,
                    'End Date': t.end_date,
                    'Progress': t.progress,
                    'Status': t.status,
                    'Priority': t.priority,
                    'Assignee': t.assignee.full_name if t.assignee else '',
                    'Cost Estimate': float(t.cost_estimate) if t.cost_estimate else None
                } for t in tasks])
                tasks_df.to_excel(writer, sheet_name='Tasks', index=False)
            
            # Resources
            if resources:
                resources_df = pd.DataFrame([{
                    'Name': r.name,
                    'Type': r.resource_type,
                    'Total Quantity': r.total_quantity,
                    'Available': r.available_quantity,
                    'Unit': r.unit,
                    'Cost Per Unit': float(r.cost_per_unit) if r.cost_per_unit else None,
                    'Supplier': r.supplier.name if r.supplier else ''
                } for r in resources])
                resources_df.to_excel(writer, sheet_name='Resources', index=False)
            
            # Milestones
            if milestones:
                milestones_df = pd.DataFrame([{
                    'Name': m.name,
                    'Due Date': m.due_date,
                    'Status': m.status,
                    'Completed Date': m.completed_date
                } for m in milestones])
                milestones_df.to_excel(writer, sheet_name='Milestones', index=False)
        
        output.seek(0)
        return output
    
    @staticmethod
    def export_to_json(project_id):
        """Export project to JSON"""
        project = Project.query.get(project_id)
        
        data = {
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'start_date': project.start_date.isoformat(),
                'end_date': project.end_date.isoformat(),
                'status': project.status,
                'progress': project.progress,
                'budget': float(project.budget) if project.budget else None,
                'actual_cost': float(project.actual_cost) if project.actual_cost else None
            },
            'tasks': [],
            'resources': [],
            'milestones': []
        }
        
        # Add tasks
        for task in project.tasks:
            data['tasks'].append({
                'id': task.id,
                'name': task.name,
                'start_date': task.start_date.isoformat(),
                'end_date': task.end_date.isoformat(),
                'progress': task.progress,
                'status': task.status,
                'assignee': task.assignee.email if task.assignee else None,
                'dependencies': [d.depends_on_id for d in task.dependencies_from]
            })
        
        # Add resources
        for resource in project.resources_list:
            data['resources'].append({
                'id': resource.id,
                'name': resource.name,
                'type': resource.resource_type,
                'quantity': resource.total_quantity,
                'unit': resource.unit
            })
        
        # Add milestones
        for milestone in project.milestones:
            data['milestones'].append({
                'id': milestone.id,
                'name': milestone.name,
                'due_date': milestone.due_date.isoformat(),
                'status': milestone.status
            })
        
        return json.dumps(data, indent=2)
    
    @staticmethod
    def import_from_csv(file_content, project_id, data_type='tasks'):
        """Import data from CSV"""
        import csv
        from io import StringIO
        
        reader = csv.DictReader(StringIO(file_content))
        
        if data_type == 'tasks':
            imported_count = 0
            for row in reader:
                if not row.get('Name'):
                    continue
                task = Task(
                    project_id=project_id,
                    name=row['Name'],
                    description=row.get('Description', ''),
                    start_date=datetime.strptime(row['Start Date'], '%Y-%m-%d').date(),
                    end_date=datetime.strptime(row['End Date'], '%Y-%m-%d').date(),
                    progress=float(row.get('Progress', 0)),
                    status=row.get('Status', 'not_started'),
                    priority=row.get('Priority', 'medium')
                )
                db.session.add(task)
                imported_count += 1
            
            db.session.commit()
            return imported_count
        
        return 0

    @staticmethod
    def import_from_excel(file_content, project_id, data_type='tasks'):
        """Import data from Excel"""
        from io import BytesIO

        if data_type != 'tasks':
            return 0

        excel_buffer = BytesIO(file_content)
        try:
            xls = pd.ExcelFile(excel_buffer)
        except Exception as e:
            raise ValueError('Unable to parse Excel file: ' + str(e))

        sheet_name = 'Tasks' if 'Tasks' in xls.sheet_names else xls.sheet_names[0]
        excel_buffer.seek(0)
        df = pd.read_excel(excel_buffer, sheet_name=sheet_name)

        imported_count = 0
        for _, row in df.iterrows():
            name = row.get('Name') if 'Name' in row else row.get('name')
            if not name or (isinstance(name, str) and not name.strip()):
                continue

            start_date_raw = row.get('Start Date') if 'Start Date' in row else row.get('start_date')
            end_date_raw = row.get('End Date') if 'End Date' in row else row.get('end_date')

            task = Task(
                project_id=project_id,
                name=str(name).strip(),
                description=str(row.get('Description', '')) if row.get('Description') is not None else '',
                start_date=ImportExportService._parse_excel_date(start_date_raw),
                end_date=ImportExportService._parse_excel_date(end_date_raw),
                progress=float(row.get('Progress', 0) or 0),
                status=str(row.get('Status', 'not_started') or 'not_started'),
                priority=str(row.get('Priority', 'medium') or 'medium')
            )
            db.session.add(task)
            imported_count += 1

        db.session.commit()
        return imported_count

    @staticmethod
    def _parse_excel_date(value):
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError('Missing date value')
        if isinstance(value, datetime):
            return value.date()
        try:
            parsed = pd.to_datetime(value, errors='raise')
            return parsed.date()
        except Exception as e:
            raise ValueError(f'Invalid date value: {value}')

    @staticmethod
    def import_from_primvera(file_content):
        """Import from Primavera P6 XML format"""
        # Parse Primavera XML
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(file_content)
        root = tree.getroot()
        
        # Extract project data
        projects = []
        for project_elem in root.findall('.//Project'):
            project = {
                'name': project_elem.find('Name').text,
                'id': project_elem.find('ID').text,
                'start_date': project_elem.find('StartDate').text,
                'end_date': project_elem.find('FinishDate').text
            }
            projects.append(project)
        
        return projects
    
    @staticmethod
    def import_from_ms_project(file_content):
        """Import from Microsoft Project MPX format"""
        # Parse MPX format
        lines = file_content.split('\n')
        
        tasks = []
        for line in lines:
            if line.startswith('Task'):
                parts = line.split(',')
                if len(parts) >= 5:
                    task = {
                        'id': parts[1],
                        'name': parts[2],
                        'start': parts[3],
                        'finish': parts[4]
                    }
                    tasks.append(task)
        
        return tasks