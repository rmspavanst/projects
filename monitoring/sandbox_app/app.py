# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from config import Config
from models import db, User, SandboxInstance
from datetime import datetime, timedelta
import uuid
import paramiko
import boto3
from botocore.exceptions import ClientError
import time
import pytz

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()

# Vagrant instance launch
def launch_vagrant_instance(sandbox_type, instance_name, os_type):
    print(f"Starting launch_vagrant_instance for {instance_name}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    logs = []

    try:
        print("Attempting SSH connection to 10.0.16.153")
        ssh.connect('10.0.16.153', username='root', password='root', timeout=10)
        logs.append("SSH connection established")
        flash("SSH connection successful.")

        vagrantfile_content = f"""
Vagrant.configure("2") do |config|
  config.vm.box = "{os_type}"
  config.vm.network "public_network", bridge: "ens18"
  config.vm.provider "virtualbox" do |vb|
    vb.name = "{instance_name}"
    vb.memory = "2048"
    vb.cpus = 1
  end
end
"""
        remote_dir = f"/root/vagrant/vagrant_{instance_name}"
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_dir}")
        stdout.channel.recv_exit_status()
        logs.extend(stdout.readlines() + stderr.readlines())
        flash(f"Directory created: {remote_dir}")

        sftp = ssh.open_sftp()
        with sftp.file(f"{remote_dir}/Vagrantfile", 'w') as f:
            f.write(vagrantfile_content)
        sftp.close()
        logs.append(f"Vagrantfile written to {remote_dir}")
        flash(f"Vagrantfile written to {remote_dir}")

        stdin, stdout, stderr = ssh.exec_command(f"cd {remote_dir} && vagrant up")
        logs.extend(stdout.readlines() + stderr.readlines())
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            flash(f"Vagrant up failed with exit status {exit_status}")
            logs.append(f"Vagrant up failed with exit status {exit_status}")
            return None, logs
        logs.append("Vagrant instance launched")
        flash("Vagrant instance launched.")

        stdin, stdout, stderr = ssh.exec_command(f"cd {remote_dir} && vagrant ssh -c 'ip a | grep eth1 | grep inet | awk \"{{print \\$2}}\" | cut -d/ -f1'")
        logs.extend(stderr.readlines())
        public_ip = stdout.read().decode().strip()
        if not public_ip:
            flash("Failed to retrieve public IP!")
            logs.append("Failed to retrieve public IP")
            return None, logs
        logs.append(f"Public IP retrieved: {public_ip}")
        flash(f"Public IP retrieved: {public_ip}")

        return public_ip, logs
    except Exception as e:
        error_msg = f"Error launching Vagrant instance: {str(e)}"
        flash(error_msg)
        logs.append(error_msg)
        return None, logs
    finally:
        ssh.close()
        logs.append("SSH connection closed")

# AWS instance launch
def launch_aws_instance(instance_name, ports, username, password, auto_terminate_time):
    logs = []
    region = "ap-southeast-5"
    key_name = "rmsmy"
    ec2_client = boto3.client('ec2', region_name=region)

    try:
        user_data = f"""#!/bin/bash
        useradd -m -s /bin/bash -p $(openssl passwd -1 {password}) {username}
        usermod -aG wheel {username}
        echo "{username} ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/{username}
        sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
        sudo systemctl restart sshd
        """
        logs.append("Preparing user data script")
        flash("Preparing user data script for AWS.")

        port_list = [int(port.strip()) for port in ports.split(",") if port.strip()]
        if 22 not in port_list:
            port_list.append(22)
        timestamp = int(time.time())
        sg_name = f"{instance_name}-sg-{timestamp}"
        sg_response = ec2_client.create_security_group(
            GroupName=sg_name,
            Description=f"Security group for {instance_name}"
        )
        security_group_id = sg_response['GroupId']
        for port in port_list:
            ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[{'IpProtocol': 'tcp', 'FromPort': port, 'ToPort': port, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]
            )
        logs.append(f"Security group {sg_name} created")
        flash(f"Security group {sg_name} created.")

        instance = ec2_client.run_instances(
            ImageId='ami-0742a9acc3cfa7a10',
            InstanceType='t3.micro',
            MinCount=1,
            MaxCount=1,
            KeyName=key_name,
            UserData=user_data,
            SecurityGroupIds=[security_group_id],
            TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': instance_name}]}]
        )
        instance_id = instance['Instances'][0]['InstanceId']
        logs.append(f"Instance {instance_id} launched")
        flash(f"Instance {instance_id} launched.")

        waiter = ec2_client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        public_ip = response['Reservations'][0]['Instances'][0].get('PublicIpAddress', 'pending')
        if public_ip != 'pending':
            logs.append(f"Public IP retrieved: {public_ip}")
            flash(f"Public IP retrieved: {public_ip}")
        else:
            logs.append("Public IP pending, will update later")
            flash("Public IP pending, will update later.")

        return instance_id, public_ip, ",".join(map(str, port_list)), logs
    except Exception as e:
        error_msg = f"Error launching AWS instance: {str(e)}"
        flash(error_msg)
        logs.append(error_msg)
        return None, None, None, logs

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('sandbox'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('home'))

@app.route('/sandbox', methods=['GET', 'POST'])
@login_required
def sandbox():
    allowed_sandboxes = current_user.sandboxes.split(',') if current_user.sandboxes else []
    logs = []
    print("Entering /sandbox route")

    if request.method == 'POST':
        print("Received POST request")
        print(f"Form data: {request.form}")
        try:
            sandbox_type = request.form.get('sandbox_type')
            if not sandbox_type:
                flash("Sandbox type is required!")
                print("Missing sandbox_type")
                return redirect(url_for('sandbox'))
            if sandbox_type not in allowed_sandboxes:
                flash('You do not have access to this sandbox!')
                print(f"User lacks access to {sandbox_type}")
                return redirect(url_for('sandbox'))

            num_instances = request.form.get('num_instances', type=int)
            if not num_instances or not 1 <= num_instances <= 5:
                flash("Number of instances must be between 1 and 5!")
                print(f"Invalid num_instances: {num_instances}")
                return redirect(url_for('sandbox'))

            instance_names = request.form.getlist('instance_names')
            auto_terminate_hours = request.form.get('auto_terminate_hours', type=int)
            if len(instance_names) != num_instances or not auto_terminate_hours or auto_terminate_hours > 24:
                flash("Invalid instance names or auto-terminate time (max 24 hours)!")
                print(f"Invalid instance_names length: {len(instance_names)} or auto_terminate_hours: {auto_terminate_hours}")
                return redirect(url_for('sandbox'))

            print(f"Launching {num_instances} instances of type {sandbox_type}")
            if sandbox_type == 'Vagrant':
                os_type = request.form.get('os_type')
                if not os_type:
                    flash("OS type is required for Vagrant!")
                    print("Missing os_type")
                    return redirect(url_for('sandbox'))

                for name in instance_names:
                    print(f"Launching Vagrant instance: {name}")
                    public_ip, instance_logs = launch_vagrant_instance(sandbox_type, name, os_type)
                    logs.extend(instance_logs)
                    if public_ip:
                        instance = SandboxInstance(
                            user_id=current_user.id,
                            sandbox_type=sandbox_type,
                            instance_name=name,
                            instance_id=f"vagrant-{uuid.uuid4().hex[:8]}",
                            public_ip=public_ip,
                            username='vagrant',
                            password='vagrant',
                            auto_terminate_time=datetime.now() + timedelta(hours=auto_terminate_hours),
                            launch_time=datetime.now(pytz.utc)
                        )
                        db.session.add(instance)
                        logs.append(f"Instance {name} added to database")
                        print(f"Instance {name} added to database")
                    else:
                        flash(f"Failed to launch instance {name}")
                        print(f"Failed to launch Vagrant instance {name}")

            elif sandbox_type == 'AWS':
                ports_list = request.form.getlist('ports')
                username = request.form.get('username')
                password = request.form.get('password')
                if len(ports_list) != num_instances or not username or not password:
                    flash("Ports, username, and password are required for AWS!")
                    print(f"Missing AWS fields: ports={len(ports_list)}, username={username}, password={password}")
                    return redirect(url_for('sandbox'))

                for i, name in enumerate(instance_names):
                    print(f"Launching AWS instance: {name}")
                    instance_id, public_ip, ports, instance_logs = launch_aws_instance(
                        name, ports_list[i], username, password, auto_terminate_hours
                    )
                    logs.extend(instance_logs)
                    if instance_id:
                        instance = SandboxInstance(
                            user_id=current_user.id,
                            sandbox_type=sandbox_type,
                            instance_name=name,
                            instance_id=instance_id,
                            public_ip=public_ip,
                            username=username,
                            password=password,
                            ports=ports,
                            auto_terminate_time=datetime.now() + timedelta(hours=auto_terminate_hours),
                            launch_time=datetime.now(pytz.utc)
                        )
                        db.session.add(instance)
                        logs.append(f"Instance {name} added to database")
                        print(f"Instance {name} added to database")
                    else:
                        flash(f"Failed to launch instance {name}")
                        print(f"Failed to launch AWS instance {name}")

            db.session.commit()
            flash(f"{num_instances} {sandbox_type} instances created successfully!")
            print(f"Successfully committed {num_instances} instances")
        except Exception as e:
            flash(f"Error processing request: {str(e)}")
            logs.append(f"Error: {str(e)}")
            print(f"Exception in POST: {str(e)}")
            db.session.rollback()
            return redirect(url_for('sandbox'))

    # Fetch instances and calculate remaining time
    if current_user.is_admin:
        instances = SandboxInstance.query.all()
    else:
        instances = SandboxInstance.query.filter_by(user_id=current_user.id).all()

    instances_with_owners = []
    for instance in instances:
        if instance.status == 'running':
            remaining_time = instance.auto_terminate_time - datetime.now(pytz.utc) if instance.auto_terminate_time else timedelta(0)
            remaining_time_str = f"{remaining_time.seconds // 3600:02}:{(remaining_time.seconds % 3600) // 60:02}:{remaining_time.seconds % 60:02}" if remaining_time.total_seconds() > 0 else "00:00:00"
            instances_with_owners.append({
                'instance': instance,
                'owner': db.session.get(User, instance.user_id).username if db.session.get(User, instance.user_id) else 'Unknown',
                'remaining_time': remaining_time_str
            })

    print(f"Rendering sandbox.html with {len(instances_with_owners)} instances")
    return render_template('sandbox.html', instances_with_owners=instances_with_owners, allowed_sandboxes=allowed_sandboxes, logs=logs)

@app.route('/terminate_instance/<int:id>')
@login_required
def terminate_instance(id):
    instance = SandboxInstance.query.get_or_404(id)
    if not current_user.is_admin and instance.user_id != current_user.id:
        flash('You can only terminate your own instances!')
        return redirect(url_for('sandbox'))
    if instance.status == 'terminated':
        flash('Instance already terminated!')
        return redirect(url_for('sandbox'))

    try:
        if instance.sandbox_type == 'Vagrant':
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect('10.0.16.153', username='root', password='root', timeout=10)
            remote_dir = f"/root/vagrant/vagrant_{instance.instance_name}"
            ssh.exec_command(f"cd {remote_dir} && vagrant destroy -f")
            ssh.exec_command(f"rm -rf {remote_dir}")
            flash(f"VM and directory {remote_dir} deleted on remote server.")
            ssh.close()

        elif instance.sandbox_type == 'AWS':
            ec2_client = boto3.client('ec2', region_name="ap-southeast-5")
            ec2_client.terminate_instances(InstanceIds=[instance.instance_id])
            waiter = ec2_client.get_waiter('instance_terminated')
            waiter.wait(InstanceIds=[instance.instance_id])
            sg_response = ec2_client.describe_security_groups(
                Filters=[{'Name': 'group-name', 'Values': [f"{instance.instance_name}-sg-*"]}]
            )
            for sg in sg_response['SecurityGroups']:
                ec2_client.delete_security_group(GroupId=sg['GroupId'])
            flash(f"AWS instance {instance.instance_id} terminated.")

        db.session.delete(instance)
        db.session.commit()
        flash('Instance terminated and removed from database!')
    except Exception as e:
        flash(f"Error terminating instance: {str(e)}")
    return redirect(url_for('sandbox'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('Admin access only!')
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        sandboxes = ','.join(request.form.getlist('sandboxes'))
        is_admin = 'is_admin' in request.form
        user = User(username=username, password=password, is_admin=is_admin, sandboxes=sandboxes)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!')
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/update_user/<int:id>', methods=['GET', 'POST'])
@login_required
def update_user(id):
    if not current_user.is_admin:
        flash('Admin access only!')
        return redirect(url_for('home'))
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.password = request.form['password']
        user.sandboxes = ','.join(request.form.getlist('sandboxes'))
        user.is_admin = 'is_admin' in request.form
        db.session.commit()
        flash('User updated successfully!')
        return redirect(url_for('admin'))
    return render_template('update_user.html', user=user)

@app.route('/delete_user/<int:id>')
@login_required
def delete_user(id):
    if not current_user.is_admin:
        flash('Admin access only!')
        return redirect(url_for('home'))
    user = User.query.get_or_404(id)
    if user.is_admin:
        flash('Cannot delete admin users!')
        return redirect(url_for('admin'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!')
    return redirect(url_for('admin'))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)