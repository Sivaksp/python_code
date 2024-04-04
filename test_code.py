#!/python38-env/bin/python

DESCRIPTION="This script sends email to the groups which has not approved the changes"
BUG_REPORT_EMAIL=""

######################################################################
# Author - 
######################################################################

import apikeys3
import json
import requests
import time
import sys
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse
import subprocess
import pytz
import getpass
import textwrap
import os
from termcolor import colored


custom_help = """
This Script sends communication for approvals on pending changes to the groups which are yet to approve

Usage:  mail_to_approvers.py -g unix-support-tr
        mail_to_approvers.py -g storage-support-tr
or
Usage:  mail_to_approvers.py -c <pending change request>
        mail_to_approvers.py -c CHG123456

* * * NOTE : do not input both -g and -c

Options:
  -g, for group name
  -c, for change request
"""
print()

parser = argparse.ArgumentParser(description='This Script sends communication for approvals on pending changes to the groups which are yet to approve')

# Define the arguments you want to accept
parser.add_argument('-g', '--group', metavar='GROUP_NAME', help='Send email to all the unapproved groups')
parser.add_argument('-c', '--change', metavar='change_number', help='Send email to all the unapproved groups')

print
args = parser.parse_args()

# Check if the advisory argument is provided
if not (args.group or args.change):
    print(custom_help)
    parser.print_usage()
    sys.exit(1)


# Setting proxy since SN is not reachable from bacon.
http_proxy = "http://webproxy.e.corp.services:80"
https_proxy = "http://webproxy.e.corp.services:80"
proxyDict = {"http" : http_proxy, "https" : https_proxy}

payload = {}
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-access-token'  # Replace with your API token or authorization method
}

existing = []
sent = []

def cred(url):

    active_response = requests.get(url, auth=(apikeys3.snow_usr, apikeys3.snow_pwd), headers=headers, proxies=proxyDict)
    active_data = active_response.json()
    return active_data

def validate_change(change):
    url = "https://thomsonreuters.service-now.com/api/now/table/change_request?sysparm_query=number%3D" + change + "&sysparm_display_value=true&sysparm_exclu
de_reference_link=true"
    data = cred(url)['result']

    if data:
        if data[0]['state'] == 'Approval':
            return data
        else:
            print(f"{change} is in {data[0]['state']} state")
            sys.exit(1)
    else:
        print("Change request not found. Enter correct number")
        sys.exit(1)

def send_mail(sender_email, receiver_email, cc_email, subject, main_body, signature, change, difference):

    # Append the signature to the body
    body_with_signature = f"{main_body}\n\n{signature}"
    # Construct the mailx command
    mailx_command = f"echo '{body_with_signature}' | mailx -s '{subject}' -S smtp=relay.mgmt.services -r {sender_email}"

    if cc_email:
        # Join multiple email addresses with commas and include them in the -c option
        cc_emails = ",".join(cc_email)
        mailx_command += f" -c {cc_emails}"

    if receiver_email:
        receiver_emails = "".join(receiver_email)
        mailx_command += f" {receiver_emails}"

    #print(mailx_command)

    file_path = "/infra_unixsvcs/unix-support/do_not_delete_mail_to_approvers"
    found = False
    if not os.path.exists(file_path):
        # If the file doesn't exist, create it and write some initial content
        with open(file_path, 'w') as file:
            # Perform any necessary operations here
            pass

    with open(file_path, 'r') as file:
        for line in file:
            if line.strip() == change:
                #print(f"{change} - Mail already existing. Please followup with the same mail with {receiver_emails}")
                existing.append(f"{change} - Starting in {difference} hours - Pending groups {receiver_emails},{cc_emails}")
                found = True
                break

    # If the search text is not found, append it to the file
    if not found:
        with open(file_path, 'a') as file:
            #print(f"{change} - Sending approval mail to {receiver_emails}")
            # Execute the mailx command using subprocess
            try:
                subprocess.run(mailx_command, shell=True, check=True)
                #print("Email sent successfully!")
                #print(mailx_command)
            except subprocess.CalledProcessError as e:
                print(f"Error sending email: {e}")
            sent.append(f"{change} - Sending approval mail to {receiver_emails}")
            # Append the search text to the file in a new line
            file.write("\n" + change)


    """
    # Execute the mailx command using subprocess
    try:
        subprocess.run(mailx_command, shell=True, check=True)
        print("Email sent successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error sending email: {e}")
    """

"""
# Function to check if a given date and time is ahead of 5 hours from the current time
def time_difference_old(given_time_str):
    # Convert the given time string to a datetime object
    given_time = datetime.strptime(given_time_str, "%Y-%m-%d %H:%M:%S")

    # Get the current time
    current_time = datetime.now()
    # Calculate the time difference
    time_diff = given_time - current_time
    return time_diff

def time_difference(given_time_str):
    given_time = datetime.strptime(given_time_str, "%Y-%m-%d %H:%M:%S")
    # Run the date +%Z command to get the timezone abbreviation
    process = subprocess.Popen(['date', '+%Z'], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    # Decode the output and strip any leading/trailing whitespace
    timezone_abbr = output.decode().strip()
    # Define a mapping of ambiguous timezone abbreviations to their corresponding timezones
    timezone_mapping = {
        'CST': 'America/Chicago',  # Central Standard Time
        # Add more mappings as needed for other ambiguous abbreviations
    }
    # Get the timezone corresponding to the abbreviation
    timezone = timezone_mapping.get(timezone_abbr)
    if timezone:
        # Get the current time in the obtained timezone
        current_time = datetime.now(pytz.timezone(timezone))
        # Convert the obtained time to GMT
        current_time_gmt = current_time.astimezone(pytz.utc)
        current_time_gmt = current_time_gmt.strftime("%Y-%m-%d %H:%M:%S")
        current_time_gmt = datetime.strptime(current_time_gmt, "%Y-%m-%d %H:%M:%S")

    else:
        print("Unknown timezone abbreviation:", timezone_abbr)

    time_diff = given_time - current_time_gmt
    time_diff_seconds = time_diff.total_seconds()/3600
    time_diff_rounded = round(time_diff_seconds)
    return time_diff_rounded

"""

def time_difference(given_time_str):
    # Get the current time in GMT
    given_time = datetime.strptime(given_time_str, "%Y-%m-%d %H:%M:%S")
    current_time_gmt = datetime.now(pytz.utc)

    # Format the current time in GMT to the desired format
    current_time_gmt_formatted = current_time_gmt.strftime("%Y-%m-%d %H:%M:%S")

    # Convert current_time_gmt_formatted back to a datetime object
    current_time_gmt_formatted = datetime.strptime(current_time_gmt_formatted, "%Y-%m-%d %H:%M:%S")

    time_diff = given_time - current_time_gmt_formatted
    time_diff_seconds = time_diff.total_seconds()/3600
    time_diff_rounded = round(time_diff_seconds)
    return time_diff_rounded

def get_pending_group(change):
    pending_teams = []
    pending_teams_url = "https://thomsonreuters.service-now.com/api/now/table/sysapproval_group?sysparm_query=parent.number=" + change + "&sysparm_display_va
lue=true&sysparm_exclude_reference_link=true&sysparm_fields=approval%2Cassignment_group"
    response = cred(pending_teams_url)['result']
    for i in range(len(response)):
        if response[i]['approval'] == 'Requested':
            pending_teams.append(response[i]['assignment_group'])
            status = "Change not in pending state"
    return pending_teams if pending_teams else status

def get_team_contacts(team):
    contacts_url = "https://thomsonreuters.service-now.com/api/now/table/sys_user_group?sysparm_query=name=" + team + "&sysparm_display_value=true&sysparm_ex
clude_reference_link=true"
    response = cred(contacts_url)['result']

    mananger_email = ''
    lead_contact_list = []
    lead_email_list = []

    for i in range(len(response)):
        team_email = response[i]['email']
        lead_contact = response[i]['u_team_lead_list']
        manager = response[i]['manager']

        if not lead_contact:
            lead_contact_list = []  # Empty list for blank lead_contact
        elif ',' in lead_contact:
        # Split the string by commas and strip whitespaces
            lead_contact_list = [contact.strip() for contact in lead_contact.split(',')]
        else:
            lead_contact_list = [lead_contact.strip()]
        # Getting the emails of the Lead contacts
        if lead_contact_list:
            for name in lead_contact_list:
                lead_email_url = "https://thomsonreuters.service-now.com/api/now/table/sys_user?sysparm_query=name%3D"+ name + "&sysparm_display_value=true&s
ysparm_exclude_reference_link=true&sysparm_limit=1"
                # Checking if name is email
                if '@' in name:
                    lead_email_list.append(name)
                else:
                    data = cred(lead_email_url)['result']
                    if data:
                        lead_email_list.append(data[0]['email'])
        if manager:
            lead_email_url = "https://thomsonreuters.service-now.com/api/now/table/sys_user?sysparm_query=name%3D"+ manager + "&sysparm_display_value=true&sy
sparm_exclude_reference_link=true&sysparm_limit=1"
            data = cred(lead_email_url)['result']
            mananger_email += data[0]['email']

    return team_email, lead_email_list, mananger_email


def get_user_details(id):
    url = "https://thomsonreuters.service-now.com/api/now/table/sys_user?employee_number="+ id + "&sysparm_view=&sysparm_display_value=true&sysparm_exclude_r
eference_link=true"
    name = cred(url)['result'][0]['name']
    my_email = cred(url)['result'][0]['email']
    title = cred(url)['result'][0]['title']
    department = cred(url)['result'][0]['department']
    company = cred(url)['result'][0]['company']
    mobile_phone = cred(url)['result'][0]['mobile_phone']

    if name:
        return name, my_email, title, department, company, mobile_phone
    else:
        return None

def get_user_group(name):
    url = "https://thomsonreuters.service-now.com/api/now/table/sys_user_grmember?sysparm_query=user.name="+ name +"&sysparm_display_value=true&sysparm_exclu
de_reference_link=true&sysparm_fields=sys_mod_count%2Cgroup"

    user_groups = []
    data = cred(url)['result']
    if data:
        # Iterate over each result object
        for result in data:
            user_groups.append(result["group"])
        return user_groups

"""
def get_user_group(name):
    url = "https://thomsonreuters.service-now.com/api/now/table/sys_user_grmember?sysparm_query=user.name="+ name +"&sysparm_display_value=true&sysparm_exclu
de_reference_link=true&sysparm_fields=sys_mod_count%2Cgroup"

    data = cred(url)['result']
    if data:
        max_sys_mod_count = 0
        max_sys_mod_count_group = None

        # Iterate over each result object
        for result in data:
            sys_mod_count_str = result["sys_mod_count"]
            group_name = result["group"]

            # Remove comma if it exists in sys_mod_count_str
            if "," in sys_mod_count_str:
                sys_mod_count_str = sys_mod_count_str.replace(",", "")

            # Convert sys_mod_count_str to integer
            sys_mod_count = int(sys_mod_count_str)

            # Check if sys_mod_count is greater than the current maximum
            if sys_mod_count > max_sys_mod_count:
                max_sys_mod_count = sys_mod_count
                max_sys_mod_count_group = group_name

        return max_sys_mod_count_group
"""
def friday():
    # Set the timezone to GMT
    gmt = pytz.timezone('GMT')

    # Get the current time in GMT timezone
    current_time = datetime.now(gmt)

    # Check if it is Friday (weekday number 4) and the time is between 10 am and 8 pm
    if current_time.weekday() == 4 and 1 <= current_time.hour < 15:
        #print(current_time.weekday())
        return True
    else:
        #print(current_time.weekday())
        return False

def monday():
    # Set the timezone to GMT
    gmt = pytz.timezone('GMT')
    # Get the current time in GMT timezone
    current_time = datetime.now(gmt)

    # Check if it is Monday (weekday number 0) and the time is between 10 am and 8 pm
    if current_time.weekday() == 0 and 1 <= current_time.hour < 15:
        #print(current_time.weekday())
        return True
    else:
        #print(current_time.weekday())
        return False

def remove_lines_with_condition(file_path):
    def condition(line):
        change_number = line.strip()
        if not change_number:
            return True
        url = f"https://thomsonreuters.service-now.com/api/now/table/change_request?sysparm_query=number%3D{change_number}&sysparm_display_value=true&sysparm
_exclude_reference_link=true"
        data = cred(url)['result']
        if data:
            for i in range(len(data)):
                status = data[i]['state']
                if status in ('Closed', 'Cancelled'):
                    return True  # Remove line if change is closed or cancelled
        return False

    # Read the contents of the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Remove lines that meet the condition (including empty lines)
    modified_lines = [line for line in lines if not condition(line.strip())]

    # Write the modified contents back to the file
    with open(file_path, 'w') as file:
        file.writelines(modified_lines)

if __name__ == "__main__":

    try:

        username = getpass.getuser()
        if not username.startswith('m'):
            print("You are supposed to run the script with your m-account but not with %s" % username)
            sys.exit(1)
        id = username[1:]
        name, my_email, title, department, company, mobile_phone = get_user_details(id)
        #print(name,my_email, title, department, company, mobile_phone)
        """
        my_group = get_user_group(name).upper()
        #print(my_group)
        my_group_email, lead_contact, manager_email = get_team_contacts(my_group)
        #print(f"This is my gorup email  ******** {my_group_email}")
        """
        condition_met = False


        if name is None:
            print("You are supposed to the script only by logging with your M-account")
            sys.exit(1)

        else:
            if args.group:
                group_name = args.group.upper()
                cc_email = []
                team_emails = ""

                my_groups = get_user_group(name)
                if group_name in my_groups:
                    group_name = group_name
                    my_group_email, lead_contact, manager_email = get_team_contacts(group_name)

                    signature = textwrap.dedent(f"""
                    {name}
                    {title}
                    {group_name}
                    {department}
                    {company}
                    {mobile_phone}
                    Escalation Information:
                    https://trten.sharepoint.com/sites/intr-plat-eng/SitePages/IHN-Contact-%26-Escalation(1).aspx
                    """)

                    unapproved_url = "https://thomsonreuters.service-now.com/api/now/table/change_request?sysparm_query=assignment_group.name%3D" + group_nam
e + "%5Eactive%3Dtrue%5EORactive%3Dfalse%5EstateIN6&sysparm_fields=number%2Ccmdb_ci%2Cstate%2Cstart_date%2Cshort_description"
                    data = cred(unapproved_url)['result']
                    if data:
                        print(f"{len(data)} changes found in pending approval state\n")
                        print(f"Following up only with the changes which start in next 48 hours\n")

                        for i in range(len(data)):
                            change_number = data[i]['number']
                            start_date = data[i]['start_date']
                            short_desc = data[i]['short_description']
                            subject = f"* * * Approval reminder for {change_number} - {short_desc}"
                            difference  = time_difference(start_date)
                            teams = get_pending_group(change_number)
                            change_url = f"https://thomsonreuters.service-now.com/change_request.do?sysparm_query=number={change_number}"
                            all_teams = ""

                            all_team_emails = ""
                            all_lead_emails = []
                            all_manager_emails = []
                            cc_email += [my_group_email]

                            for team in teams:
                                if team == 'AMS-NOVUS':
                                    all_team_emails += "platformoperationschangeMgmt@thomsonreuters.com" + ","
                                if team == 'APP-OPS-ASE-LEGALSERVICES':
                                    all_team_emails +=  "tr-app-ops-changecoordinators@thomsonreuters.com" + ","

                                all_teams += team + ", "

                                team_email, lead_email, manager_email = get_team_contacts(team)

                                all_team_emails += team_email + ","
                                all_lead_emails.extend(lead_email)
                                all_manager_emails.append(manager_email)

                            all_team_emails = all_team_emails.rstrip(",")
                            main_body = f"Hi {all_teams} \n\n{change_number} is going to start in {difference} hours. Do review and approve it at the earlies
t.\n\n\n{change_url}\n"

                            if difference <= 5:

                                cc_email += all_lead_emails
                                cc_email += all_manager_emails
                                cc_email = list(set(cc_email))
                                send_mail(my_email, all_team_emails, cc_email, subject, main_body, signature, change_number, difference)

                                cc_email = []
                                all_lead_emails = []
                                all_manager_emails = []
                                condition_met = True

                            elif 5 < difference <= 10:
                                cc_email += all_lead_emails
                                cc_email = list(set(cc_email))
                                send_mail(my_email, all_team_emails, cc_email, subject, main_body, signature, change_number, difference)

                                cc_email = []
                                all_lead_emails = []
                                all_manager_emails = []
                                condition_met = True

                            elif 10 < difference <= 48:
                                cc_email = list(set(cc_email))
                                send_mail(my_email, all_team_emails, cc_email, subject, main_body, signature, change_number, difference)

                                cc_email = []
                                all_lead_emails = []
                                all_manager_emails = []
                                condition_met = True

                            if friday() and 48 < difference <= 96:
                                cc_email = list(set(cc_email))
                                send_mail(my_email, all_team_emails, cc_email, subject, main_body, signature, change_number, difference)

                                cc_email = []
                                all_lead_emails = []
                                all_manager_emails = []
                                condition_met = True


                        if not condition_met:
                            print("No changes in Pending Approval state which are going to start within 48 hours")
                    else:
                        print("No changes found in Pending Approval state or provided Group not found")
                else:
                    print(f"You are not authorized to communicate on {group_name} changes\n")
                    sys.exit(1)


            if args.change:
                my_groups = get_user_group(name)
                change_number = args.change
                data = validate_change(change_number)
                change_owner = data[0]['assignment_group'].upper()
                short_desc = data[0]['short_description']
                subject = f"* * * Approval reminder for {change_number} - {short_desc}"
                change_url = f"https://thomsonreuters.service-now.com/change_request.do?sysparm_query=number={change_number}"
                cc_email = []
                team_emails = ""

                if change_owner in my_groups:

                    group_name = change_owner
                    my_group_email, lead_contact, manager_email = get_team_contacts(group_name)

                    signature = textwrap.dedent(f"""
                    {name}
                    {title}
                    {group_name}
                    {department}
                    {company}
                    {mobile_phone}
                    Escalation Information:
                    https://trten.sharepoint.com/sites/intr-plat-eng/SitePages/IHN-Contact-%26-Escalation(1).aspx
                    """)


                    if data is not None:

                        start_date = data[0]['start_date']
                        #print("start date is " ,start_date)
                        difference  = time_difference(start_date)

                        if data:
                            teams = get_pending_group(change_number)
                            all_teams = ""


                            all_team_emails = ""
                            all_lead_emails = []
                            all_manager_emails = []
                            cc_email += [my_group_email]

                            for team in teams:
                                if team == 'AMS-NOVUS':
                                    all_team_emails += "platformoperationschangeMgmt@thomsonreuters.com" + ","
                                if team == 'APP-OPS-ASE-LEGALSERVICES':
                                    all_team_emails +=  "tr-app-ops-changecoordinators@thomsonreuters.com" + ","

                                all_teams += team + ", "

                                team_email, lead_email, manager_email = get_team_contacts(team)

                                all_team_emails += team_email + ","
                                all_lead_emails.extend(lead_email)
                                all_manager_emails.append(manager_email)

                            all_team_emails = all_team_emails.rstrip(",")
                            main_body = f"Hi {all_teams} \n\n{change_number} is going to start in {difference} hours. Do review and approve it at the earlies
t.\n\n\n{change_url}\n"

                            if difference <= 5:

                                cc_email += all_lead_emails
                                cc_email += all_manager_emails
                                cc_email = list(set(cc_email))
                                send_mail(my_email, all_team_emails, cc_email, subject, main_body, signature, change_number, difference)

                                cc_email = []
                                all_lead_emails = []
                                all_manager_emails = []
                                condition_met = True

                            elif 5 < difference <= 10:
                                cc_email += all_lead_emails
                                cc_email = list(set(cc_email))
                                send_mail(my_email, all_team_emails, cc_email, subject, main_body, signature, change_number, difference)

                                cc_email = []
                                all_lead_emails = []
                                all_manager_emails = []
                                condition_met = True

                            elif 10 < difference <= 200:
                                #cc_email = list(set(cc_email)
                                send_mail(my_email, all_team_emails, cc_email, subject, main_body, signature, change_number, difference)

                                cc_email = []
                                all_lead_emails = []
                                all_manager_emails = []
                                condition_met = True

                            if not condition_met:
                                print(f"{change_number} is not going to start within 24 hours")
                        else:
                            print("Change not found")
                    else:
                        print("Change is not in Approval state")
                else:
                    print(f"You are not authorized to communicate on {change_owner} changes\n")
                    exit()


        if existing:
            print(colored("* * * * Mail existing for below changes. Followup with these pending groups * * * * *\n", 'yellow'))
            for i in existing:
                print(i)

        print()
        print()

        if sent:
            print(colored("* * * * * * * * * Sending mail for below changes * * * * * * * * *\n", 'yellow'))
            for i in sent:
                print(i)

        print()

    except KeyboardInterrupt:
        # Code to be stopped when Ctrl+C is pressed
        print("\nUser interrupt detected. Script execution is stopped\n")

if monday():
    try:
        # Example usage:
        print("\nCleaning the change numbers database file\n")
        file_path = "/infra_unixsvcs/unix-support/do_not_delete_mail_to_approvers"
        if file_path:
            remove_lines_with_condition(file_path)
    except FileNotFoundError:
        print()
