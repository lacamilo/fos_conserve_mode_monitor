#!/usr/bin/env python3

import re
import sys
import time
import paramiko
import fg_logger

class FortigateSSHClient:
    def __init__(self, host, port, user, log_file, log_level):
        self.cycle_interval = None
        self.host = host
        self.port = port
        self.user = user
        self.password = None
        self.prompt = "# "
        self.logger = fg_logger.configure_logger(log_file, log_level)
        self.ssh_client = None
        self.connected = False

    def connect_ssh(self):
        client = paramiko.SSHClient()
        try:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.host, username=self.user, password=self.password, port=self.port)
            return client.invoke_shell()
        except Exception as ex:
            self.logger.error("SSH connection wasn't established!")
            self.logger.error(str(ex))  # Log the exception details
            sys.exit(1)

    def send_command(self, command, show=False):
        output, clean_output = "", ""
        self.ssh_client.send(command + "\n")
        if command != "":
            time.sleep(0.1)
            while not output.endswith(self.prompt):
                try:
                    output_chunk = self.ssh_client.recv(1024).decode("utf-8")
                    if not output_chunk:
                        break
                    output += output_chunk
                except Exception as e:
                    self.logger.error(f"Error receiving data: {e}")
                    break
            clean_output = fg_logger.remove_special_chars(output)
            clean_output = fg_logger.remove_last_line(clean_output)
            if show:
                self.logger.info(f"COMMAND: {clean_output}")
        return clean_output

    def execute_commands(self, commands):
        full_output = ""
        for command, show_output in commands:
            output = self.send_command(command, show=show_output)
            full_output += output
        return full_output

    def memory_system_performance(self, output, memory_threshold):
        # this function returns True if global memory threshold is crossed and false if it's not.
        memory_match = re.search(r'Memory: \d+k total, \d+k used \((\d+\.\d+)%\)', output)
        if memory_match:
            used_percent = float(memory_match.group(1))
            self.logger.info(f"Used memory: {used_percent}%")
            if used_percent > memory_threshold:
                self.logger.warning(
                    f"Used memory is above the threshold of {memory_threshold}%. Checking application individual "
                    f"userspace usage...")
                return True
            else:
                self.logger.info(
                    f"Used memory is below the threshold of {memory_threshold}%. No further action taken...")
                return False

    def aditional_commands(self):
        # when this function is called, it will run a sequence of aditional commands.
        self.send_command('get hardware memory', show=True)
        self.send_command('get system performance status', show=True)
        self.send_command('diag hardware sysinfo slab', show=True)
        self.logger.info("Collecting: diag sys mpstat 5 1 - Wait 5 sec please...")
        self.send_command('diag sys mpstat 5 1', show=True)
        self.send_command('diag sys top-fd 20', show=True)
        self.send_command('diagnose sys top-sockmem 10', show=True)
        self.send_command('fnsysctl cat /proc/version', show=True)
        self.send_command('fnsysctl cat /proc/vmstat', show=True)
        self.send_command('fnsysctl cat /proc/vmallocinfo', show=True)
        self.send_command('fnsysctl du /dev/shm', show=True)
        # self.send_command('', show=True)
        return None

    def process_top_mem(self, output, pmem_threshold, kill):
        # this function will try to find the top processes consuming userspace memory
        processes = re.findall(r'(\w+)\s+\((\d+)\):\s+(\d+)kB', output)
        above_threshold = False
        if not processes:
            self.logger.info("No processes found in 'diag sys top-mem' output...")
        else:
            for process in processes:
                name, pid, mem_kb = process
                # print("memory: " + str(process))
                mem_mb = int(mem_kb) / 1024
                # print ("memory: " + str(mem_mb))
                if name == 'ipsengine' and mem_mb > pmem_threshold:
                    above_threshold = True
                    self.logger.warning(f"Process: {name}, PID: {pid}, Memory Usage: {mem_mb:.2f} MB")
                    self.logger.warning('------------ High memory found ipsengine ------------')
                    self.send_command(f'diag sys process dump {pid}', show=True)
                    self.send_command(f'diag sys process pstack {pid}', show=True)
                    self.send_command('fnsysctl du /dev/shm', show=True)
                    time.sleep(5)  # sleep and stack again to see if pointers are moving.
                    self.send_command(f'diag sys process pstack {pid}', show=True)
                    self.send_command('fnsysctl du /dev/shm', show=True)
                    self.send_command('diag ips memory status', show=True)
                    self.send_command('diag ips session status', show=True)
                    self.send_command('diag test application ipsmonitor 24', show=True)
                    self.aditional_commands()
                elif (name == 'wad' or name == 'proxyd') and mem_mb > pmem_threshold:
                    above_threshold = True
                    self.logger.warning(f"Process: {name}, PID: {pid}, Memory Usage: {mem_mb:.2f} MB")
                    self.logger.warning('------------ High memory found wad ------------')
                    self.send_command(f'diag sys process dump {pid}', show=True)
                    self.send_command(f'diag sys process pstack {pid}', show=True)
                    self.send_command('fnsysctl du /dev/shm', show=True)
                    time.sleep(3)  # sleep and stack again to see if pointers are moving.
                    self.send_command('diag wad stats worker.sysmem', show=True)
                    self.send_command(f'diag sys process pstack {pid}', show=True)
                    self.send_command('fnsysctl du /dev/shm', show=True)
                    self.send_command('diag wad memory overused', show=True)
                    self.aditional_commands()

                # run any aditional commands after a high memory event is detected.
                elif mem_mb > pmem_threshold:
                    self.logger.warning(f"Process: {name}, PID: {pid}, Memory Usage: {mem_mb:.2f} MB")
                    self.logger.warning('------------ High memory found ------------')
                    self.logger.info(f"No special procedure to capture process {name}, collecting general output")
                    self.aditional_commands()
                    # elf.logger.warning('Debug collected successfully, please upload output.log file on the ticket')
                    # self.logger.warning('under System => Settings => Download the Debug logs and attach them on the
                    # ticket as well')
                    # self.logger.info('When this tool is not needed anymore, consider deleting .pwd and .key files')
                    # sys.exit()

            # Kill high mem process
            if kill == 1:
                # for now, only killing ips and wad processes
                for process in processes:
                    name, pid, mem_kb = process
                    mem_mb = int(mem_kb) / 1024
                    if name == 'ipsengine' and mem_mb > pmem_threshold:
                        above_threshold = True
                        self.logger.warning(f"Process: {name}, PID: {pid}, Memory Usage: {mem_mb:.2f} MB")
                        self.logger.warning(f"Kill Process PID: {pid} ")
                        self.send_command(f'diag sys kill 11 {pid}', show=True)
                    if name == 'wad' and mem_mb > pmem_threshold:
                        above_threshold = True
                        self.logger.warning(f"Process: {name}, PID: {pid}, Memory Usage: {mem_mb:.2f} MB")
                        self.logger.warning(f"Restarting all WAD Processes")
                        self.send_command('diag test app wad 99', show=True)
                        # self.send_command('diag wad memory report', show=True)

        if not above_threshold:
            self.logger.info(f"No userspace process above defined threshold: {pmem_threshold:.2f} MB")

    def ensure_connection(self):
        if not self.connected:
            self.ssh_client = self.connect_ssh()
            self.send_command('config global', False)
            self.connected = True

    def run_infinite_loop(self, commands_list, cycle_interval, threshold, pmem_threshold, kill, log_file):
        self.cycle_interval = cycle_interval
        try:
            while True:
                self.ensure_connection()
                output = self.execute_commands(commands_list)
                threshold_crossed = self.memory_system_performance(output, threshold)
                if threshold_crossed:
                    self.process_top_mem(output, pmem_threshold=pmem_threshold, kill=kill)
                self.logger.info(f"Waiting for {cycle_interval}s before next cycle...")
                time.sleep(cycle_interval)

        except KeyboardInterrupt:
            self.logger.info("CTRL+C Pressed - Exiting due to user interruption.\n")
            print(f'File saved successfully, please zip and upload {log_file} to the ticket')
        except Exception as e:
            self.logger.error(f"An error occurred during the infinite loop: {e}")
            self.logger.info(f"Waiting for {cycle_interval}s before attempting to reconnect...")
            self.connected = False
            time.sleep(cycle_interval)
            self.run_infinite_loop(commands_list, cycle_interval, threshold, pmem_threshold, kill, log_file)

    def close(self):
        self.ssh_client.close()
