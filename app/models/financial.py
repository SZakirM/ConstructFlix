# app/models/financial.py
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
    
    # Budget categorization
    category = db.Column(db.String(100))  # labor, materials, equipment, subcontractor
    subcategory = db.Column(db.String(100))
    wbs_code = db.Column(db.String(50))  # Work Breakdown Structure
    
    # Budget amounts
    original_budget = db.Column(db.Numeric(15, 2), default=0)
    revised_budget = db.Column(db.Numeric(15, 2), default=0)
    committed_cost = db.Column(db.Numeric(15, 2), default=0)  # Purchase orders, contracts
    actual_cost = db.Column(db.Numeric(15, 2), default=0)
    forecast_cost = db.Column(db.Numeric(15, 2), default=0)  # Estimated final
    
    # Variance
    variance = db.Column(db.Numeric(15, 2), default=0)
    variance_percentage = db.Column(db.Float, default=0)
    
    # Earned Value Management
    planned_value = db.Column(db.Numeric(15, 2), default=0)  # PV
    earned_value = db.Column(db.Numeric(15, 2), default=0)  # EV
    actual_cost_ev = db.Column(db.Numeric(15, 2), default=0)  # AC
    
    # Performance indices
    cost_performance_index = db.Column(db.Float)  # CPI
    schedule_performance_index = db.Column(db.Float)  # SPI
    
    # Estimates
    estimate_at_completion = db.Column(db.Numeric(15, 2))  # EAC
    estimate_to_complete = db.Column(db.Numeric(15, 2))  # ETC
    variance_at_completion = db.Column(db.Numeric(15, 2))  # VAC
    
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='budgets')
    transactions = db.relationship('BudgetTransaction', backref='budget', lazy='dynamic', cascade='all, delete-orphan')
    
    def calculate_earned_value(self):
        """Calculate EVM metrics"""
        total_budget = float(self.revised_budget or self.original_budget)
        if total_budget == 0:
            return
        
        # Get tasks for this budget category
        tasks = Task.query.filter_by(project_id=self.project_id).all()
        
        # Calculate Planned Value (based on schedule)
        total_duration = 0
        completed_planned = 0
        
        for task in tasks:
            if task.start_date and task.end_date:
                duration = (task.end_date - task.start_date).days
                total_duration += duration
                
                task_budget = total_budget / len(tasks)
                
                if task.start_date <= date.today() <= task.end_date:
                    # Task in progress
                    days_passed = (date.today() - task.start_date).days
                    completed_planned += (days_passed / duration) * task_budget
                elif task.end_date < date.today():
                    # Task should be complete
                    completed_planned += task_budget
        
        self.planned_value = completed_planned
        
        # Calculate Earned Value (based on actual progress)
        earned = 0
        for task in tasks:
            task_budget = total_budget / len(tasks)
            earned += (task.progress / 100) * task_budget
        
        self.earned_value = earned
        self.actual_cost_ev = float(self.actual_cost)
        
        # Calculate indices
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
        
        return {
            'cpi': float(self.cost_performance_index) if self.cost_performance_index else None,
            'spi': float(self.schedule_performance_index) if self.schedule_performance_index else None,
            'eac': float(self.estimate_at_completion) if self.estimate_at_completion else None,
            'vac': float(self.variance_at_completion) if self.variance_at_completion else None
        }
    
    def add_transaction(self, transaction_type, amount, description, reference=None):
        """Add budget transaction"""
        transaction = BudgetTransaction(
            budget_id=self.id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            reference=reference
        )
        db.session.add(transaction)
        
        # Update budget totals
        if transaction_type == 'commitment':
            self.committed_cost = db.func.coalesce(self.committed_cost, 0) + amount
        elif transaction_type == 'actual':
            self.actual_cost = db.func.coalesce(self.actual_cost, 0) + amount
        
        # Recalculate variance
        self.variance = float(self.revised_budget or self.original_budget) - float(self.actual_cost)
        if float(self.revised_budget or self.original_budget) > 0:
            self.variance_percentage = (self.variance / float(self.revised_budget or self.original_budget)) * 100
        
        db.session.commit()
        return transaction


class BudgetTransaction(db.Model):
    """Individual budget transactions"""
    __tablename__ = 'budget_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)
    
    transaction_type = db.Column(db.String(50))  # commitment, actual, adjustment
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.String(500))
    
    # Reference (purchase order, invoice, etc.)
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.Integer)
    reference_number = db.Column(db.String(100))
    
    transaction_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Approval
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_date = db.Column(db.DateTime)
    approval_status = db.Column(db.String(50), default='pending')
    
    # Attachments
    attachments = db.Column(db.JSON)
    
    approver = db.relationship('User', foreign_keys=[approved_by])


class PurchaseOrder(db.Model):
    """Purchase order management"""
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'))
    
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
    paid_amount = db.Column(db.Numeric(15, 2), default=0)
    
    # Approval
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_date = db.Column(db.DateTime)
    
    # Line items (JSON for flexibility)
    line_items = db.Column(db.JSON)
    
    # Attachments
    attachments = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='purchase_orders')
    supplier = db.relationship('Supplier', backref='purchase_orders')
    budget = db.relationship('Budget', backref='purchase_orders')
    requester = db.relationship('User', foreign_keys=[requested_by])
    approver_user = db.relationship('User', foreign_keys=[approved_by])
    
    def approve(self, user_id):
        """Approve purchase order"""
        self.status = 'approved'
        self.approved_by = user_id
        self.approved_date = datetime.utcnow()
        db.session.commit()
        
        # Create budget commitment
        if self.budget_id and self.total:
            budget = Budget.query.get(self.budget_id)
            budget.add_transaction(
                transaction_type='commitment',
                amount=self.total,
                description=f"PO: {self.po_number} - {self.title}",
                reference={'type': 'purchase_order', 'id': self.id}
            )
    
    def receive(self, receiving_report):
        """Mark items as received"""
        self.status = 'partial' if receiving_report.get('partial') else 'complete'
        self.actual_delivery = date.today()
        
        # Update line items with received quantities
        if self.line_items:
            for item in self.line_items:
                if item.get('id') == receiving_report.get('item_id'):
                    item['received_quantity'] = receiving_report.get('quantity')
                    item['received_date'] = date.today().isoformat()
        
        db.session.commit()
        
        # Create actual cost transaction
        if receiving_report.get('invoice_amount'):
            budget = Budget.query.get(self.budget_id)
            budget.add_transaction(
                transaction_type='actual',
                amount=receiving_report['invoice_amount'],
                description=f"Invoice for PO: {self.po_number}",
                reference={'type': 'purchase_order', 'id': self.id}
            )
    
    def to_dict(self):
        return {
            'id': self.id,
            'po_number': self.po_number,
            'title': self.title,
            'supplier': self.supplier.name if self.supplier else None,
            'total': float(self.total) if self.total else 0,
            'status': self.status,
            'order_date': self.order_date.isoformat(),
            'expected_delivery': self.expected_delivery.isoformat() if self.expected_delivery else None,
            'payment_status': self.payment_status
        }