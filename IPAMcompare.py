import xlrd
import os
import re
import xlsxwriter
import json
import time

import ipam

'''
single purpose code to compare IP address assignments from 
spreadsheets versus IPAM data

this is ugly code. it's one-and-done code
this is expected to be run maybe a few times, but not on a consistent basis....this is why 
there are no try/except's here

the output is an xlsx format spreadsheet with the following details:
Each column maps to a network that is defined in a spreadsheet from google drive

The results were created and can be recreated by following the process below:
•       Manually copied all google drive xls spreadsheets to a shared folder
        (shared local folder between Mac host and Mac VM)
•       Copied address/host specific block from “x.x.x.x – Virtual Server Network”
        to “x.x.x.x Virtual Server Network IP Adresss Only” and then
        deleted “x.x.x.x Virtual Server Network”
•       Deleted from shared folder
•       Run this script (updated on github)
'''


#
###############################################################################
# define InfoBlox (IPAM) login parameters                                     #
###############################################################################
#
InfoBlox_IP = "x.x.x.x"
InfoBlox_User = "swinters"
zone = "xxxxx.local"
url = 'https://' + InfoBlox_IP + '/wapi/v2.9/'
pwdfile = '.pwd'
pwdfile = os.path.join(os.getenv('HOME'), pwdfile)
if os.path.exists(pwdfile):
    with open(pwdfile) as f:
        InfoBlox_Password = f.readline().rstrip()
else:
    print("couldn't find password file")
    exit()


#
###############################################################################
# get all IPAM 'A' records                                                    #
###############################################################################
#
allArecords = ipam.getAllIPAMARecords(url, InfoBlox_User, InfoBlox_Password)
print("allArecords: ", allArecords)


#
###############################################################################
# get all IPAM 'host' records                                                 #
###############################################################################
#
allHostrecords = ipam.getAllIPAMHostRecords(url, InfoBlox_User, InfoBlox_Password)
print("allHostRecords: ", allHostrecords)


#
###############################################################################
# get IP and hostname mapping info from all spreadsheets in the shared folder #
###############################################################################
#
DriveFilesDir = "/Users/swinters/Downloads/Shared_Folder/IPAMCorrelate/google-drive-spreadsheets/"
resultfile = 'comparisonresults.xlsx'
drivefiles = os.listdir(DriveFilesDir)
spreadsheetNetworkIPs = {}
for afile in drivefiles:
    column = 0
    arow = 1
    if not afile.startswith('.') and afile != resultfile:
        # print("afile is: ", afile)
        match = re.search(r"(\d+.\d+\.\d+\.\d+)", afile)
        network = match.group(1)
        spreadsheetNetworkIPs[network] = []
        # print("Spreadsheet file IP network is: ", afile)
        wb = xlrd.open_workbook(DriveFilesDir + afile)
        sheet = wb.sheet_by_index(0)
        #
        # identify the columns in the header line (row 0) and
        # find the columns that match "Host" and "Address"
        #
        while column < sheet.ncols:
            if 'ddress' in sheet.cell_value(0, column).casefold():
                addrColumn = column
            if 'host' in sheet.cell_value(0, column).casefold():
                hostCol = column
            column += 1
        ipmap = []
        while arow < sheet.nrows:
            ipaddr = sheet.cell_value(arow, addrColumn)
            hostname = sheet.cell_value(arow, hostCol)
            # print(ipaddr, hostname)
            if len(ipaddr) > 0:
                ipmap.append([ipaddr, hostname])
                spreadsheetNetworkIPs[network].append([ipaddr, hostname])
            arow += 1
print("Spreadsheet records: ", json.dumps(spreadsheetNetworkIPs))

#
###############################################################################
# Create a workbook and add a worksheet.                                      #
###############################################################################
#
workbook = xlsxwriter.Workbook(DriveFilesDir + resultfile)
worksheet = workbook.add_worksheet()
bold = workbook.add_format({'bold': True})
red = workbook.add_format({'bg_color': '#FF0000'})
yellow = workbook.add_format({'bg_color': '#FFFF00'})
darkkhaki = workbook.add_format({'bg_color': '#BDB76B'})
darkgray = workbook.add_format({'bg_color': '#A9A9A9'})
lightgreen = workbook.add_format({'bg_color': '#ADFF2F'})
green = workbook.add_format({'bg_color': '#008000'})
blueviolet = workbook.add_format({'bg_color': '#8A2BE2'})


#
################################################################################
# do the comparison                                                            #
################################################################################
#
# for every spreadsheet found, create a column header of that network in the resultant comparison data spreadsheet
#   for every IP in that spreadsheet:
#       if that IP has a Hostname entry in the spreadsheet:
#           color the cell blueviolet if it's an IPAM host record
#           color the cell light green if it's an IPAM DNS A record
#           color the cell light red if there's no entry in IPAM
#       else (this means that there's no associated Hostname for that IP in the spreadsheet):
#           color the cell darkgray if there IS a hostrecord entry in IPAM
#           color the cell darkkhaki if there IS an IPAM A record entry
#           color the cell transparent if similarly no entry in IPAM (i.e., spreadsheets are in sync with IPAM)
#
count = 0
for network in spreadsheetNetworkIPs:
    row = 0
    worksheet.write(row, count, network, bold)
    print("comparing network: ", network)
    for ip in spreadsheetNetworkIPs[network]:
        if ip[1]:
            print("hostname WAS found in spreadsheet for ip: ", ip[0], ip[1])
            amatch = False
            row += 1
            for hostrecord in allHostrecords:
                for ahost in hostrecord:
                    # print("IP from IPAM hostrecord is ", ahost, "and ip from spreadsheet is: ", ip[0])
                    # time.sleep(.5)
                    if ip[0] == ahost:
                        # print("hostrecord IP ", ahost, ' matches spreadsheet IP', ip[0], "background blueviolet")
                        amatch = True
                        worksheet.write(row, count, ip[0] + ' host:record', green)
                        break
                if not amatch:
                    for arecord in allArecords:
                        for arecordhost in arecord.keys():
                            # print("IP from IPAM A record is ", arecordhost, "and ip from spreadsheet is: ", ip[0])
                            # time.sleep(.5)
                            if ip[0] == arecordhost:
                                print("A record IP ", arecordhost, ' matches spreadsheet IP', ip[0], "background green")
                                amatch = True
                                worksheet.write(row, count, ip[0] + ' A:Record', green)
                                break
            if not amatch:
                print("notamatch arecord or hostrecord hostname found in spreadsheet for", ip[0], ip[1])
                worksheet.write(row, count, ip[0], red)
        else:
            print("hostname NOT found in spreadsheet for ip: ", ip[0], ip[1])
            amatch = False
            row += 1
            for hostrecord in allHostrecords:
                for ahost in hostrecord:
                    # print("IP from IPAM hostrecord is ", ahost, "and ip from spreadsheet is: ", ip[0])
                    # time.sleep(.5)
                    if ip[0] == ahost:
                        # print("hostrecord IP ", ahost, ' matches spreadsheet IP', ip[0], "background darkgray")
                        amatch = True
                        worksheet.write(row, count, ip[0] + ' host:record', yellow)
                        break
                if not amatch:
                    for arecord in allArecords:
                        for arecordhost in arecord.keys():
                            # print("IP from IPAM A record is ", arecordhost, "and ip from spreadsheet is: ", ip[0])
                            # time.sleep(.5)
                            if ip[0] == arecordhost:
                                amatch = True
                                worksheet.write(row, count, ip[0] + ' A:Record', yellow)
                                break
            if not amatch:
                print("notamatch A record or hostrecord, hostname not found in spreadsheet for: ", ip[0], ip[1])
                # worksheet.write(row, count, ip[0])
    count += 1

workbook.close()
