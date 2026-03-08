# Pylance Diagnostics Fix Plan

## Summary of Issues Found

### 1. Missing Imports (reportUndefinedVariable)
- `app/models/budget.py`: Uses `Task` without importing
- `app/models/financial.py`: Uses `Task` without importing  
- `app/services/gantt.py`: Uses `Task`, `pd`, `px`, `timedelta`, `json` without imports
- `app/services/import_export.py`: Uses `Task`, `Resource`, `Project`, `Milestone` without imports
- `app/services/notification_service.py`: Uses `current_user` without import

### 2. Missing Model Definitions (reportMissingImports)
- `app/services/notification.py`: Imports `app.models.comment` and `app.models.message` which don't exist

### 3. Missing Model Methods/Properties
- `Task` model: Missing `assignee` property, `add_dependency` method
- `Project` model: Missing `to_dict` method
- `Task` model in `routes/api.py`: Missing `to_dict` method

### 4. Flask Extension Type Issues (reportAttributeAccessIssue)
- `app/init.py`: Custom attributes on Flask app need typing

### 5. Route Issues
- `app/routes/auth.py`: Duplicate function definitions (login, register, forgot_password)
- `app/routes/admin.py`: Raw SQL without text() wrapper, missing psutil import
- `app/routes/api.py`: Using methods that don't exist
- `app/routes/gantt.py`: Using methods that don't exist on GanttChartService
- `app/routes/main.py`: Using methods that don't exist on Project
- `app/routes/tasks.py`: Using methods that don't exist on Task

### 6. Scheduling Model Issues
- `app/models/scheduling.py`: `dep` possibly unbound

### 7. Notification Model Issues
- `app/models/notification.py`: The `send_to_user` method parameters don't match service expectations

## Fix Priority
1. First: Fix missing imports in models
2. Second: Fix missing methods on models
3. Third: Fix service files with missing imports
4. Fourth: Fix route files
5. Fifth: Fix Flask app typing issues

