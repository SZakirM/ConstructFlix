# app/models/budget.py
from datetime import datetime, date
from app import db
from app.models.task import Task
class Budget(db.Model):
    """Complete project budget management"""
    __tablename__ = 'budgets'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    version = db.Column(db.String(20), default='1.0')
    
    # Budget categories
    category = db.Column(db.String(100))  # labor, materials, equipment, subcontractor, etc.
    subcategory = db.Column(db.String(100))
    wbs_code = db.Column(db.String(50))  # Work Breakdown Structure code
    
    # Budget amounts
    original_budget = db.Column(db.Numeric(15, 2), default=0)
    revised_budget = db.Column(db.Numeric(15, 2), default=0)
    committed_cost = db.Column(db.Numeric(15, 2), default=0)  # Purchase orders, contracts
    actual_cost = db.Column(db.Numeric(15, 2), default=0)
    forecast_cost = db.Column(db.Numeric(15, 2), default=0)  # Estimated final cost
    
    # Variance tracking
    variance = db.Column(db.Numeric(15, 2), default=0)  # Budget vs actual
    variance_percentage = db.Column(db.Float, default=0)
    
    # Performance metrics
    earned_value = db.Column(db.Numeric(15, 2), default=0)  # EV
    planned_value = db.Column(db.Numeric(15, 2), default=0)  # PV
    actual_cost_ev = db.Column(db.Numeric(15, 2), default=0)  # AC
    
    # Earned value metrics
    cost_performance_index = db.Column(db.Float)  # CPI = EV / AC
    schedule_performance_index = db.Column(db.Float)  # SPI = EV / PV
    estimate_at_completion = db.Column(db.Numeric(15, 2))  # EAC
    estimate_to_complete = db.Column(db.Numeric(15, 2))  # ETC
    variance_at_completion = db.Column(db.Numeric(15, 2))  # VAC
    
    # Notes
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='budgets')
    transactions = db.relationship('BudgetTransaction', backref='budget', lazy='dynamic')
    
    def calculate_earned_value(self):
        """Calculate earned value metrics"""
        # Get all tasks for this budget category
        tasks = Task.query.filter_by(project_id=self.project_id).all()
        
        total_budget = float(self.revised_budget or self.original_budget)
        if total_budget == 0:
            return
        
        # Calculate planned value based on schedule
        total_planned_duration = 0
        completed_planned = 0
        
        for task in tasks:
            if task.start_date and task.end_date:
                duration = (task.end_date - task.start_date).days
                total_planned_duration += duration
                
                # Planned value based on schedule
                if task.start_date <= date.today() <= task.end_date:
                    # Task in progress - partial credit
                    days_passed = (date.today() - task.start_date).days
                    completed_planned += (days_passed / duration) * (total_budget / len(tasks))
                elif task.end_date < date.today():
                    # Task should be complete
                    completed_planned += total_budget / len(tasks)
        
        self.planned_value = completed_planned
        
        # Calculate earned value based on actual progress
        earned = 0
        for task in tasks:
            earned += (task.progress / 100) * (total_budget / len(tasks))
        
        self.earned_value = earned
        self.actual_cost_ev = float(self.actual_cost)
        
        # Calculate performance indices
        if self.actual_cost_ev > 0:
            self.cost_performance_index = self.earned_value / self.actual_cost_ev
        if self.planned_value > 0:
            self.schedule_performance_index = self.earned_value / self.planned_value
        
        # Calculate estimates
        if self.cost_performance_index and self.cost_performance_index > 0:
            self.estimate_at_completion = total_budget / self.cost_performance_index
            self.estimate_to_complete = self.estimate_at_completion - self.actual_cost_ev
            self.variance_at_completion = total_budget - self.estimate_at_completion
        
        db.session.commit()


class BudgetTransaction(db.Model):
    """Individual budget transactions"""
    __tablename__ = 'budget_transactions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)
    
    # Transaction details
    transaction_type = db.Column(db.String(50))  # commitment, actual, adjustment
    description = db.Column(db.String(500))
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    # Reference
    reference_type = db.Column(db.String(50))  # purchase_order, invoice, contract
    reference_id = db.Column(db.Integer)
    reference_number = db.Column(db.String(100))
    
    # Date
    transaction_date = db.Column(db.Date, nullable=False)
    entered_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Approval
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_date = db.Column(db.DateTime)
    approval_status = db.Column(db.String(50), default='pending')
    
    # Attachments
    attachments = db.Column(db.JSON)
    
    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by])


class PurchaseOrder(db.Model):
    """Purchase order tracking"""
    __tablename__ = 'purchase_orders'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # Amounts
    subtotal = db.Column(db.Numeric(15, 2))
    tax = db.Column(db.Numeric(15, 2))
    total = db.Column(db.Numeric(15, 2))
    currency = db.Column(db.String(3), default='USD')
    
    # Dates
    order_date = db.Column(db.Date, nullable=False)
    expected_delivery = db.Column(db.Date)
    actual_delivery = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(50), default='draft')  # draft, sent, acknowledged, partial, complete, cancelled
    
    # Payment
    payment_terms = db.Column(db.String(100))
    payment_status = db.Column(db.String(50), default='unpaid')
    
    # Approval
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_date = db.Column(db.DateTime)
    
    # Line items
    line_items = db.Column(db.JSON)
    
    # Attachments
    attachments = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)