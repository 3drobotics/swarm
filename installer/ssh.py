import paramiko
import sys
import socket
import time

class ssh_instance():
	def connect(self,ip, await=True, silent=False):
    		self.client = paramiko.SSHClient()
    		self.client.load_system_host_keys()
    		self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    		socket.setdefaulttimeout(5)
    		message = silent
   		start = time.time()
    		while True:
        		try:
            			self.client.connect(ip, username='root', password='TjSDBkAu', timeout=5)
        		except paramiko.BadHostKeyException:
            			print 'error: {} has an incorrect entry in ~/.ssh/known_hosts. please run:'.format(ip)
            			print ''
            			print '    ssh-keygen -R {}'.format(ip)
            			print ''
            			print 'and try again'
            			sys.exit(1)
        		except Exception as e:
            			if not await:
                			raise e
            			if not message and time.time() - start > 5:
                			message = True
                			print '(note: ensure you are connected to Solo\'s wifi network.)'
            			self.client.close()
            			continue
        		time.sleep(1)
        		break
    		socket.setdefaulttimeout(None)
    		return self.client

	def connect_controller(await=True, silent=False):
    		return _connect('10.1.1.1', await=await, silent=silent)

	def connect_solo(await=True, silent=False):
    		return _connect('10.1.1.10', await=await, silent=silent)

	def command_stream(client, cmd, stdout=sys.stdout, stderr=sys.stderr):
    		chan = client.get_transport().open_session()
    		chan.exec_command(cmd)
    		while True:
        		time.sleep(0.1)
        		if chan.recv_ready():
            			str = chan.recv(4096).decode('ascii')
            			if stdout:
                			stdout.write(str)
       			if chan.recv_stderr_ready():
            			str = chan.recv_stderr(4096).decode('ascii')
           	 		if stderr:
                			stderr.write(str)
        		if chan.exit_status_ready():
            			break
    		code = chan.recv_exit_status()
    		chan.close()
    		return code

	def command_blind(self, cmd):
    		chan = self.client.get_transport().open_session()
    		chan.exec_command(cmd)

	def command(self, cmd):
    		chan = self.client.get_transport().open_session()
    		chan.exec_command(cmd)
    		stderr = ''
    		stdout = ''
    		while True:
        		time.sleep(0.1)
        		if chan.recv_ready():
            			stdout += chan.recv(4096).decode('ascii')
        		if chan.recv_stderr_ready():
            			stderr += chan.recv_stderr(4096).decode('ascii')
        		if chan.exit_status_ready():
            			break
    		code = chan.recv_exit_status()
    		chan.close()
    		return stdout
