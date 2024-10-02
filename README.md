# Supervision-de-materiel-reseau-via-SNMP

##Diagrame de GANTT du projet



##Différents solutions choisis 

###Module de configuration :

###Module de surveillance :

###Module de « Log » :	



+---------------------+              +--------------------+              +--------------------+
|      Devices         |1           n|      OID            |1           n|      Logs           |
+---------------------+<------------>|---------------------|<------------>|---------------------|
| device_id (PK)       |              | oid_id (PK)         |              | log_id (PK)         |
| hostname             |              | oid_value           |             | device_id (FK)      |
| ip_address           |              | oid_name            |             | oid_id (FK)         |
| device_type          |              | device_id (FK)      |             | value               |
| description          |              +--------------------+              | timestamp           |
| status               |                                                  | severity            |
|  last_updated        |                                                       | message             |
 +---------------------+                                                        +--------------------+
                                                     

                                                    | 
+---------------------+              +--------------------+ 
|      Alerts          |1           n|   Logs_Access       |
+---------------------+<------------>|---------------------|  
| alert_id (PK)        |              | access_id (PK)      |
| device_id (FK)       |              | log_id (FK)         |
| alert_type           |              | user_id (FK)        |
| severity             |              | access_time         |
| message              |              +---------------------+
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

