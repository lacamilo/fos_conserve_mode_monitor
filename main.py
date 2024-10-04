#!/usr/bin/env python3

# compile info: pyinstaller --icon=performance.ico --clean -Fn fos_conserve_v0.3.exe main.py --upx-dir "C:\Program Files\UPX"
# https://github.com/upx/upx/releases/tag/v4.2.2
# bug_id=0898404

import argparse
import getpass
import paramiko
import mem_debug
import password_manager

if __name__ == '__main__':
    fortigate_client = None
    ssh_client = None
    manager = password_manager.PasswordManager()
    parser = argparse.ArgumentParser(
        prog="fos_conserve.exe",
        description='Fortigate Conserve mode monitor and script collector - lcamilo@fortinet.com',
        #usage="fos_conserve.exe --host --user --save 1 -p -l -c -t -p -k",
        epilog="Example : fos_conserve.exe --host 172.16.45.1 --user admin --save 1",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--host", required=True, help='Fortigate hostname or IP address')
    parser.add_argument("--port", required=False, default=22, help='SSH port')
    parser.add_argument("--user", required=True, help='SSH username')
    parser.add_argument("--save", type=int, default=0, help='set 1 to encrypt and cache password')
    parser.add_argument("--log-file", default="output.log", help='Log file to store output')
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help='Logging level - Feature in progress')
    parser.add_argument("--mode", default="conserve", choices=["conserve", "fgcat"], help='conserve=memory conserve mode - fgcat=Fortiguard category errors')
    parser.add_argument("--cycle-interval", type=int, default=20, help='Interval (in seconds) between cycles - default 20 sec')
    parser.add_argument("--threshold", type=float, default=79, help='Overall used memory threshold in percentage - default 79')
    parser.add_argument("--pmem_threshold", type=float, default=500, help='Threshold for user process memory usage in MB - default 500MB')
    parser.add_argument("--kill", type=int, default=0, help='0=dont kill, 1=will kill memory spiking processes')
    parser.add_argument("--version", action='version', version='%(prog)s 0.3')
    args = parser.parse_args()

    username = args.user
    existing_password = manager.retrieve_password(username)

    if existing_password is not None:
        password = existing_password
        print('Existing password retrieved successfully.')
    else:
        password = getpass.getpass('Enter your password: ')

    try:
        ssh_client = (mem_debug.FortigateSSHClient(args.host, args.port, args.user, args.log_file, args.log_level))

        commands_list = [
            ("get system performance status", False),
            ("diag sys top-mem 16", True),
        ]

        if args.save:
            manager.store_password(username, password)
            encryption_key = password_manager.load_encryption_key("key.key")
            encrypted_password = password_manager.load_encrypted_password(f"{args.user}.pwd")
            ssh_client.password = password_manager.decrypt_password(encrypted_password, encryption_key)
        else:
            ssh_client.password = password

        ssh_client.logger.info("------------ Program Start ------------")
        ssh_client.run_infinite_loop(commands_list, args.cycle_interval, args.threshold, args.pmem_threshold, args.kill, args.log_file)
        ssh_client.close()

        # if args.mode == "conserve":
        #     ssh_client.run_infinite_loop(commands_list, cycle_interval=args.cycle_interval, threshold=args.threshold,
        #                                  pmem_threshold=args.pmem_threshold, kill=args.kill)
        #     ssh_client.close()
        # if args.mode == "fgcat":
        #     print("fortiguard")

    except paramiko.AuthenticationException:
        ssh_client.logger.error("Authentication failed. Please check your credentials.")
        ssh_client.logger.error("Delete the .pwd file and try again")
    except paramiko.SSHException as e:
        ssh_client.logger.error(f"SSH error: {e}")
    except Exception as e:
        ssh_client.logger.error(f"An error occurred: {e}")

# Changelog:
# v0.3 - jan 2024 - improving ipsengine capture and cosmetics
#        splitting fg_logger functionality to a separated module.
#        adding --port parameter to specify an ssh port other than 22
#        adding option to save and cache password file
#        adding version control on github
