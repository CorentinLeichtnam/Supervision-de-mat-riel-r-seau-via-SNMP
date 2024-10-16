LEICHTNAM Corentin & STRENTZ Nicolas

# Supervision-de-materiel-reseau-via-SNMP

## Diagrame de GANTT du projet



## Différents solutions choisis 

### Module de configuration :

### Module de surveillance :

### Module de « Log » :	





+---------------------+              +--------------------+               +--------------------+              +--------------------+
|      Devices         |1           n|   Devices_OID       |n           1|      OID            |1            n|      Logs           |
+---------------------+<------------>|---------------------|------------>|---------------------|<------------>|---------------------|
| device_id (PK)       |              | device_oid_id (PK)  |             | oid_id (PK)         |             | log_id (PK)         |
| hostname             |              | device_id (FK)      |             | oid_value           |             | device_id (FK)      |
| ip_address           |              | oid_id (FK)         |             | oid_name            |             | oid_id (FK)         |
| location             |              | timestamp           |             | description         |             | value               |
| device_type          |              +--------------------+             +---------------------+              | severity            |
| description          |                                                                                      | message             |
| status               |                                                                                      | timestamp           |
| last_updated         |                                                                                      +--------------------+
+---------------------+


                                                                         +---------------------+              +--------------------+ 
                                                                         |      Alerts          |1           n|   Logs_Access       |
                                                                         +---------------------+<------------>|---------------------|  
                                                                         | alert_id (PK)        |             | access_id (PK)      |
                                                                         | device_id (FK)       |             | log_id (FK)         |
                                                                         | alert_type           |             | user_id (FK)        |
                                                                         | severity             |             | access_time         |
                                                                         | message              |             +---------------------+
                                                                         | timestamp            |
                                                                         | resolved             |
                                                                         +---------------------+

 

+---------------------+
|      Users           |        
+---------------------+
| user_id (PK)         |
| username             |
| email                |
| role                 |
+---------------------+
