import paramiko

class SSHConnection:
    def __init__(self, host, port, username, password) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def ssh_command(self, command):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(self.host, port=self.port, username=self.username, password=self.password)   
            stdin, stdout, stderr = client.exec_command(command)
            print("Comando executado com sucesso")
    
        finally:
            client.close()

ssh = SSHConnection('localhost', 80, 'root', '1234')
ssh.ssh_command('')