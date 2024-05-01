import sys
import paramiko
import getpass
from scp import SCPClient

def copy_to_remote(ssh, local_dir, remote_dir):
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(local_dir, remote_dir, recursive=True)

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print('Usage: python sched-job.py <psql | elastic>')
        sys.exit(1)

    dbms_type = sys.argv[1]

    username = input('Enter your username: ')
    password = getpass.getpass('Enter your password: ')

    print('Connecting to HPC...')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('hpc.itu.dk', username=username, password=password)

    # Upload files from our src directory to the remote directory
    print('Copying files to remote...')
    copy_to_remote(ssh, './src', '~/cosyp')

    # Schedule jobs
    remote_job_file = f'~/cosyp/{dbms_type}.job'
    stdin, stdout, stderr = ssh.exec_command(f'sbatch {remote_job_file}')
    job_id = int(stdout.read().decode().split()[-1])
    print(f'Submitted job with ID {job_id}')
