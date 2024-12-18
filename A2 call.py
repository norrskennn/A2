from ast import main
from logging import FileHandler
from random import choice
from netmiko import ConnectHandler
import difflib
import logging

#Establish cisco_router information
router_info = {
    'device_type': 'cisco_ios',
    'host': '192.168.56.101',
    'username': 'prne',
    'password': 'cisco123!',
    'secret': 'class123!', 
}

#Hostname rename
hostname = 'R1'

#Cisco hardening advice
hardening_advice = """
! Cisco Hardening Advice

!General Recommendations

enable secret 5 $1$dYxA$WbhPASqVS56AAvopBYAbk1
service password-encrption
no ip http server
no ip http secure-sever
ip domain name example.netacad.com
crypto key generate rsa modulus 2048
login block-for 120 attempts 3 within 60

! Management Access Control
line vty 0 15
    transport input ssh
    login local
    transport input telnet
    exec-timeout 5 0
    access-class 15
    password class123!

! Console Access Control
line con 0
    login local
    exec-timeout 5 0 
    access class 15 in
    password cisco123!

! SNMP Configuration
no snmp-server community
no snmp-server contact
no snmp-server location

! Loggin configuration
logging buffered 4096
logging console critical
logging console warnings
logging trap notifications
no logging source-interface

! NTP Configuration
no ntp server
no ntp source

! Access control lists 
no ip access-list standards
    no permit
    no deny any log

! interface Security
interface range 192.168.56.101/24
    no cdp enable
    switchport mode access
    switchport negotiate
    spanning-trr portfast
    ip verify source
"""

device_config = ""

acl_list = 'acl_conf.txt'

#IPsec parameters
isakmp_policy = 10 #lower number mean higher priority 
crypto_map = 'VPN_MAP' #a crypto map defines ipsec polcies that specify which traffic should be encrypted 
shared_key =  'Th3cra!c$f@rfr0mm!ghty' #this key must be configured identically on both ends for a VPN Connection 

def ssh(router_infoo):
    try:
        #Establish SSH connection
        with ConnectHandler(**router_infoo) as ssh_connection:
            #Enable mode
            ssh_connection.enable()
            print("SSH connection successful")

            #Log a syslog message
            ssh_connection.send_command("SSH Connection established.")

    #Print error message in string
    except Exception as e:
        print(f"Error!: {str(e)}")

#Establish a Telnet connection
def telnet(router_infoo):
    try:
        with ConnectHandler(**router_infoo)as telnet_connection:
            
            #Send a syslog message to the file for telnet connection
            telnet_connection.send_command("Telnet connection established.")
            #Syslog message is not being printed for security reasons
    
    #Prints an error message in string
    except Exception as e:    
        print(f"Error: {str(e)}")
            

def hostname_change(router_infoo):
    
    #New hostname from the user
    new_hostname = input("Enter new hostname: ")
#while true is a loop and will stop when the condition is met 
    while True:
        print("\n Change Hostname Menu: ")
        print("1. Change hostname with SSH ")
        print("2. Return to main menu")
        print("0. Exit")

        choice = input("Enter your choice: ")
#gives option for 1 
        if choice == '1':
            ssh(new_hostname) #calls the ssh() function with new hostname as argument
        elif  choice == '2':
            break             # if the first condition is false check for other options 
        elif choice == '0':
            print('Exiting {new_hostname}.')
            exit()
        else:
            print("Invalid. Choose again") #lets user known their input was invalid and prompts them to choose again 

def grab_router_config(router_infoo): #function 
    try:
        #Establish SSH connection for config files
        with ConnectHandler(**router_infoo) as ssh_connection: 
            #Enter enable mode / router_infoo is a input 
            ssh_connection.enable() #inside the function 

            #Grab running config
            output = ssh_connection.send_command("show running-config") #retriveves configuration 

            return output 

    except Exception as e:
        print(f"Error!: {str(e)}")    #error handling if any error its caught in the except block 
        #and you are given an error 

#Compares the running config to cisco hardening advice
def config_hardening_compare(device_config, hardening_advice): #function 
    #Difflib compares the config to hardening advice
    d = difflib.Differ()
    diff = list(d.compare(device_config.splitlines(), hardening_advice.splitlines())) 
    #deivce_config is a string representing the router hardening_advice also a string 

    #prints differences
    print("\n".join(diff)) #output The differences between the device /
    #configuration and the hardening advice are printed out line by line.


def syslog_config(router_infoo): # function that sets up logging to a file and establishes an SSH connection to a router to configure syslog.
    try:   #Input: It takes a single argument router_infoo, is a dictionary containing the connection details for the router  IP, username, password).
        #Logging to a file
        syslog_file_handler = FileHandler('syslog_events_monitoring.txt')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(messages)s')
        syslog_file_handler.setFormatter(formatter)

        logger = logging.getLogger()
        logger.addHandler(syslog_file_handler)
        logger.setLevel(logging.INFO)

        #Establish SSH connection
        with ConnectHandler(**router_infoo) as ssh_connection:
            #Enter enable mode
            ssh_connection.enable() #The enable()) method is called to enter privileged mode on the router.

#This function configures logging to a file and establishes an SSH connection to a router to enable syslog configuration.
            event_log_commands = [
                'logging buffered 4096', #Overwriting will occur after 50 messages logged
                'logging console warning', #Logs commands entered in console 
                'logging monitor warning', #Alerts if the systems performance or health is affected
                'logging trap notifcations', #Limits messages logged to file
            ]
            ssh_connection.send_config_set(event_log_commands)
# sends the list of event logging commands to the router, applying the configurations for event logging.

            #Log syslog message for event log configuration
            ssh_connection.send_command("Logging syslog, event logging configured. ")
            # Syslog message not printed to console for security measures
    except Exception as e:
        print(f"Error!: {str(e)}") #If an error occurs during the SSH connection or command execution,
        #it is caught by the except block, and an error message is printed.


def acl_list(router_infoo, acl_file): #function 
    ## Connect to the router using SSH with the provided connection details (router_infoo)
    with ConnectHandler(**router_infoo) as ssh_connection:
        ## Enter privileged (enable) mode on the router to issue configuration commands
        ssh_connection.enable()


        #Read ACL config from file
        with open(acl_file, 'r') as file:
            acl_config = file.read().splitlines()

        #Send config command to the router
        output = ssh_connection.send_confifg_set(acl_config)

        #Show file configuration of who has access and thier privellage
        print(output)

def ipsec_config(router_infoo, isakmp_policy, crypto_map, shared_key):
    #connect to device
    with ConnectHandler(**router_infoo) as ssh_connection:
        #Enter enable mode
        ssh_connection.enable
  # Build ISAKMP configuration string with the provided policy and parameters
        isakmp_config = f"crypto isakmp policy {isakmp_policy}\n" \
                        "encryption aes-256\n" \
                        "hash sha256\n" \
                        "authentication pre-share\n" \
                        f"group 14\n" \
                        f"lifetime 28800\n" \
        
                # Configure the pre-shared key for ISAKMP (used in IPsec)
        shared_key_config =  f"crypto isakmp key {shared_key} address 192.168.56.101\n"

        #Config crypto mapping
        crypto_map_config = f"crypto map {crypto_map} 10 ipsec-isakmp" \
                            "set peer 0.0.0.0\n" \
                            f"set transform-set myset\n" \
                            "match address 100\n"
        
        # Send all IPsec configuration commands to the router at once
        output = ssh_connection.send_config_set([isakmp_config, shared_key_config, crypto_map_config])

        print(output)

#Main menu
while True:
    print("\n Main Menu: ")
    print("1. Change_Hostname_now")
    print("2. Establish_SSH_Connection_ ")
    print("3. Establish_Telnet_Connection_")
    print("4. retrieve_running_configuration")
    print("5. Compare_running_configuration_with_Cisco_Hardening_Advice")
    print("6. Configure_event_logging_will_redirect")
    print("7. Does_Access_Control_from_list")
    print("8.IP_security")
    print("0. Exiting")

    main_choice = input("Enter your choice: ")

    if main_choice == '1':
        hostname_change(router_info) #host name(the yellow text) is the function and router is the variable 
    elif main_choice == '2':
        ssh(router_info)
    elif main_choice == '3':
        telnet(router_info, "")
    elif main_choice == '4':
        device_config = grab_router_config(router_info)
        print("Running Configuration now:\n", device_config)
    elif main_choice == '5':
        config_hardening_compare(device_config,hardening_advice)
    elif main_choice == '6':
        syslog_config(router_info)
    elif main_choice == '7':
       acl_list(router_info, acl_list) 
    elif main_choice == '8':
        ipsec_config(router_info,isakmp_policy,crypto_map,shared_key)
    elif main_choice == '0':
        print("Exiting router now.")
        exit()
    else:
        print("Invalid choose")

    #s22153423