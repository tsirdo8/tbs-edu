from flask import Flask, render_template, flash, redirect, url_for, request, send_file
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, EducationalMaterial, Comment
from ext import login_manager, csrf
from forms import LoginForm, RegistrationForm, EducationalMaterialForm, CommentForm, ContactForm
from flask_wtf import FlaskForm
import os
import secrets
from datetime import datetime
import pytz


# File upload directories
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
MATERIAL_FOLDER = os.path.join(UPLOAD_FOLDER, 'materials')
IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')

# Georgian timezone
georgian_timezone = pytz.timezone('Asia/Tbilisi')

def georgian_date(date):
    """Convert datetime to Georgian format with Georgian timezone"""
    if date.tzinfo is None:
        # If the date has no timezone info, assume it's UTC and convert to Georgian time
        date = pytz.utc.localize(date).astimezone(georgian_timezone)
    else:
        # If it has timezone info, just convert to Georgian time
        date = date.astimezone(georgian_timezone)
        
    georgian_months = {
        1: 'იანვარი',
        2: 'თებერვალი',
        3: 'მარტი',
        4: 'აპრილი',
        5: 'მაისი',
        6: 'ივნისი',
        7: 'ივლისი',
        8: 'აგვისტო',
        9: 'სექტემბერი',
        10: 'ოქტომბერი',
        11: 'ნოემბერი',
        12: 'დეკემბერი'
    }
    if hasattr(date, 'hour'):
        return f"{date.day} {georgian_months[date.month]}, {date.year} {date.hour:02d}:{date.minute:02d}"
    return f"{date.day} {georgian_months[date.month]}, {date.year}"

# Create Flask app
app = Flask(__name__)

# Add the custom filter
app.jinja_env.filters['georgian_date'] = georgian_date

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER
app.config['MATERIAL_FOLDER'] = MATERIAL_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)

# Create upload directories
os.makedirs(MATERIAL_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Create all database tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def save_file(form_file, folder):
    """Save uploaded file and return filename"""
    if form_file:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_file.filename)
        filename = random_hex + f_ext
        filepath = os.path.join(folder, filename)
        form_file.save(filepath)
        return filename
    return None

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.route('/')
def home():
    """Home page with latest materials"""
    materials = EducationalMaterial.query.order_by(EducationalMaterial.date_posted.desc()).all()
    return render_template('home.html', materials=materials)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/material/new', methods=['GET', 'POST'])
@login_required
def new_material():
    """Create new educational material"""
    form = EducationalMaterialForm()
    if form.validate_on_submit():
        try:
            # Save files if they exist
            image_file = save_file(form.image.data, app.config['IMAGE_FOLDER']) if form.image.data else None
            material_file = save_file(form.material_file.data, app.config['MATERIAL_FOLDER']) if form.material_file.data else None
            
            material = EducationalMaterial(
                title=form.title.data,
                content=form.content.data,
                subject=form.subject.data,
                grade_level=form.grade_level.data,
                material_type=form.material_type.data,
                image_file=image_file,
                file_path=material_file,
                author=current_user
            )
            db.session.add(material)
            db.session.commit()
            flash('თქვენი მასალა წარმატებით აიტვირთა!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            # Clean up any uploaded files if database operation fails
            if image_file:
                try:
                    os.remove(os.path.join(app.config['IMAGE_FOLDER'], image_file))
                except OSError:
                    pass
            if material_file:
                try:
                    os.remove(os.path.join(app.config['MATERIAL_FOLDER'], material_file))
                except OSError:
                    pass
            flash('მასალის ატვირთვისას მოხდა შეცდომა. გთხოვთ სცადოთ მოგვიანებით.', 'danger')
            print(f"Upload error: {e}")
    return render_template('create_material.html', form=form, title='ახალი მასალა')

@app.route('/material/<int:material_id>', methods=['GET', 'POST'])
def material(material_id):
    """View educational material and handle comments"""
    material = EducationalMaterial.query.get_or_404(material_id)
    form = CommentForm()
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('კომენტარის დასატოვებლად გაიარეთ ავტორიზაცია', 'info')
            return redirect(url_for('login'))
        
        comment = Comment(
            content=form.content.data,
            author=current_user,
            material=material
        )
        db.session.add(comment)
        try:
            db.session.commit()
            flash('კომენტარი წარმატებით დაემატა!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('კომენტარის დამატებისას მოხდა შეცდომა.', 'danger')
            print(f"Comment error: {e}")
        return redirect(url_for('material', material_id=material_id))
    
    comments = Comment.query.filter_by(material_id=material_id)\
        .order_by(Comment.date_posted.desc()).all()
    
    return render_template('material.html', 
                         title=material.title, 
                         material=material, 
                         form=form,
                         comments=comments)

@app.route('/material/<int:material_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_material(material_id):
    """Edit educational material"""
    material = EducationalMaterial.query.get_or_404(material_id)
    if material.author != current_user and current_user.username != 'hageograpia_admin':
        flash('თქვენ არ გაქვთ ამ მასალის რედაქტირების უფლება', 'danger')
        return redirect(url_for('home'))
    
    form = EducationalMaterialForm()
    if form.validate_on_submit():
        try:
            # Update files if new ones are uploaded
            if form.image.data:
                old_image = material.image_file
                material.image_file = save_file(form.image.data, app.config['IMAGE_FOLDER'])
                if old_image:
                    os.remove(os.path.join(app.config['IMAGE_FOLDER'], old_image))

            if form.material_file.data:
                old_file = material.file_path
                material.file_path = save_file(form.material_file.data, app.config['MATERIAL_FOLDER'])
                if old_file:
                    os.remove(os.path.join(app.config['MATERIAL_FOLDER'], old_file))

            # Update other fields
            form.populate_obj(material)
            db.session.commit()
            flash('მასალა წარმატებით განახლდა!', 'success')
            return redirect(url_for('material', material_id=material.id))
        except Exception as e:
            flash('მასალის განახლებისას მოხდა შეცდომა.', 'danger')
            print(f"Update error: {e}")
    elif request.method == 'GET':
        form = EducationalMaterialForm(obj=material)
    return render_template('create_material.html', form=form, title='მასალის რედაქტირება', material=material)

@app.route('/material/<int:material_id>/delete', methods=['POST'])
@login_required
def delete_material(material_id):
    """Delete educational material"""
    material = EducationalMaterial.query.get_or_404(material_id)
    
    if material.author != current_user and current_user.username != 'hageograpia_admin':
        flash('თქვენ არ გაქვთ ამ მასალის წაშლის უფლება', 'danger')
        return redirect(url_for('home'))
    
    try:
        image_path = os.path.join(app.config['IMAGE_FOLDER'], material.image_file) if material.image_file else None
        material_path = os.path.join(app.config['MATERIAL_FOLDER'], material.file_path) if material.file_path else None
        
        db.session.delete(material)
        db.session.commit()
        
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass
                
        if material_path and os.path.exists(material_path):
            try:
                os.remove(material_path)
            except OSError:
                pass
        
        flash('მასალა წარმატებით წაიშალა!', 'success')
    except Exception:
        db.session.rollback()
        flash('მასალის წაშლისას მოხდა შეცდომა.', 'danger')
    
    return redirect(url_for('home'))

@app.route('/material/<int:material_id>/download')
def download_material(material_id):
    """Download educational material file"""
    material = EducationalMaterial.query.get_or_404(material_id)
    if not material.file_path:
        flash('მასალის ფაილი არ არის ხელმისაწვდომი', 'warning')
        return redirect(url_for('material', material_id=material.id))
    
    try:
        return send_file(
            os.path.join(app.config['MATERIAL_FOLDER'], material.file_path),
            as_attachment=True,
            download_name=secure_filename(f"{material.title}{os.path.splitext(material.file_path)[1]}")
        )
    except Exception:
        flash('ფაილის ჩამოტვირთვისას მოხდა შეცდომა.', 'danger')
        return redirect(url_for('material', material_id=material.id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                flash('წარმატებით შეხვედით სისტემაში!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
            else:
                flash('შესვლა ვერ მოხერხდა. გთხოვთ შეამოწმოთ მომხმარებლის სახელი და პაროლი', 'danger')
        except Exception:
            flash('სისტემური შეცდომა. გთხოვთ სცადოთ მოგვიანებით.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            hashed_password = generate_password_hash(form.password.data)
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            flash('რეგისტრაცია წარმატებით დასრულდა! შეგიძლიათ შეხვიდეთ სისტემაში', 'success')
            return redirect(url_for('login'))
        except Exception:
            db.session.rollback()
            flash('სისტემური შეცდომა რეგისტრაციისას. გთხოვთ სცადოთ მოგვიანებით.', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('წარმატებით გამოხვედით სისტემიდან!', 'success')
    return redirect(url_for('home'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with contact form"""
    form = ContactForm()
    if form.validate_on_submit():
        try:
            flash('თქვენი შეტყობინება წარმატებით გაიგზავნა!', 'success')
            return redirect(url_for('contact'))
        except Exception:
            flash('შეტყობინების გაგზავნისას მოხდა შეცდომა. გთხოვთ სცადოთ მოგვიანებით.', 'danger')
    return render_template('contact.html', title='კონტაქტი', form=form)

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html', title='პროფილი')

@app.route('/my-materials')
@login_required
def my_materials():
    """Show user's materials"""
    materials = EducationalMaterial.query.filter_by(author=current_user)\
        .order_by(EducationalMaterial.date_posted.desc()).all()
    return render_template('my_materials.html', title='ჩემი მასალები', materials=materials)

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user and not current_user.is_admin:
        flash('თქვენ არ გაქვთ ამ კომენტარის წაშლის უფლება', 'danger')
        return redirect(url_for('material', material_id=comment.material_id))
    
    db.session.delete(comment)
    db.session.commit()
    flash('კომენტარი წაიშალა!', 'success')
    return redirect(url_for('material', material_id=comment.material_id))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5002')
