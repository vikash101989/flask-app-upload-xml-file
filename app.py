from flask import Flask, request, redirect, url_for, render_template, flash, jsonify
from werkzeug.utils import secure_filename
import os
from models import db, Job, UserData
from xml.etree import ElementTree as ET
import uuid
import threading
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)

# Create DB tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file and file.filename.endswith('.xml'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Create a new job
        job_id = str(uuid.uuid4())
        new_job = Job(id=job_id, status='Queued', filename=filename)
        db.session.add(new_job)
        db.session.commit()

        # Start a thread to process the job
        threading.Thread(target=process_job, args=(file_path, job_id)).start()

        return redirect(url_for('view_job', job_id=job_id))
    else:
        flash('Not correct format, XML requred.')
        return redirect(url_for('index'))

def process_job(file_path, job_id):
    with app.app_context():
        job = Job.query.get(job_id)
        job.status = 'Processing'
        db.session.commit()
        time.sleep(3)

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            for user in root.findall('.//user'):
                name = user.find('name').text
                phone = user.find('phone').text
                address = user.find('address').text

                new_user_data = UserData(
                    name=name,
                    job_id=job_id,
                    phone=phone,
                    address=address
                )
                db.session.add(new_user_data)

            job.status = 'Completed'
            db.session.commit()
        except Exception as e:
            job.status = f'Failed: {str(e)}'
            db.session.commit()

@app.route('/view_job/<job_id>')
def view_job(job_id):
    job = Job.query.get(job_id)
    return render_template('view_job.html', job=job)

@app.route('/job_status/<job_id>', methods=['GET'])
def job_status(job_id):
    job = Job.query.get(job_id)
    if job.status == 'Completed':
        # Fetch extracted data
        user_data = UserData.query.filter_by(job_id=job_id).all()
        data = [{'id': user.id, 'name': user.name, 'phone': user.phone, 'address': user.address} for user in user_data]
        return jsonify({'status': job.status, 'data': data})
    else:
        return jsonify({'status': job.status})

if __name__ == '__main__':
    app.run(debug=True)
