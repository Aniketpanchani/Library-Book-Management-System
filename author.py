from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import mysql.connector
from datetime import datetime
def create_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='root',
        database='Library'
    )
def create_tables():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS AUTHOR (
            AUTHOR_ID INT AUTO_INCREMENT PRIMARY KEY,
            NAME VARCHAR(50),
            BIO VARCHAR(100),
            BIRTHDATE DATE,
            COUNTRY VARCHAR(20)
        );
    ''')
    cursor.close()
    connection.close()
def get_authors():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM AUTHOR")
    result = cursor.fetchall()
    cursor.close()
    connection.close()

    # Convert date fields to string  for json 
    for author in result:
        if author.get('BIRTHDATE'):
            author['BIRTHDATE'] = author['BIRTHDATE'].strftime('%Y-%m-%d')

    return result
     

def get_author(author_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM AUTHOR WHERE AUTHOR_ID = %s", (author_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()

    if result and result.get('BIRTHDATE'):
        result['BIRTHDATE'] = result['BIRTHDATE'].strftime('%Y-%m-%d')

    return result

def insert_author(author):
    if not isinstance(author, dict):
        return {"error": "Invalid input. Expected a dictionary."}

    errors = []

    # Validate the name field
    name = author.get('name')
    if not name or not isinstance(name, str) or not name.isalpha():
        errors.append("Invalid name. Name must be a string ")

    # Validate the bio field
    bio = author.get('bio')
    if not bio or not isinstance(bio, str):
        errors.append("Invalid bio. Bio must be a string.")

    # Validate the birthdate field
    birthdate = author.get('birthdate')
    if birthdate:
        try:
            date_obj = datetime.strptime(birthdate, '%Y-%m-%d')
            if date_obj > datetime.now():
                errors.append("Birthdate cannot be a future date.")
        except (ValueError, TypeError):
            errors.append("Invalid birthdate format. Use YYYY-MM-DD.")
    else:
        errors.append("Birthdate is required.")

    # Validate the country field
    country = author.get('country')
    if not country or not isinstance(country, str) or not country.isalpha():
        errors.append("Invalid country. Country must be a string.")

    if errors:
        return {"error": errors}

    # Proceed with insertion if no errors
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO AUTHOR (NAME, BIO, BIRTHDATE, COUNTRY) VALUES (%s, %s, %s, %s)",
        (author['name'], author['bio'], author['birthdate'], author['country'])
    )
    connection.commit()
    new_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return {'id': new_id}

def update_author(author_id, author):
    # Check if the input is a dictionary
    if not isinstance(author, dict):
        return {"error": "Invalid input. Expected a dictionary."}

    errors = []

    # Validate 'name'
    name = author.get('name')
    if not name or not isinstance(name, str) or not name.isalpha():
        errors.append("Invalid name.")

    # Validate the bio field
    bio = author.get('bio')
    if not bio or not isinstance(bio, str):
        errors.append("Invalid bio.")
    
    # Validate 'birthdate'
    birthdate = author.get('birthdate')
    if birthdate:
        try:
            date_obj = datetime.strptime(birthdate, '%Y-%m-%d')
            if date_obj > datetime.now():
                errors.append("Birthdate cannot be a future date")
            else:
                author['birthdate'] = date_obj.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            errors.append("Invalid birthdate. Use YYYY-MM-DD.")
    else:
        errors.append("Birthdate is required")

    # Validate 'country'
    country = author.get('country')
    if not country or not isinstance(country, str) or not country.isalpha():
        errors.append("Invalid country. ")

    # Return errors if any
    if errors:
        return {"error": errors}

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM AUTHOR WHERE AUTHOR_ID = %s", (author_id,))
    selectedauthor = cursor.fetchone()

    if not selectedauthor:
        cursor.close()
        connection.close()
        return {"error": "Author not found"}
    else:
        cursor.execute(
            "UPDATE AUTHOR SET NAME = %s, BIO = %s, BIRTHDATE = %s, COUNTRY = %s WHERE AUTHOR_ID = %s",
            (author['name'], author['bio'], author['birthdate'], author['country'], author_id)
        )
        connection.commit()
        cursor.close()
        connection.close()

        return {"id updated": author_id}


def delete_author(author_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Check if the author ID exists in the BOOK table
    cursor.execute("SELECT * FROM Book WHERE AUTHOR_ID = %s", (author_id,))
    books = cursor.fetchall()

    if books:
        cursor.close()
        connection.close()
        return {"error": "Cannot delete author. Please delete all associated books first."}

    # Proceed with author deletion if no books are associated
    cursor.execute("SELECT * FROM Author WHERE AUTHOR_ID = %s", (author_id,))
    existing_author = cursor.fetchone()

    if not existing_author:
        cursor.close()
        connection.close()
        return {"error": "Author not found"}
    
    cursor.execute("DELETE FROM Author WHERE AUTHOR_ID = %s", (author_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Author deleted successfully"}

class RequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, status, response):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))    

    def do_GET(self):
        if self.path == '/authors':
            authors = get_authors()
            self._send_response(200, authors)
        elif self.path.startswith('/authors/'):
            try:            
                author_id = int(self.path.split('/')[2])
                author = get_author(author_id)
                if author:
                    self._send_response(200, author)
                else:
                    self._send_response(404, {'error': 'Author not found'})
            except ValueError:
                self._send_response(400, {'error': 'Invalid author ID'})
        else:
            self._send_response(404, {'error': 'Not found'})
    def do_POST(self):
         if self.path == '/authors':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                new_author = json.loads(post_data)
                response = insert_author(new_author)
                
                if 'error' in response:
                    self._send_response(400, response)
                else:
                    self._send_response(201, response)
            
            except ValueError:
                self._send_response(400, {'error': 'Invalid request'})
         else:
            self._send_response(404, {'error': 'Not found'})        
    def do_PUT(self):
        if self.path.startswith('/authors/'):
            try:
                author_id = int(self.path.split('/')[-1])
                content_length = int(self.headers['Content-Length'])
                put_data = self.rfile.read(content_length)
                updated_author = json.loads(put_data)
                result = update_author(author_id, updated_author)

                if 'error' in result:
                    if 'Author not found' in result['error']:
                        self._send_response(404, result)
                    else:
                        self._send_response(400, result)
                else:
                    self._send_response(200, result)

            except ValueError:
                self._send_response(400, {'error': 'Invalid author ID'})
        else:
            self._send_response(404, {'error': 'Not found'})

    def do_DELETE(self):
        if self.path.startswith('/authors/'):
            try:
                author_id = int(self.path.split('/')[-1])
                response = delete_author(author_id)
                
                if 'error' in response:
                    self._send_response(404, response)
                else:
                    self._send_response(200, response)
            
            except ValueError:
                self._send_response(400, {'error': 'Invalid author ID'})
        else:
            self._send_response(404, {'error': 'Not found'})
def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()
run()    

