import json
import os
import re

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#
# TODO: add CLI options for APIC_IP, APIC_USER, APIC_PASSWORD
#       this may be best done as a generic module
#

class vzwACI:
    """
    SWINTERS:
        I lifted this from https://stackoverflow.com/questions/12737740/python-requests-and-persistent-sessions
        but removed a lot of his goodies

        this code is an attempt to create a session OBJECT with basic methods so that we can pass the APIC IP
        into subsequent calls from main versus having to pass the APIC IP in globally or with each method call

        this is hoped to be referenced as an imported module to replace orig_post.py
    """
    def __init__(self, IP, User, Password):
        # urlData = urlparse(loginUrl)
        self.APICIP = IP
        self.loginUser = User
        self.loginPassword = Password
        self.login()

    def login(self, forceLogin = False, **kwargs):
        login_url = "https://" + self.APICIP + "/api/mo/aaaLogin.json"
        payload = {"aaaUser": {"attributes": {"name": self.loginUser, "pwd": self.loginPassword}}}
        self.session = requests.Session()
        post_response = self.session.post(login_url, data=json.dumps(payload), verify=False)
        # print("post_response is ", post_response.json())

    def getNodes(self):
        nodeinfo = self.session.get("https://" + self.APICIP + '/api/node/class/fabricNode.json').json()
        nodes = []
        for anode in nodeinfo['imdata']:
            adn = anode['fabricNode']['attributes']['dn']
            match = re.search(r"topology/pod-1/(.*)", adn)
            nodes.append(match.group(1))
        return sorted(list(dict.fromkeys(nodes)))

    def getTierInfo(self):
        pass
        # for anode in self.getNodes():
        #     tierinfo = self.session.get("https://"
        #                                 + self.APICIP
        #                                 # + '/api/node/mo/topology/pod-1/node-691.json?query-target=children').json()
        #                                 + '/api/node/mo/topology/pod-1/' + anode + '.json?query-target=children').json()
        #     # print("tierinfo is ", tierinfo)
        #     # print("nodeType is: ", tierinfo['imdata']['topSystem']['attributes']['nodeType'])
        #     atier = tierinfo['imdata']
        #     for anodetype in atier:
        #         if 'topSystem' in anodetype.keys():
        #             print('nodeType for ', anode, ' is: ', anodetype['topSystem']['attributes']['nodeType'])

    def getAttachedCDPdevices(self):
        cdpinfo = self.session.get("https://" + self.APICIP + '/api/node/class/cdpAdjEp.json').json()
        nodes = {}
        for cdpNode in cdpinfo['imdata']:
            adn = cdpNode['cdpAdjEp']['attributes']['dn']
            # "dn": "topology/pod-1/node-203/sys/cdp/inst/if-[eth1/28]/adj-1"
            match = re.search(r"topology/pod-1/(.*)/sys/cdp/inst/if-\[(.*)\]/adj", adn)
            leaf = str(match.group(1))
            port = str(match.group(2))
            devId = cdpNode['cdpAdjEp']['attributes']['devId']
            platId = cdpNode['cdpAdjEp']['attributes']['platId']
            #
            # want data structure returned in the form of:
            #   nodes[leaf] = {port:{devId:platId}}
            #
            portmap = {port: {devId: platId}}
            if leaf in nodes.keys():
                nodes[leaf][port] = {devId: platId}
            else:
                nodes[leaf] = portmap
        return nodes

    def getAttachedLLDPdevices(self):
        lldpinfo = self.session.get("https://" + self.APICIP + '/api/node/class/lldpAdjEp.json').json()
        nodes = {}
        for lldpNode in lldpinfo['imdata']:
            adn = lldpNode['lldpAdjEp']['attributes']['dn']
            # "dn": "topology/pod-1/node-601/sys/lldp/inst/if-[eth1/36]/adj-1",
            match = re.search(r"topology/pod-1/(.*)/sys/lldp/inst/if-\[(.*)\]/adj", adn)
            leaf = str(match.group(1))
            port = str(match.group(2))
            sysName = lldpNode['lldpAdjEp']['attributes']['sysName']
            enCap = lldpNode['lldpAdjEp']['attributes']['enCap']
            #
            # want data structure returned in the form of:
            #   nodes[leaf] = {port:{devId:platId}}
            #
            portmap = {port: {sysName: enCap}}
            if leaf in nodes.keys():
                nodes[leaf][port] = {sysName: enCap}
            else:
                nodes[leaf] = portmap
        return nodes

    def getallepgs(self):
        epgs = self.session.get("https://" + self.APICIP + '/api/class/fvAEPg.json').json()
        epglist = {}
        for fvAEPg in epgs['imdata']:
            anepg = fvAEPg['fvAEPg']['attributes']['dn']
            match = re.search(r"uni/tn-(.*)/ap-(.*)/epg-(.*)", anepg)
            tenant = match.group(1)
            ap = match.group(2)
            epg = match.group(3)
            # print("tenant ", match.group(1), "AP ", match.group(2), "EPG ", match.group(3))
            # print("epg type ", type(epgs), "epgs ", epgs)
            epglist[epg] = [tenant, ap]
        return epglist

    def getallcircuits(self):
        epgs = self.session.get("https://" + self.APICIP + '/api/class/fvAEPg.json').json()
        acircuit = {}
        for fvAEPg in epgs['imdata']:
            anepg = fvAEPg['fvAEPg']['attributes']['dn']
            match = re.search(r"uni/tn-(.*)/ap-(.*)/epg-(.*)", anepg)
            tenant = match.group(1)
            ap = match.group(2)
            epg = match.group(3)
            descr = fvAEPg['fvAEPg']['attributes']['descr']
            if tenant == 'common' and ap == 'PIP_Internet':
                acircuit[epg] = descr
        return acircuit

    def getallcontracts(self):
        contractsJson = self.session.get("https://" + self.APICIP + '/api/node/class/vzBrCP.json').json()
        contracts = []
        for vzBrCP in contractsJson['imdata']:
            scope = vzBrCP['vzBrCP']['attributes']['scope']
            adn = vzBrCP['vzBrCP']['attributes']['dn']
            match = re.search(r"uni/tn-(.*)/brc-(.*)", adn)
            tenant = match.group(1)
            acontract = match.group(2)
            contracttuple = (acontract, tenant, scope)
            # print("tenant = ", tenant, "\tcontract = ", acontract, "\tscope = ", scope)
            contracts.append(contracttuple)
        return sorted(list(dict.fromkeys(contracts)))
        # return contracts

    def getalltenants(self):
        tenants = []
        allepgs=self.getallepgs()
        for anepg in allepgs.values():
            atenant = anepg[0]
            tenants.append(atenant)
        # remove duplicate tenant entries before returning tenant list
        return list(dict.fromkeys(tenants))

    def getallaps(self):
        aps = []
        allepgs = self.getallepgs()
        for anepg in allepgs.values():
            anap = anepg[1]
            aps.append(anap)
        # remove duplicate ap entries before returning AP list
        return list(dict.fromkeys(aps))

    def AddStaticToEPG(self, Tenant, AP, EPG, Node, Port, VLAN):
        vlan = 'vlan-' + VLAN
        Dn = "topology/pod-1/paths-{node}/pathep-[{port}]".format(node=Node, port=Port)
        payload = {
            "fvRsPathAtt": {
                "attributes": {
                    "encap": vlan,
                    "instrImedcy": "immediate",
                    "mode": "untagged",
                    "tDn": Dn,
                    "status": "created"
                },
                "children": []
            }
        }
        print("payload sent is ", payload)
        epgobject = "/api/node/mo/uni/tn-{tenant}/ap-{ap}/epg-{epg}.json".format(tenant=Tenant, ap=AP, epg=EPG)
        post_response = self.session.post("https://" + self.APICIP + epgobject, data=json.dumps(payload))
        return post_response.json()

    def DeleteStaticFromEPG(self, Tenant, AP, EPG, Node, Port, VLAN):
        Dn = "uni/tn-{tenant}/" \
             "ap-{ap}/epg-{epg}/" \
             "rspathAtt-[topology/" \
             "pod-1/paths-{node}/" \
             "pathep-[{port}]".format(tenant=Tenant, ap=AP, epg=EPG, node=Node, port=Port)

        payload = {
            "fvRsPathAtt": {
                "attributes": {
                    "dn": Dn,
                    "status": "deleted"
                }, "children": []
            }
        }
        print("payload sent is ", payload)
        post_response = self.session.post("https://" + self.APICIP + epgobject, data=json.dumps(payload))
        return post_response.json()


def main():

    # Presales ACI Fabric with 127 leafs is "x.x.x.x"
    # Test ACI Fabric is "x.x.x.x"

    APIC_IP = "x.x.x.x"
    APIC_USER = "swinters"

    pwdfile = '.pwd'
    pwdfile = os.path.join(os.getenv('HOME'), pwdfile)
    if os.path.exists(pwdfile):
        with open(pwdfile) as f:
            APIC_PASS = f.readline().rstrip()
    else:
        print("couldn't find password file")
        exit()

    session = vzwACI(APIC_IP, APIC_USER, APIC_PASS)

    allcircuits = session.getallcircuits()
    for circuit in allcircuits.keys():
        match = re.search(r'(\d+\.\+d\.\+d\.\+d)-(\d+)+cry*', circuit)
        network = match.group(1)
        mask = match.group(2)
        print(network + "/" + mask, allcircuits[circuit])
    #
    # print(session.APICIP)
    #
    # getEPGs = session.getallepgs()
    # print("len getEPGs ", len(getEPGs))
    #
    # getTenants = session.getalltenants()
    # print("Tenants: ", getTenants)
    #
    # getAPs = session.getallaps()
    # print("num of AP's is: ", len(getAPs), "\nAP's: ", getAPs)
    #
    # getCDPattachments = session.showattachedCDPdevices()
    # print("there are: ", len(getCDPattachments), "\nnodes are:", getCDPattachments)
    # for akey in sorted(getCDPattachments.keys()):
    #     print(akey, getCDPattachments[akey])
    #
    # getallnodes = session.getNodes()
    # print(getallnodes)
    #
    # tiers = session.getTierInfo()
    #
    # contracts = session.getallcontracts()
    # print("num of contracts is: ", len(contracts), contracts)
    # for i in contracts:
    #     print('tenant: ', i[1], '\tcontract: ', i[0], '\t\t\tscope: ', i[2])
    #
    # cdps = session.getAttachedCDPdevices()
    # print(cdps)
    # lldps = session.getAttachedLLDPdevices()
    # print(lldps)
    #
    # print(tabulate(contracts, headers=["Contract", "Tenant", "Scope"]))
    # exit()
    #
    # Tenant = 'common'
    # AP = 'Infrastructure'
    # EPG = 'x.x.x.x'
    # VLAN = '88'
    # ports = ['33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46']
    # leafids = ['481', '482', '491', '492']
    # for leaf in leafids:
    #     for port in ports:
    #         ethport = 'eth1/' + port
    #         result = session.AddStaticToEPG(Tenant, AP, EPG, leaf, ethport, VLAN)
    #         print(result)
    #
if __name__ == "__main__":
    main()
