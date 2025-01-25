import pymysql

connection = pymysql.connect(
    host='localhost', 
    port=9030,          
    user='root',       
    password='',        
    database='app_db',  
    cursorclass=pymysql.cursors.DictCursor  # to dict
)

try:
    with connection.cursor() as cursor:
        query = """
        SELECT 
            sensor_id, 
            DATE_FORMAT(`timestamp`, '%Y-%m-%d') AS day, 
            COUNT(*) AS total_messages, 
            AVG(CAST(JSON_UNQUOTE(JSON_EXTRACT(message, '$.temperature')) AS DOUBLE)) AS avg_temperature, 
            MAX(CAST(JSON_UNQUOTE(JSON_EXTRACT(message, '$.temperature')) AS DOUBLE)) AS max_temperature
        FROM raw_sensors_data
        WHERE DATE_FORMAT(`timestamp`, '%Y-%m-%d') = CURRENT_DATE()
        GROUP BY sensor_id, DATE_FORMAT(`timestamp`, '%Y-%m-%d')
        ORDER BY sensor_id ASC;
        """


        cursor.execute(query)

        results = cursor.fetchall()
        for row in results:
            print(row)

finally:
    connection.close()
