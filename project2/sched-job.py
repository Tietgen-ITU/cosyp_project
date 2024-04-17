import paramiko
import getpass
import time
import os
from scp import SCPClient

username = input('Enter your username: ')
password = getpass.getpass('Enter your password: ')


ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('hpc.itu.dk', username=username, password=password)

# Upload files from our src directory to the remote directory
local_dir = './src/'
remote_dir = '~/cosyp/'
with SCPClient(ssh.get_transport()) as scp:
    scp.put(local_dir, remote_dir, recursive=True)

# Schedule jobs
remote_job_file = '~/cosyp/psql.job' # TODO: This should maybe be a parameter or an argument to the script
stdin, stdout, stderr = ssh.exec_command(f'sbatch {remote_job_file}')
job_id = int(stdout.read().decode().split()[-1])
print(f'Submitted job with ID {job_id}')
