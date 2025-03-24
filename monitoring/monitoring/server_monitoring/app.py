import io
import logging
import paramiko
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from cryptography.fernet import Fernet
import winrm
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234!@#$Qwerty'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/server_monitoring'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Encryption key (store securely in production)
key = Fernet.generate_key()
cipher = Fernet(key)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # Plain text password
    is_admin = db.Column(db.Boolean, default=False)
    privileges = db.Column(db.String(120), default='read')

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(80))
    ip_address = db.Column(db.String(15), unique=True, nullable=False)
    username = db.Column(db.LargeBinary, nullable=False)
    password = db.Column(db.LargeBinary, nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    environment = db.Column(db.String(20), nullable=False)
    operating_system = db.Column(db.String(255))
    kernel = db.Column(db.String(255))
    total_disk_gb = db.Column(db.Integer)
    free_disk_gb = db.Column(db.Integer)
    total_ram_gb = db.Column(db.Integer)
    cpu_count = db.Column(db.Integer)
    boot_time = db.Column(db.String(80))
    status = db.Column(db.Boolean)

    def encrypt_field(self, data):
        return cipher.encrypt(data.encode())

    def decrypt_field(self, data):
        return cipher.decrypt(data).decode()

    def set_username(self, username):
        self.username = self.encrypt_field(username)

    def get_username(self):
        return self.decrypt_field(self.username)

    def set_password(self, password):
        self.password = self.encrypt_field(password)

    def get_password(self):
        return self.decrypt_field(self.password)

@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Loading user with ID: {user_id}")
    try:
        user = db.session.get(User, int(user_id))
        if user:
            logger.debug(f"Loaded user: {user.username}")
        else:
            logger.warning(f"User with ID {user_id} not found")
        return user
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

def fetch_server_details(ip_address, username, password, platform):
    details = {'operating_system': 'Unknown', 'kernel': 'Unknown', 'total_disk_gb': 0, 'free_disk_gb': 0,
               'total_ram_gb': 0, 'cpu_count': 0, 'boot_time': 'Unknown', 'status': False}
    try:
        if platform == 'Windows':
            logger.debug(f"Fetching details for Windows server {ip_address}")
            sess = winrm.Session(ip_address, auth=(username, password), transport='ntlm')
            result = sess.run_ps('(Get-CimInstance Win32_OperatingSystem)')
            stdout = result.std_out.decode()
            if 'Caption' in stdout:
                details['operating_system'] = stdout.split('Caption')[1].split('\n')[0].strip()
            if 'TotalVisibleMemorySize' in stdout:
                details['total_ram_gb'] = int(stdout.split('TotalVisibleMemorySize')[1].split('\n')[0].strip()) // 1024 // 1024 or 0
            if 'FreeSpace' in stdout:
                details['free_disk_gb'] = int(stdout.split('FreeSpace')[1].split('\n')[0].strip()) // 1024 // 1024 // 1024 or 0
            if 'Size' in stdout:
                details['total_disk_gb'] = int(stdout.split('Size')[1].split('\n')[0].strip()) // 1024 // 1024 // 1024 or 0
            if 'NumberOfCores' in stdout:
                details['cpu_count'] = int(stdout.split('NumberOfCores')[1].split('\n')[0].strip()) or 0
            if 'LastBootUpTime' in stdout:
                details['boot_time'] = stdout.split('LastBootUpTime')[1].split('\n')[0].strip()
            details['status'] = True
        else:
            logger.debug(f"Fetching details for Linux/Unix server {ip_address}")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip_address, username=username, password=password, timeout=5)
            stdin, stdout, stderr = ssh.exec_command('uname -a')
            details['kernel'] = stdout.read().decode().strip() or 'Unknown'
            stdin, stdout, stderr = ssh.exec_command('cat /proc/cpuinfo | grep "processor" | wc -l')
            cpu_output = stdout.read().decode().strip()
            details['cpu_count'] = int(cpu_output) if cpu_output and cpu_output.isdigit() else 0
            stdin, stdout, stderr = ssh.exec_command('df -h / | tail -1 | awk \'{print $2}\'')
            total_disk = stdout.read().decode().strip().replace('G', '')
            details['total_disk_gb'] = int(total_disk) if total_disk and total_disk.isdigit() else 0
            stdin, stdout, stderr = ssh.exec_command('df -h / | tail -1 | awk \'{print $4}\'')
            free_disk = stdout.read().decode().strip().replace('G', '')
            details['free_disk_gb'] = int(free_disk) if free_disk and free_disk.isdigit() else 0
            stdin, stdout, stderr = ssh.exec_command('free -g | grep Mem | awk \'{print $2}\'')
            total_ram = stdout.read().decode().strip()
            details['total_ram_gb'] = int(total_ram) if total_ram and total_ram.isdigit() else 0
            stdin, stdout, stderr = ssh.exec_command('uptime -s')
            details['boot_time'] = stdout.read().decode().strip() or 'Unknown'
            stdin, stdout, stderr = ssh.exec_command('cat /etc/os-release')
            os_info = stdout.read().decode()
            for line in os_info.split('\n'):
                if line.startswith('PRETTY_NAME'):
                    details['operating_system'] = line.split('=')[1].strip('"') or 'Unknown'
            details['status'] = True
            ssh.close()
        logger.debug(f"Successfully fetched details for {ip_address}: {details}")
    except Exception as e:
        logger.error(f"Error fetching details for {ip_address}: {str(e)}")
        details['status'] = False
    return details

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        logger.debug(f"Login attempt for username: {username}")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            logger.info(f"User {username} logged in successfully")
            flash("Logged in successfully", "success")
            return redirect(url_for('dashboard'))
        logger.warning(f"Failed login attempt for username: {username}")
        flash("Invalid username or password", "danger")
    logger.info(f"User accessed login page")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logger.info(f"User {current_user.username} logged out")
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    logger.info(f"User {current_user.username} accessed register page")
    with db.session.no_autoflush:
        try:
            servers = Server.query.all()
            logger.debug(f"Fetched {len(servers)} servers from database")
            if request.method == 'POST':
                if 'delete' in request.form:
                    server_id = request.form['delete']
                    server = db.session.get(Server, int(server_id))
                    if server:
                        db.session.delete(server)
                        db.session.commit()
                        logger.info(f"Server {server.ip_address} deleted by {current_user.username}")
                        flash("Server deleted successfully", "success")
                    else:
                        flash("Server not found", "danger")
                    return redirect(url_for('register'))

                if 'bulk_register' in request.form:
                    file = request.files['file']
                    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xls') or file.filename.endswith('.xlsx')):
                        try:
                            if file.filename.endswith('.csv'):
                                df = pd.read_csv(file)
                            else:
                                df = pd.read_excel(file)
                            required_columns = ['ip_address', 'username', 'password', 'platform', 'environment']
                            if not all(col in df.columns for col in required_columns):
                                flash("Invalid file format. Required columns: ip_address, username, password, platform, environment", "danger")
                                return redirect(url_for('register'))
                            for _, row in df.iterrows():
                                if Server.query.filter_by(ip_address=row['ip_address']).first():
                                    continue
                                server = Server(
                                    ip_address=row['ip_address'],
                                    platform=row['platform'],
                                    environment=row['environment']
                                )
                                server.set_username(row['username'])
                                server.set_password(row['password'])
                                details = fetch_server_details(server.ip_address, server.get_username(), server.get_password(), server.platform)
                                server.operating_system = details['operating_system']
                                server.kernel = details['kernel']
                                server.total_disk_gb = details['total_disk_gb']
                                server.free_disk_gb = details['free_disk_gb']
                                server.total_ram_gb = details['total_ram_gb']
                                server.cpu_count = details['cpu_count']
                                server.boot_time = details['boot_time']
                                server.status = details['status']
                                db.session.add(server)
                            db.session.commit()
                            logger.info(f"Bulk servers registered successfully by {current_user.username}")
                            flash("Bulk servers registered successfully", "success")
                        except Exception as e:
                            db.session.rollback()
                            logger.error(f"Error during bulk registration: {str(e)}")
                            flash(f"Error during bulk registration: {str(e)}", "danger")
                else:
                    ip_address = request.form['ip_address']
                    username = request.form['username']
                    password = request.form['password']
                    platform = request.form['platform']
                    environment = request.form['environment']
                    if Server.query.filter_by(ip_address=ip_address).first():
                        flash("Server already registered", "danger")
                        return redirect(url_for('register'))
                    server = Server(ip_address=ip_address, platform=platform, environment=environment)
                    server.set_username(username)
                    server.set_password(password)
                    details = fetch_server_details(ip_address, username, password, platform)
                    server.operating_system = details['operating_system']
                    server.kernel = details['kernel']
                    server.total_disk_gb = details['total_disk_gb']
                    server.free_disk_gb = details['free_disk_gb']
                    server.total_ram_gb = details['total_ram_gb']
                    server.cpu_count = details['cpu_count']
                    server.boot_time = details['boot_time']
                    server.status = details['status']
                    db.session.add(server)
                    db.session.commit()
                    logger.info(f"Server {ip_address} registered by {current_user.username}")
                    flash("Server registered successfully", "success")
                    return redirect(url_for('register'))

                # CLI functionality moved here
                if 'cli_server_id' in request.form:
                    server_id = request.form['cli_server_id']
                    server = db.session.get(Server, int(server_id))
                    if not server:
                        flash("Server not found", "danger")
                        return redirect(url_for('register'))
                    output = ""
                    if request.method == 'GET' and 'cli_session' in session:
                        session.pop('cli_session', None)
                        logger.debug(f"Cleared CLI session for server {server_id}")
                    if 'exit' in request.form:
                        session.pop('cli_session', None)
                        logger.info(f"CLI session ended for server {server.ip_address} by {current_user.username}")
                        flash("CLI session ended", "success")
                        return redirect(url_for('register'))
                    elif 'username' in request.form and 'password' in request.form:
                        cli_username = request.form['username']
                        cli_password = request.form['password']
                        logger.debug(f"CLI connection attempt for {server.ip_address} with username: {cli_username}")
                        if server.platform == 'Windows':
                            try:
                                sess = winrm.Session(server.ip_address, auth=(cli_username, cli_password), transport='ntlm')
                                sess.run_cmd('echo.')
                                session['cli_session'] = {'type': 'winrm', 'ip': server.ip_address, 'username': cli_username, 'password': cli_password}
                                logger.info(f"Connected to PowerShell on {server.ip_address}")
                                flash("Connected to PowerShell", "success")
                            except Exception as e:
                                logger.error(f"CLI connection failed for {server.ip_address}: {str(e)}")
                                flash(f"Invalid credentials or connection failed: {str(e)}", "danger")
                        else:
                            try:
                                ssh = paramiko.SSHClient()
                                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                ssh.connect(server.ip_address, username=cli_username, password=cli_password, timeout=5)
                                session['cli_session'] = {'type': 'ssh', 'ip': server.ip_address, 'username': cli_username, 'password': cli_password}
                                ssh.close()
                                logger.info(f"Connected to SSH on {server.ip_address}")
                                flash("Connected to SSH terminal", "success")
                            except Exception as e:
                                logger.error(f"CLI connection failed for {server.ip_address}: {str(e)}")
                                flash(f"Invalid credentials or connection failed: {str(e)}", "danger")
                    elif 'command' in request.form and 'cli_session' in session:
                        command = request.form['command']
                        logger.debug(f"Executing command '{command}' on {server.ip_address}")
                        if session['cli_session']['type'] == 'winrm':
                            try:
                                sess = winrm.Session(session['cli_session']['ip'], auth=(session['cli_session']['username'], session['cli_session']['password']), transport='ntlm')
                                result = sess.run_ps(command)
                                output = result.std_out.decode() or result.std_err.decode()
                                logger.info(f"Command '{command}' executed successfully on {server.ip_address}")
                                flash("Command executed", "success")
                                session.pop('cli_session', None)
                            except Exception as e:
                                output = f"Failed: {str(e)}"
                                logger.error(f"Command execution failed on {server.ip_address}: {str(e)}")
                                flash("Command execution failed", "danger")
                        else:
                            try:
                                ssh = paramiko.SSHClient()
                                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                ssh.connect(session['cli_session']['ip'], username=session['cli_session']['username'], password=session['cli_session']['password'], timeout=5)
                                stdin, stdout, stderr = ssh.exec_command(command)
                                output = stdout.read().decode() or stderr.read().decode()
                                ssh.close()
                                logger.info(f"Command '{command}' executed successfully on {server.ip_address}")
                                flash("Command executed", "success")
                                session.pop('cli_session', None)
                            except Exception as e:
                                output = f"Failed: {str(e)}"
                                logger.error(f"Command execution failed on {server.ip_address}: {str(e)}")
                                flash("Command execution failed", "danger")
                    return render_template('register.html', servers=servers, cli_server=server, cli_output=output, cli_session='cli_session' in session)

            return render_template('register.html', servers=servers)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error in register: {str(e)}")
            flash(f"Unexpected error: {str(e)}", "danger")
            return render_template('register.html', servers=[])
    return render_template('register.html', servers=[])

@app.route('/download_sample')
def download_sample():
    sample_data = "ip_address,username,password,platform,environment\n192.168.1.1,admin,pass123,Linux,prod\n192.168.1.2,user,pass456,Windows,DR"
    return Response(
        sample_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=sample_servers.csv"}
    )

@app.route('/download_sample_excel')
def download_sample_excel():
    df = pd.DataFrame([
        ["192.168.1.1", "admin", "pass123", "Linux", "prod"],
        ["192.168.1.2", "user", "pass456", "Windows", "DR"]
    ], columns=["ip_address", "username", "password", "platform", "environment"])
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name='sample_servers.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/modify_server/<int:server_id>', methods=['GET', 'POST'])
@login_required
def modify_server(server_id):
    server = db.session.get(Server, server_id)
    if not server or not current_user.is_admin:
        flash("Access denied or server not found", "danger")
        return redirect(url_for('register'))
    if request.method == 'POST':
        server.ip_address = request.form['ip_address']
        server.set_username(request.form['username'])
        server.set_password(request.form['password'])
        server.platform = request.form['platform']
        server.environment = request.form['environment']
        details = fetch_server_details(server.ip_address, server.get_username(), server.get_password(), server.platform)
        server.operating_system = details['operating_system']
        server.kernel = details['kernel']
        server.total_disk_gb = details['total_disk_gb']
        server.free_disk_gb = details['free_disk_gb']
        server.total_ram_gb = details['total_ram_gb']
        server.cpu_count = details['cpu_count']
        server.boot_time = details['boot_time']
        server.status = details['status']
        db.session.commit()
        logger.info(f"Server {server.ip_address} modified by {current_user.username}")
        flash("Server updated successfully", "success")
        return redirect(url_for('register'))
    return render_template('modify_server.html', server=server)

@app.route('/update_patches/<int:server_id>', methods=['POST'])
@login_required
def update_patches(server_id):
    server = db.session.get(Server, server_id)
    if not server or not current_user.is_admin:
        return jsonify({"message": "Access denied or server not found"}), 403
    if server.platform == 'Linux':
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(server.ip_address, username=server.get_username(), password=server.get_password(), timeout=5)
            if 'Ubuntu' in server.operating_system:
                ssh.exec_command('apt update && apt upgrade -y')
            elif 'CentOS' in server.operating_system or 'Red Hat' in server.operating_system:
                ssh.exec_command('yum update -y')
            ssh.close()
            logger.info(f"Patches updated for Linux server {server.ip_address} by {current_user.username}")
            return jsonify({"message": "Patches updated successfully"})
        except Exception as e:
            logger.error(f"Error updating patches for {server.ip_address}: {str(e)}")
            return jsonify({"message": f"Error updating patches: {str(e)}"})
    elif server.platform == 'Windows':
        try:
            sess = winrm.Session(server.ip_address, auth=(server.get_username(), server.get_password()), transport='ntlm')
            sess.run_ps('Install-WindowsUpdate -AcceptAll -AutoReboot')
            logger.info(f"Patches updated for Windows server {server.ip_address} by {current_user.username}")
            return jsonify({"message": "Patches updated successfully"})
        except Exception as e:
            logger.error(f"Error updating patches for {server.ip_address}: {str(e)}")
            return jsonify({"message": f"Error updating patches: {str(e)}"})
    return jsonify({"message": "Patch update not supported for this platform"})

@app.route('/dashboard')
@login_required
def dashboard():
    logger.info(f"User {current_user.username} accessed dashboard")
    servers = Server.query.all()
    return render_template('dashboard.html', servers=servers)

@app.route('/reports')
@login_required
def reports():
    logger.info(f"User {current_user.username} accessed reports page")
    servers = Server.query.all()
    return render_template('reports.html', servers=servers)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        logger.warning(f"User {current_user.username} attempted to access admin page without permission")
        flash("Access denied", "danger")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = 'is_admin' in request.form
        privileges = request.form['privileges']
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for('admin'))
        user = User(username=username, password=password, is_admin=is_admin, privileges=privileges)
        db.session.add(user)
        db.session.commit()
        logger.info(f"Admin created new user: {username}")
        flash("User created successfully", "success")
        return redirect(url_for('admin'))
    users = User.query.all()
    return render_template('admin.html', users=users)

def create_default_admin():
    with app.app_context():
        try:
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    password='admin123',
                    is_admin=True,
                    privileges='read,write,delete'
                )
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Created default admin user: admin")
            else:
                logger.info("Default admin user already exists")
        except Exception as e:
            logger.error(f"Failed to create default admin user: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    logger.info("Starting Flask application")
    app.run(debug=True, host='0.0.0.0', port=5000)