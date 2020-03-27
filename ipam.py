import json
import os

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def getAllIPAMARecords(url, InfoBlox_User, InfoBlox_Password):
    #
    #############
    #  GET ALL IPAM RECORD:A Entries (not HOSTRECORD ENTRIES)
    #############
    #
    ipmapping = []
    Arecords = requests.get(url + 'record:a?_max_results=100000', auth=(InfoBlox_User, InfoBlox_Password),
                     verify=False, headers={'Accept': 'application/json'}).json()
    for arecord in Arecords:
        ipaddr = arecord['ipv4addr']
        name = arecord['name']
        ipmapping.append({ipaddr: name})
    return ipmapping


def getAllIPAMHostRecords(url, InfoBlox_User, InfoBlox_Password):
    #
    #############
    #  GET ALL IPAM RECORD:HOST Entries (not DNS 'A' RECORD ENTRIES)
    #############
    #
    ipmapping = []
    hostrecords = requests.get(url + 'record:host?_max_results=100000', auth=(InfoBlox_User, InfoBlox_Password),
                     verify=False, headers={'Accept': 'application/json'}).json()
    for arecord in hostrecords:
        for ipv4addr in arecord['ipv4addrs']:
            ipaddr = ipv4addr['ipv4addr']
            name = ipv4addr['host']
            ipmapping.append({ipaddr: name})
    return ipmapping
    #
    '''
    ipmapping = []
    ipmapping = [ {ip: host1}, {ip: host55}, {ip2:host2}, {ip3: host3}...]
    ipmapping = { ip:host, ip2:host2, ip3:host3, ...}
    '''
    # print(type(hostrecords), hostrecords)
    # print(hostrecords['ipv4addrs'][0])
    # for arecord in hostrecords['ipv4addrs']:
    #     print(hostrecords['ipv4addrs'][arecord]['host'], hostrecords['ipv4addrs'][arecord]['ipv4addrs'])
    # print(hostrecords.json())
    #
    # bubba = [
    # {
    #     '_ref': 'record:host/xxxxxxxxxxxxxxx'
    #     'ipv4addrs': [
    #         {
    #             '_ref': 'record:host_ipv4addr/xxxxxxxxxxxxxxx'
    #             'configure_for_dhcp': False,
    #             'host': 'hpe-future',
    #             'ipv4addr': 'x.x.x.x'
    #         },
    #              'host':'hpe2'
    #               'ipv4addr': '1.1.1.1'
    #     ],
    #     'name': 'hpe-future',
    #     'view': ' '
    # },
    # {
    #     '_ref': 'record:host/xxxxxxxxxxxxxxx'
    #     'ipv4addrs': [
    #       {
    #         '_ref': 'record:host_ipv4addr/xxxxxxxxxxxxxxx'
    #         'configure_for_dhcp': False,
    #         'host': 'hpe-future',
    #         'ipv4addr': 'x.x.x.x'
    #       }
    #     ],
    #     'name': 'hpe-future',
    #     'view': ' '
    # }
    #   ]
    #


def getallIPAMrecords(url, InfoBlox_User, InfoBlox_Password, zone):
    #
    #############
    #  GET IPAM RECORDS of EVERY TYPE
    #############
    #
    allrecords = requests.get(url + 'allrecords?zone=' + zone + '&_max_results=1000000&_return_as_object=1',
                              auth=(InfoBlox_User, InfoBlox_Password),
                              verify=False, headers={'Accept': 'application/json'})
    return allrecords.json()


def AddIPAMHostRecord(url, InfoBlox_User, InfoBlox_Password, addresslist):
    #
    #############
    #  ADD AN IPAM HOSTRECORD (not a DNS 'A' RECORD)
    #############
    #
    # new_addrs = {'x.x.x.x': 'fsw100-408-31-',
    #              'x.x.x.x': 'fsw100-408-30-',
    #              'x.x.x.x': 'fsw100-408-29-',
    #              'x.x.x.x': 'fg2500e-408-27-',
    #              'x.x.x.x': 'fwifi60-408-24-',
    #              'x.x.x.x': 'fwifi60-408-23-',
    #              'x.x.x.x': 'fwifi60-408-22-',
    #              'x.x.x.x': 'fg2000mgr-408-20-',
    #              'x.x.x.x': 'fwifi60-408-17-',
    #              'x.x.x.x': 'fwifi60-408-16-',
    #              'x.x.x.x': 'fsw100-408-15-',
    #              'x.x.x.x': 'fsw100-408-14-',
    #              'x.x.x.x': 'fsw124e-poe-408-13-',
    #              'x.x.x.x': 'fgAP-408-10-',
    #              }
    #
    for addr in addresslist:
        data = {
            "name": addresslist[addr],
            "network_view": "default",
            "configure_for_dns": False,
            "ipv4addrs": [
                {
                    "ipv4addr": addr
                }
            ]
        }
        postToInfoBlox = requests.post(url + 'record:host',
                                auth = (InfoBlox_User, InfoBlox_Password),
                                verify=False,
                                headers={'Content-type': 'application/json', 'Accept': 'application/json'},
                                data=json.dumps(data))
        print(postToInfoBlox.status_code)
        print(postToInfoBlox.json())
        print("\n\n", postToInfoBlox.text)



def DeleteIPAMIPv4HostRecord(url, InfoBlox_User, InfoBlox_Password, addresslist):
    #
    #############
    #  DELETE AN IPAM RECORD
    #############
    #
    NameToIPv4addrMapping = requests.get(url + 'record:host?ipv4addr=' + ipaddr,
                                         auth=(InfoBlox_User, InfoBlox_Password),
                                         verify=False,
                                         headers={'Content-type': 'application/json', 'Accept': 'application/json'}).json()

    print("now removing the 'reserve' entry", url + NameToIPv4addrMapping[0]['_ref'])
    if len(NameToIPv4addrMapping) == 1:
        delrequest = requests.delete(url + NameToIPv4addrMapping[0]['_ref'],
                      auth=(InfoBlox_User, InfoBlox_Password),
                      verify=False,
                      headers={'Content-type': 'application/json', 'Accept': 'application/json'})
        print(delrequest.status_code)
        print(delrequest.json())
        print("\n\n", delrequest.text)


'''
Extra stuff I shouldn't need anymore

        ipv4addrs = requests.get(url + 'record:host_ipv4addr?_return_fields=ipv4addr,host',
                                 auth = (InfoBlox_User, InfoBlox_Password),
                                 verify=False,
                                 headers={'Content-type': 'application/json', 'Accept': 'application/json'})
        for record in ipv4addrs.json():
            print(record['host'], record['ipv4addr'])
        
        
        print("host_ipv4addr = ", ipv4addrs.json())
        
        specific_host = requests.get(url + 'record:host?ipv4addr=' + ipaddr,
                                     auth=(InfoBlox_User, InfoBlox_Password),
                                     verify=False,
                                     headers={'Content-type': 'application/json', 'Accept': 'application/json'})
        print("info for ", ipaddr, " is ", specific_host.json())
        
        
        schema = requests.get(url + '?_schema=1', auth = (InfoBlox_User, InfoBlox_Password),
                         verify=False, headers={'Accept': 'application/json'})
        print(schema.json())
        
        
        
        arecords = requests.get(url + 'record:a', auth = (InfoBlox_User, InfoBlox_Password),
                         verify=False, headers={'Accept': 'application/json'})
        print(arecords.json())
        
        ipv4 = requests.get(url + 'record:host?ipv4addr=10.34.144.114', auth = (InfoBlox_User, InfoBlox_Password),
                         verify=False, headers={'Accept': 'application/json'})
        print(ipv4.json())
'''

if __name__ == "__main__":
    InfoBlox_IP = "x.x.x.x"
    InfoBlox_User = "swinters"
    zone = "xxxx.local"
    url = 'https://' + InfoBlox_IP + '/wapi/v2.9/'
    pwdfile = '.pwd'
    pwdfile = os.path.join(os.getenv('HOME'), pwdfile)
    if os.path.exists(pwdfile):
        with open(pwdfile) as f:
            InfoBlox_Password = f.readline().rstrip()
    else:
        print("couldn't find password file")
        exit()

    # allArecords = getallIPAMArecords(url, InfoBlox_User, InfoBlox_Password)
    # print(allArecords)

    allHostrecords = getAllIPAMHostRecords(url, InfoBlox_User, InfoBlox_Password)
    print(json.dumps(allHostrecords))

    allArecords = getAllIPAMARecords(url, InfoBlox_User, InfoBlox_Password)
    print(allArecords)

    # allrecords = getallIPAMrecords(url, InfoBlox_User, InfoBlox_Password, zone)
    # print(allrecords)
