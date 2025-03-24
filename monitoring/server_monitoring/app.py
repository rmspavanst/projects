from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Server
from config import Config
import paramiko
import winrm
import pandas as pd
import io
import time
import threading
import openpyxl
from collections import Counter
import logging
import os

# Configure logging
log_dir = '/var/log/monitor'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    os.chmod(log_dir, 0o750)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'your-secret-key'
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

app.jinja_env.globals.update(zip=zip)

@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Loading user with ID: {user_id}")
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123', is_admin=True, privileges='all')
        db.session.add(admin)
        db.session.commit()
        logger.info("Created default admin user")

def fetch_server_details(ip_address, username, password, platform):
    details = {'hostname': None, 'operating_system': None, 'kernel': None, 'total_disk_gb': None, 'free_disk_gb': None, 'total_ram_gb': None, 'cpu_count': None, 'boot_time': None}
    logger.debug(f"Fetching details for server {ip_address} ({platform})")
    if platform == 'Windows':
        try:
            sess = winrm.Session(ip_address, auth=(username, password), transport='ntlm')
            details['hostname'] = sess.run_cmd('hostname').std_out.decode().strip()
            details['operating_system'] = sess.run_cmd('systeminfo | findstr /B /C:"OS Name"').std_out.decode().strip().split(':')[1].strip()
            details['kernel'] = sess.run_cmd('systeminfo | findstr /B /C:"OS Version"').std_out.decode().strip().split(':')[1].strip()
            result = sess.run_cmd('wmic logicaldisk get size,freespace')
            lines = result.std_out.decode().splitlines()[1].split()
            details['total_disk_gb'] = int(int(lines[1]) / (1024**3)) if lines else 0
            details['free_disk_gb'] = int(int(lines[0]) / (1024**3)) if lines else 0
            details['total_ram_gb'] = int(int(sess.run_cmd('wmic computersystem get TotalPhysicalMemory').std_out.decode().splitlines()[1]) / (1024**3))
            details['cpu_count'] = int(sess.run_cmd('wmic cpu get NumberOfLogicalProcessors').std_out.decode().splitlines()[1])
            uptime = sess.run_cmd('wmic os get LastBootUpTime').std_out.decode().splitlines()[1].split('.')[0]
            details['boot_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - int(uptime[:14]) / 1000000))
            logger.info(f"Successfully fetched details for Windows server {ip_address}")
        except Exception as e:
            logger.error(f"Windows fetch error for {ip_address}: {str(e)}")
            details['hostname'] = f"Unknown-{ip_address}"
            details['operating_system'] = "Unknown"
    else:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip_address, username=username, password=password, timeout=5)
            details['hostname'] = ssh.exec_command('hostname')[1].read().decode().strip()
            os_info = ssh.exec_command('cat /etc/os-release')[1].read().decode()
            for line in os_info.splitlines():
                if line.startswith('PRETTY_NAME='):
                    details['operating_system'] = line.split('=')[1].strip('"')
                    break
            else:
                details['operating_system'] = "Unknown"
            details['kernel'] = ssh.exec_command('uname -r')[1].read().decode().strip()
            lines = ssh.exec_command('df -h /')[1].read().decode().splitlines()[1].split()
            details['total_disk_gb'] = int(lines[1].replace('G', '')) if lines else 0
            details['free_disk_gb'] = int(lines[3].replace('G', '')) if lines else 0
            details['total_ram_gb'] = int(ssh.exec_command('free -g')[1].read().decode().splitlines()[1].split()[1])
            details['cpu_count'] = int(ssh.exec_command('nproc')[1].read().decode().strip())
            uptime = float(ssh.exec_command('cat /proc/uptime')[1].read().decode().split()[0])
            details['boot_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - uptime))
            ssh.close()
            logger.info(f"Successfully fetched details for Linux server {ip_address}")
        except Exception as e:
            logger.error(f"Linux fetch error for {ip_address}: {str(e)}")
            details['hostname'] = f"Unknown-{ip_address}"
            details['operating_system'] = "Unknown"
    return details

def is_server_powered_on(ip_address, username, password, platform):
    logger.debug(f"Checking power status for {ip_address} ({platform})")
    if platform == 'Windows':
        try:
            winrm.Session(ip_address, auth=(username, password), transport='ntlm').run_cmd('echo.')
            logger.debug(f"Server {ip_address} is powered on")
            return True
        except:
            logger.debug(f"Server {ip_address} is powered off or unreachable")
            return False
    else:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip_address, username=username, password=password, timeout=5)
            ssh.close()
            logger.debug(f"Server {ip_address} is powered on")
            return True
        except:
            logger.debug(f"Server {ip_address} is powered off or unreachable")
            return False

def fetch_server_status(server):
    logger.debug(f"Fetching status for server {server.ip_address}")
    server.status = is_server_powered_on(server.ip_address, server.get_username(), server.get_password(), server.platform)

@app.route('/')
def home():
    logger.info("Accessed home page")
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.info("Accessed login page")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        logger.debug(f"Login attempt for username: {username}")
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            logger.info(f"User {username} logged in successfully")
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        logger.warning(f"Failed login attempt for username: {username}")
        flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logger.info(f"User {current_user.username} logged out")
    logout_user()
    session.pop('cli_session', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    logger.info(f"User {current_user.username} accessed admin page")
    if not current_user.is_admin:
        logger.warning(f"User {current_user.username} denied access to admin page")
        flash("Access denied: Admin only", "danger")
        return redirect(url_for('home'))
    if request.method == 'POST':
        if 'delete' in request.form:
            user_id = request.form['user_id']
            user = db.session.get(User, user_id)
            if user and not user.is_admin:
                db.session.delete(user)
                db.session.commit()
                logger.info(f"User {user.username} deleted by {current_user.username}")
                flash(f"User {user.username} deleted", "success")
        elif 'update' in request.form:
            user_id = request.form['user_id']
            user = db.session.get(User, user_id)
            if user:
                user.username = request.form['username']
                user.password = request.form['password']
                user.is_admin = 'is_admin' in request.form
                privileges = request.form.getlist('privileges')
                if 'read' in request.form:
                    privileges.append('read')
                user.privileges = ','.join(privileges)
                db.session.commit()
                logger.info(f"User {user.username} updated by {current_user.username}")
                flash(f"User {user.username} updated", "success")
        else:
            username = request.form['username']
            password = request.form['password']
            is_admin = 'is_admin' in request.form
            privileges = request.form.getlist('privileges')
            if 'read' in request.form:
                privileges.append('read')
            user = User(username=username, password=password, is_admin=is_admin, privileges=','.join(privileges))
            db.session.add(user)
            db.session.commit()
            logger.info(f"User {username} added by {current_user.username}")
            flash(f"User {username} added", "success")
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    logger.info(f"User {current_user.username} accessed register page")
    if 'register' not in current_user.privileges and not current_user.is_admin:
        logger.warning(f"User {current_user.username} denied access to register page")
        flash("Access denied", "danger")
        return redirect(url_for('home'))
    if request.method == 'POST':
        if 'delete' in request.form:
            if not current_user.is_admin:
                logger.warning(f"User {current_user.username} attempted to delete server without admin privileges")
                flash("Only admin can delete servers", "danger")
            else:
                server_id = request.form['server_id']
                server = db.session.get(Server, server_id)
                if server:
                    db.session.delete(server)
                    db.session.commit()
                    logger.info(f"Server {server.ip_address} deleted by {current_user.username}")
                    flash(f"Server {server.ip_address} deleted", "success")
        elif 'update' in request.form:
            if not current_user.is_admin:
                logger.warning(f"User {current_user.username} attempted to update server without admin privileges")
                flash("Only admin can update servers", "danger")
            else:
                server_id = request.form['server_id']
                server = db.session.get(Server, server_id)
                if server:
                    ip_address = request.form['ip_address']
                    username = request.form['username']
                    password = request.form['password']
                    platform = request.form['platform']
                    environment = request.form['environment']
                    if Server.query.filter_by(ip_address=ip_address).filter(Server.id != server_id).first():
                        logger.warning(f"Attempt to update server {server_id} with duplicate IP {ip_address}")
                        flash("IP address already registered", "danger")
                    else:
                        details = fetch_server_details(ip_address, username, password, platform)
                        server.ip_address = ip_address
                        server.set_username(username)
                        server.set_password(password)
                        server.platform = platform
                        server.environment = environment
                        server.hostname = details['hostname']
                        server.operating_system = details['operating_system']
                        server.kernel = details['kernel']
                        server.total_disk_gb = details['total_disk_gb']
                        server.free_disk_gb = details['free_disk_gb']
                        server.total_ram_gb = details['total_ram_gb']
                        server.cpu_count = details['cpu_count']
                        server.boot_time = details['boot_time']
                        db.session.commit()
                        logger.info(f"Server {ip_address} updated by {current_user.username}")
                        flash(f"Server {ip_address} updated", "success")
        elif 'file' in request.files:
            file = request.files['file']
            logger.debug(f"Processing file upload: {file.filename}")
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                logger.warning(f"Invalid file format uploaded: {file.filename}")
                flash("Invalid file format", "danger")
                return redirect(url_for('register'))
            for _, row in df.iterrows():
                if Server.query.filter_by(ip_address=row['ip_address']).first():
                    logger.warning(f"Server {row['ip_address']} already registered, skipping")
                    flash(f"Server {row['ip_address']} already registered", "danger")
                    continue
                details = fetch_server_details(row['ip_address'], row['username'], row['password'], row['platform'])
                server = Server(
                    hostname=details['hostname'],
                    ip_address=row['ip_address'],
                    platform=row['platform'],
                    environment=row['environment'],
                    operating_system=details['operating_system'],
                    kernel=details['kernel'],
                    total_disk_gb=details['total_disk_gb'],
                    free_disk_gb=details['free_disk_gb'],
                    total_ram_gb=details['total_ram_gb'],
                    cpu_count=details['cpu_count'],
                    boot_time=details['boot_time']
                )
                server.set_username(row['username'])
                server.set_password(row['password'])
                db.session.add(server)
            db.session.commit()
            logger.info(f"Bulk server registration completed by {current_user.username}")
            flash("Servers registered successfully", "success")
        else:
            ip_address = request.form['ip_address']
            username = request.form['username']
            password = request.form['password']
            platform = request.form['platform']
            environment = request.form['environment']
            if Server.query.filter_by(ip_address=ip_address).first():
                logger.warning(f"Server {ip_address} already registered")
                flash("Server already registered", "danger")
            else:
                details = fetch_server_details(ip_address, username, password, platform)
                server = Server(
                    hostname=details['hostname'],
                    ip_address=ip_address,
                    platform=platform,
                    environment=environment,
                    operating_system=details['operating_system'],
                    kernel=details['kernel'],
                    total_disk_gb=details['total_disk_gb'],
                    free_disk_gb=details['free_disk_gb'],
                    total_ram_gb=details['total_ram_gb'],
                    cpu_count=details['cpu_count'],
                    boot_time=details['boot_time']
                )
                server.set_username(username)
                server.set_password(password)
                db.session.add(server)
                db.session.commit()
                logger.info(f"Server {ip_address} registered by {current_user.username}")
                flash("Server registered successfully", "success")
    servers = Server.query.all()
    return render_template('register.html', servers=servers)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    logger.info(f"User {current_user.username} accessed dashboard")
    if 'dashboard' not in current_user.privileges and 'read' not in current_user.privileges and not current_user.is_admin:
        logger.warning(f"User {current_user.username} denied access to dashboard")
        flash("Access denied", "danger")
        return redirect(url_for('home'))
    servers = Server.query.all()
    threads = []
    for server in servers:
        t = threading.Thread(target=fetch_server_status, args=(server,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    platform_counts = Counter((server.platform, server.status) for server in servers)
    platform_data = {
        'labels': [f"{platform} ({'On' if status else 'Off'})" for platform, status in platform_counts.keys()],
        'data': list(platform_counts.values())
    }
    platform_filter = request.form.get('platform', '') if request.method == 'POST' else ''
    env_filter = request.form.get('environment', '') if request.method == 'POST' else ''
    status_filter = request.form.get('status', '') if request.method == 'POST' else ''
    logger.debug(f"Dashboard filter applied: platform={platform_filter}, environment={env_filter}, status={status_filter}")
    filtered_servers = [s for s in servers if 
                        (not platform_filter or s.platform == platform_filter) and 
                        (not env_filter or s.environment == env_filter) and 
                        (not status_filter or (status_filter == 'On' and s.status) or (status_filter == 'Off' and not s.status))]
    servers_with_status = [
        {
            'id': server.id,
            'hostname': server.hostname,
            'ip_address': server.ip_address,
            'platform': server.platform,
            'operating_system': server.operating_system,
            'environment': server.environment,
            'kernel': server.kernel,
            'total_disk_gb': server.total_disk_gb,
            'free_disk_gb': server.free_disk_gb,
            'total_ram_gb': server.total_ram_gb,
            'cpu_count': server.cpu_count,
            'boot_time': server.boot_time,
            'is_powered_on': server.status
        }
        for server in filtered_servers
    ]
    return render_template('dashboard.html', platform_data=platform_data, servers=servers_with_status, 
                          platform_filter=platform_filter, env_filter=env_filter, status_filter=status_filter)

@app.route('/server_details/<int:server_id>')
@login_required
def server_details(server_id):
    logger.info(f"User {current_user.username} accessed details for server ID {server_id}")
    server = db.session.get(Server, server_id)
    if not server:
        logger.warning(f"Server ID {server_id} not found")
        flash("Server not found", "danger")
        return redirect(url_for('dashboard'))
    server.status = is_server_powered_on(server.ip_address, server.get_username(), server.get_password(), server.platform)
    return render_template('server_details.html', server=server)

@app.route('/cli/<int:server_id>', methods=['GET', 'POST'])
@login_required
def cli(server_id):
    logger.info(f"User {current_user.username} accessed CLI for server ID {server_id}")
    server = db.session.get(Server, server_id)
    if not server:
        logger.warning(f"Server ID {server_id} not found")
        flash("Server not found", "danger")
        return redirect(url_for('register'))
    output = ""
    if request.method == 'GET' and 'cli_session' in session:
        session.pop('cli_session', None)
        logger.debug(f"Cleared CLI session for server {server_id}")
    if request.method == 'POST':
        if 'exit' in request.form:
            session.pop('cli_session', None)
            logger.info(f"CLI session ended for server {server.ip_address} by {current_user.username}")
            flash("CLI session ended", "success")
            return redirect(url_for('register'))
        elif 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            logger.debug(f"CLI connection attempt for {server.ip_address} with username: {username}")
            if server.platform == 'Windows':
                try:
                    sess = winrm.Session(server.ip_address, auth=(username, password), transport='ntlm')
                    sess.run_cmd('echo.')
                    session['cli_session'] = {'type': 'winrm', 'ip': server.ip_address, 'username': username, 'password': password}
                    logger.info(f"Connected to PowerShell on {server.ip_address}")
                    flash("Connected to PowerShell", "success")
                except Exception as e:
                    logger.error(f"CLI connection failed for {server.ip_address}: {str(e)}")
                    flash(f"Invalid credentials or connection failed: {str(e)}", "danger")
            else:
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(server.ip_address, username=username, password=password, timeout=5)
                    session['cli_session'] = {'type': 'ssh', 'ip': server.ip_address, 'username': username, 'password': password}
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
                except Exception as e:
                    output = f"Failed: {str(e)}"
                    logger.error(f"Command execution failed on {server.ip_address}: {str(e)}")
                    flash("Command execution failed", "danger")
    return render_template('cli.html', server=server, output=output, session='cli_session' in session)

@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    logger.info(f"User {current_user.username} accessed reports page")
    if 'reports' not in current_user.privileges and 'read' not in current_user.privileges and not current_user.is_admin:
        logger.warning(f"User {current_user.username} denied access to reports")
        flash("Access denied", "danger")
        return redirect(url_for('home'))
    servers = Server.query.all()
    fields = ['hostname', 'ip_address', 'platform', 'operating_system', 'environment', 'kernel', 'total_disk_gb', 'free_disk_gb', 'total_ram_gb', 'cpu_count', 'boot_time']
    headers = ['Hostname', 'IP Address', 'Platform', 'Operating System', 'Environment', 'Kernel', 'Total Disk (GB)', 'Free Disk (GB)', 'Total RAM (GB)', 'CPU Count', 'Boot Time']
    show_fields = False
    selected_fields = []
    filtered_servers = servers

    if request.method == 'POST':
        if 'generate_report' in request.form:
            show_fields = True
            logger.debug("Showing field selection for report generation")
        elif 'generate_excel' in request.form:
            selected_fields = request.form.getlist('fields')
            if not selected_fields:
                logger.warning("Excel generation attempted with no fields selected")
                flash("Please select at least one field for the report", "warning")
                show_fields = True
            else:
                buffer = io.BytesIO()
                df = pd.DataFrame([[getattr(server, field) for field in fields if field in selected_fields] for server in filtered_servers], 
                                columns=[headers[i] for i in range(len(fields)) if fields[i] in selected_fields])
                df.to_excel(buffer, index=False, engine='openpyxl')
                buffer.seek(0)
                logger.info(f"Excel report generated by {current_user.username} with fields: {selected_fields}")
                flash("Excel generated successfully", "success")
                return send_file(buffer, as_attachment=True, download_name='report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    return render_template('reports.html', servers=filtered_servers, fields=fields, headers=headers, 
                          show_fields=show_fields, selected_fields=selected_fields)

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(debug=True, host='0.0.0.0')
