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
        SELECT * from traffic_data;
        """


        cursor.execute(query)

        results = cursor.fetchall()
        for row in results:
            print(row)

finally:
    connection.close()
