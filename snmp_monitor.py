from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd

class SNMPMonitor:
    def __init__(self, ip, community="public", port=161):
        """
        Initialise une session SNMP.
        :param ip: Adresse IP de l'équipement.
        :param community: Communauté SNMP (par défaut : public).
        :param port: Port SNMP (par défaut : 161).
        """
        self.ip = ip
        self.community = community
        self.port = port

    def get_snmp_data(self, oid):
        """
        Récupère la valeur associée à un OID via SNMP.
        :param oid: L'OID SNMP à interroger.
        :return: La valeur associée à l'OID ou None en cas d'erreur.
        """
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((self.ip, self.port)),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )

            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

            if errorIndication:
                print(f"SNMP Error: {errorIndication}")
                return None
            elif errorStatus:
                print(f"SNMP Error: {errorStatus.prettyPrint()}")
                return None
            else:
                for varBind in varBinds:
                    return str(varBind[1])  # Retourne la valeur associée à l'OID
        except Exception as e:
            print(f"SNMP Exception: {e}")
            return None


    def get_in_octets(self):
        """
        Récupère les octets entrants sur l'interface indexée par 18.
        :return: Le nombre d'octets entrants ou None en cas d'erreur.
        """
        in_octets_oid = "1.3.6.1.2.1.2.2.1.10.4"  # OID pour les octets entrants
        return self.get_snmp_data(in_octets_oid)

    def get_out_octets(self):
        """
        Récupère les octets sortants sur l'interface indexée par 18.
        :return: Le nombre d'octets sortants ou None en cas d'erreur.
        """
        out_octets_oid = "1.3.6.1.2.1.2.2.1.16.4"  # OID pour les octets sortants
        return self.get_snmp_data(out_octets_oid)

    def get_system_description(self):
        """
        Récupère la description du système (sysDescr).
        :return: Description du système.
        """
        sys_descr_oid = "1.3.6.1.2.1.1.1.0"  # OID pour sysDescr
        return self.get_snmp_data(sys_descr_oid)