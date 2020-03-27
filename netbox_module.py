import requests
import json


def update_IPAM(netbox_ip, headers, IPv4ToHostList):
    url = "http://" + netbox_ip + "/api/ipam/ip-addresses/"
    for record in IPv4ToHostList:
        print(record['ipv4addr'], record['host'])
        ipv4addr = record['ipv4addr']
        hostname = record['host']
        payload = {
                "family": {
                    "value": '4',
                    "label": "IPv4",
                },
                "address": ipv4addr,
                "dns_name": hostname,
            }
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
        print(response.text.encode('utf8'))

def update_circuits(netbox_ip, headers, CircuitsDict):
    url = "http://" + netbox_ip + "/api/circuits/circuits/"
    for circuit in CircuitsDict:
        desc = CircuitsDict[circuit]
        payload = {
            "cid": circuit,
            "provider": {
                "name": "Vxxxx",
                "slug": "vxxxx"
            },
            "type": {
                "name": "circuit",
                "slug": "circuit"
            },
            "description": desc,
            "tags": [
                "2127"
            ]
        }
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
        print(response.text.encode('utf8'))
    """
    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "cid": "IABLCY0S0001",
                "provider": {
                    "id": 1,
                    "url": "http://localhost:8002/api/circuits/providers/1/",
                    "name": "Vxxxx",
                    "slug": "vxxxx"
                },
                "type": {
                    "id": 1,
                    "url": "http://localhost:8002/api/circuits/circuit-types/1/",
                    "name": "circuit",
                    "slug": "circuit"
                },
                "status": {
                    "value": "active",
                    "label": "Active",
                    "id": 1
                },
                "tenant": null,
                "install_date": null,
                "commit_rate": null,
                "description": "CE-Address: x.x.x.x",
                "termination_a": null,
                "termination_z": null,
                "comments": "",
                "tags": [
                    "2127"
                ],
                "custom_fields": {},
                "created": "2020-02-28",
                "last_updated": "2020-02-28T14:18:16.438028Z"
            }
        ]
    }
    """
def main():

    NETBOX_IP = "localhost:8002"
    NETBOX_TOKEN = "Token xxxx"

    headers = {
        'Authorization': NETBOX_TOKEN,
        'Content-Type': 'application/json'
    }

    # ips = [{'ipv4addr': 'x.x.x.x', 'host': 'bubba'},
    #        {'ipv4addr': 'x.x.x.x', 'host': 'gump'}]
    # update_IPAM(url, headers, ips)

    circuits = {'x.x.x.x': 'circuit description', 'x.x.x.x': 'another description'}
    update_circuits(NETBOX_IP, headers, circuits)

    # pwdfile = '.pwd'
    # pwdfile = os.path.join(os.getenv('HOME'), pwdfile)
    # if os.path.exists(pwdfile):
    #     with open(pwdfile) as f:
    #         APIC_PASS = f.readline().rstrip()
    # else:
    #     print("couldn't find password file")
    #     exit()
    #

if __name__ == "__main__":
    main()

