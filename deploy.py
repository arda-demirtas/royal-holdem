import paramiko
import os
import sys

# Reconfigure stdout and stderr to handle UTF-8 symbols without crashing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def main():
    host = "46.225.59.232"
    port = 22
    username = "root"
    password = "Taktakshow123*"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    try:
        ssh.connect(host, port, username, password, timeout=30)
        print("Connected successfully!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    commands = [
        "cd /var/www/holdem && git pull",
        "cd /var/www/holdem/frontend && npm run build",
        "pm2 restart all",
        "pm2 status"
    ]

    for cmd in commands:
        print(f"\n--- Running: {cmd} ---")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # Wait for the command to finish
        exit_status = stdout.channel.recv_exit_status()
        
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        
        if out:
            print("Output:")
            print(out)
        if err:
            print("Error:")
            print(err)
            
        print(f"Exit status: {exit_status}")

    ssh.close()
    print("SSH connection closed.")

if __name__ == "__main__":
    try:
        main()
    finally:
        # Self-destruct
        try:
            print("Self-destructing deploy.py...")
            os.remove(__file__)
        except Exception as e:
            print(f"Failed to self-destruct: {e}")
