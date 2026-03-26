# TODO.md - Construction Scheduler Fixes

## Previous Fixes (Completed)
- [x] Read key model files
- [x] Implement missing model methods
- [x] Fix model imports
- [x] Fix service imports
- [x] Update routes
- [ ] Run tests
- [ ] Lint & type check
- [ ] Test run.py

## NEW: Fix 'schedule - task not create' Bug

### 1. Add permission checks to task creation APIs [x]
- Files: `app/routes/api.py`, `app/routes/tasks.py`
- Verify `project.created_by == current_user.id`

### 2. Remove duplicate create_task endpoint [x]
- File: `app/routes/tasks.py` - removed

### 3. Add 'Add Task' UI to project_detail.html [x]
- Button + modal form added

### 4. Create task creation JavaScript [x]
- Inline JS in project_detail.html
- POST to `/api/projects/<id>/tasks`

### 5. Add error handling/logging to endpoints [x]
- Try/catch, validation, rollback in api.py

### 6. Test task creation
- [ ] `python run_tests.py`
- [ ] Manual test: create project -> add task -> view schedule

### 7. Lint and restart
- [ ] `black .`
- [ ] `mypy .`
- [ ] `python run.py`

**Legend:** [ ] TODO  [x] DONE
