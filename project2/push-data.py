import sys
import paramiko
import getpass
from scp import SCPClient

def copy_to_remote(ssh, local_dir, remote_dir):
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(local_dir, remote_dir, recursive=True)

if __name__ == "__main__":

    username = input('Enter your username: ')
    password = getpass.getpass('Enter your password: ')

    print('Connecting to HPC...')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('hpc.itu.dk', username=username, password=password)

    print('Copying data files to shared remote...')
    copy_to_remote(ssh, './data', '/scratch/group_brrrrr')
