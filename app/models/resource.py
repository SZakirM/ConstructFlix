# app/models/resource.py
from datetime import datetime
from app import db


class Resource(db.Model):
    """Complete resource management system"""
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # Basic info
    name = db.Column(db.String(200), nullable=False)
    resource_type = db.Column(db.String(50))  # labor, equipment, material, tool
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(50))
    
    # Identification
    code = db.Column(db.String(50), unique=True)
    manufacturer = db.Column(db.String(100))
    model = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    
    # Quantity tracking
    total_quantity = db.Column(db.Float, default=0)
    available_quantity = db.Column(db.Float, default=0)
    allocated_quantity = db.Column(db.Float, default=0)
    used_quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20))  # hours, pieces, tons, each
    
    # Cost tracking
    cost_per_unit = db.Column(db.Numeric(15, 2))
    total_cost = db.Column(db.Numeric(15, 2))
    currency = db.Column(db.String(3), default='USD')
    
    # Supplier info
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    supplier_sku = db.Column(db.String(100))
    supplier_price = db.Column(db.Numeric(15, 2))
    
    # Status
    status = db.Column(db.String(50), default='available')  # available, reserved, in_use, maintenance, depleted
    condition = db.Column(db.String(50), default='new')  # new, good, fair, poor
    location = db.Column(db.String(200))
    
    # Dates
    expected_delivery = db.Column(db.Date)
    actual_delivery = db.Column(db.Date)
    expected_return = db.Column(db.Date)
    actual_return = db.Column(db.Date)
    
    # Maintenance (for equipment)
    last_maintenance = db.Column(db.Date)
    next_maintenance = db.Column(db.Date)
    maintenance_interval = db.Column(db.Integer)  # days
    
    # Documents and notes
    notes = db.Column(db.Text)
    specifications = db.Column(db.JSON)
    documents = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='resources_list')
    supplier = db.relationship('Supplier', backref='resources')
    calendar = db.relationship('ResourceCalendar', backref='resource', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def utilization_rate(self):
        """Calculate current utilization rate"""
        if self.total_quantity > 0:
            return (self.used_quantity / self.total_quantity) * 100
        return 0
    
    @property
    def is_available(self):
        """Check if resource is available for allocation"""
        return self.available_quantity > 0
    
    def allocate(self, quantity):
        """Allocate resource quantity"""
        if quantity <= self.available_quantity:
            self.available_quantity -= quantity
            self.allocated_quantity += quantity
            db.session.commit()
            return True
        return False
    
    def release(self, quantity):
        """Release allocated resource"""
        if quantity <= self.allocated_quantity:
            self.available_quantity += quantity
            self.allocated_quantity -= quantity
            db.session.commit()
            return True
        return False
    
    def use(self, quantity):
        """Mark resource as used"""
        if quantity <= self.allocated_quantity:
            self.allocated_quantity -= quantity
            self.used_quantity += quantity
            db.session.commit()
            return True
        return False
    
    def check_availability(self, start_date, end_date):
        """Check resource availability for date range"""
        calendar_entries = self.calendar.filter(
            ResourceCalendar.date.between(start_date, end_date)
        ).all()
        
        for entry in calendar_entries:
            if entry.booked_quantity >= self.total_quantity:
                return False
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.resource_type,
            'category': self.category,
            'total_quantity': self.total_quantity,
            'available': self.available_quantity,
            'allocated': self.allocated_quantity,
            'used': self.used_quantity,
            'unit': self.unit,
            'status': self.status,
            'utilization': self.utilization_rate,
            'supplier': self.supplier.name if self.supplier else None
        }


class ResourceCalendar(db.Model):
    """Daily resource availability calendar"""
    __tablename__ = 'resource_calendars'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    
    date = db.Column(db.Date, nullable=False)
    available_quantity = db.Column(db.Float, default=0)
    booked_quantity = db.Column(db.Float, default=0)
    
    # Status for this day
    is_available = db.Column(db.Boolean, default=True)
    reason = db.Column(db.String(200))  # maintenance, holiday, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('resource_id', 'date', name='unique_resource_date'),)


class Supplier(db.Model):
    """Supplier/vendor management"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), unique=True)
    
    # Contact
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    
    # Business
    tax_id = db.Column(db.String(50))
    payment_terms = db.Column(db.String(100))
    rating = db.Column(db.Float)  # 1-5
    notes = db.Column(db.Text)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(100))  # preferred, approved, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'rating': self.rating,
            'is_active': self.is_active
        }

