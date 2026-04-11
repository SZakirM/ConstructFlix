from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm, ForgotPasswordForm
from datetime import datetime
import secrets
from flask import Blueprint
from app import limiter


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # 5 attempts per minute
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.first_name}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")  # 3 registrations per hour per IP
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=str(form.username.data),  # type: ignore
            email=str(form.email.data).lower(),  # type: ignore
            first_name=str(form.first_name.data),  # type: ignore
            last_name=str(form.last_name.data),  # type: ignore
            company=str(form.company.data) if form.company.data else None,  # type: ignore
            role='team_member'
        )
        user.set_password(str(form.password.data))  # type: ignore
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please sign in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()

    response = redirect(url_for('auth.login'))
    remember_cookie = current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')
    response.delete_cookie(remember_cookie)

    flash('You have been signed out.', 'info')
    return response

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")  # 3 password reset requests per hour
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            db.session.commit()
            # Send email (implement email sending here)
            flash('Password reset instructions have been sent to your email.', 'info')
        else:
            flash('If your email is registered, you will receive reset instructions.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)
