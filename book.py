from http.server import BaseHTTPRequestHandler, HTTPServer
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
        CREATE TABLE IF NOT EXISTS BOOK (
            BOOK_ID INT AUTO_INCREMENT PRIMARY KEY,
            TITLE VARCHAR(100),
            DESCRIPTION VARCHAR(255),
            PUBLICATION_DATE DATE,
            GENRE VARCHAR(50),
            PAGES INT,
            AUTHOR_ID INT,
            FOREIGN KEY (AUTHOR_ID) REFERENCES AUTHOR(AUTHOR_ID)
        );
    ''')
    cursor.close()
    connection.close()

def get_books():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Book")
        results = cursor.fetchall()
        for book in results:
            if book.get('PUBLICATION_DATE'):
                book['PUBLICATION_DATE'] = book['PUBLICATION_DATE'].strftime('%Y-%m-%d')
    finally:
        cursor.close()
        connection.close()
    return results

def get_book(book_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Book WHERE BOOK_ID = %s", (book_id,))
    result = cursor.fetchone()
    if result and result.get('PUBLICATION_DATE'):
        result['PUBLICATION_DATE'] = result['PUBLICATION_DATE'].strftime('%Y-%m-%d')  # Convert date to string
    cursor.close()
    connection.close()
    return result

def get_books_byauthor(author_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Book WHERE AUTHOR_ID = %s", (author_id,))
    results = cursor.fetchall()
    for book in results:
        if book.get('PUBLICATION_DATE'):
            book['PUBLICATION_DATE'] = book['PUBLICATION_DATE'].strftime('%Y-%m-%d')  # Convert date to string
    cursor.close()
    connection.close()
    return results
def get_author_by_book(book_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    query = '''
        SELECT a.* FROM AUTHOR AS a
JOIN BOOK AS b ON a.AUTHOR_ID = b.AUTHOR_ID
WHERE b.BOOK_ID = %s

    '''
    cursor.execute(query, (book_id,))
    author = cursor.fetchone()
    cursor.close()
    connection.close()

    # Convert date fields to string
    if author and author.get('BIRTHDATE'):
        author['BIRTHDATE'] = author['BIRTHDATE'].strftime('%Y-%m-%d')
    
    return author

    

def insert_book(book):
    errors = []
    if not isinstance(book, dict):
        return {"error": "Invalid input. Expected a dictionary."}

    # Validate the title field
    title = book.get('title')
    if not title or not isinstance(title, str) or not title.isalpha():
        errors.append("Invalid title. Title must be a string containing only alphabetic characters.")

    # Validate the description field
    description = book.get('description')
    if not description or not isinstance(description, str):
        errors.append("Invalid description. Description must be a string.")

    # Validate the publication_date field
    publication_date = book.get('publication_date')
    if publication_date:
        try:
            date_obj = datetime.strptime(publication_date, '%Y-%m-%d')
            if date_obj > datetime.now():
                errors.append("Publication date cannot be a future date.")
        except (ValueError, TypeError):
            errors.append("Invalid publication date format. Use YYYY-MM-DD.")
    else:
        errors.append("Publication date is required.")

    # Validate the author_id field
    author_id = book.get('author_id')
    if not author_id or not isinstance(author_id, int):
        errors.append("Invalid author ID.or can not be Author ID not empty.")
    else:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM AUTHOR WHERE AUTHOR_ID = %s", (author_id,))
        if cursor.fetchone() is None:
            cursor.close()
            connection.close()
            return {"error": "Invalid author ID. Author not found."}
        cursor.close()
        connection.close()

    # Validate the genre field
    genre = book.get('genre')
    if not genre or not isinstance(genre, str) or not genre.isalpha():
        errors.append("Invalid genre. Genre must be a string containing only alphabetic characters.")

    # Validate the pages field
    pages = book.get('pages')
    if not pages or not isinstance(pages, int) or pages <= 0:
        errors.append("Invalid number of pages. Pages must be a positive integer.")

    if errors:
        return {"error": errors}

    # Proceed with insertion if no errors
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO Book (TITLE, DESCRIPTION, PUBLICATION_DATE, AUTHOR_ID, GENRE, PAGES) VALUES (%s, %s, %s, %s, %s, %s)",
        (book['title'], book['description'], book['publication_date'], book['author_id'], book['genre'], book['pages'])
    )
    connection.commit()
    new_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return {'id': new_id}

def update_book(book_id, book):
    # Check if the input is a dictionary
    if not isinstance(book, dict):
        return {"error": "Invalid input. Expected a dictionary."}

    errors = []

    # Validate the title field
    title = book.get('title')
    if not title or not isinstance(title, str) or not title.isalpha():
        errors.append("Invalid title. Title must be a string containing only alphabetic characters.")

    # Validate the description field            
    description = book.get('description')
    if not description or not isinstance(description, str):
        errors.append("Invalid description. Description must be a string.")

    # Validate the publication_date field
    publication_date = book.get('publication_date')
    if publication_date:
        try:
            date_obj = datetime.strptime(publication_date, '%Y-%m-%d')
            if date_obj > datetime.now():
                errors.append("Publication date cannot be a future date.")
            else:
                book['publication_date'] = date_obj.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            errors.append("Invalid publication date format. Use YYYY-MM-DD.")
    else:
        errors.append("Publication date is required.")

    author_id = book.get('author_id')
    if not author_id or not isinstance(author_id, int):
    
        errors.append("Invalid author ID.or can not be Author ID not empty.")
    else:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM AUTHOR WHERE AUTHOR_ID = %s", (author_id,))
        if cursor.fetchone() is None:
            cursor.close()
            connection.close()
            return {"error": "Invalid author ID. Author not found."}
        cursor.close()
        connection.close()

    # Validate the genre field
    genre = book.get('genre')
    if not genre or not isinstance(genre, str) or not genre.isalpha():
        errors.append("Invalid genre. Genre must be a string.")

    # Validate the pages field
    pages = book.get('pages')
    if not pages or not isinstance(pages, int) or pages <= 0:
        errors.append("Invalid number of pages. Pages must be a positive integer.")

    if errors:
        return {"error": errors}

    # Proceed with updating the book in the database
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Book WHERE BOOK_ID = %s", (book_id,))
    existing_book = cursor.fetchone()

    if not existing_book:
        cursor.close()
        connection.close()
        return {"error": "Book not found"}

    cursor.execute(
        "UPDATE Book SET TITLE = %s, DESCRIPTION = %s, PUBLICATION_DATE = %s, AUTHOR_ID = %s, GENRE = %s, PAGES = %s WHERE BOOK_ID = %s",
        (book['title'], book['description'], book['publication_date'], book['author_id'], book['genre'], book['pages'], book_id)
    )
    connection.commit()
    cursor.close()
    connection.close()
    return {"id": book_id}

def delete_book(book_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Book WHERE BOOK_ID = %s", (book_id,))
    existing_book = cursor.fetchone()

    if not existing_book:
        cursor.close()
        connection.close()
        return {"error": "Book not found"}

    cursor.execute("DELETE FROM Book WHERE BOOK_ID = %s", (book_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Book deleted successfully"}

class RequestHandler2(BaseHTTPRequestHandler):
    def _send_response(self, status, response):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        if self.path == '/books':
            books = get_books()
            self._send_response(200, books)

        elif self.path.startswith('/books/'):
            try:
                book_id = int(self.path.split('/')[2])
                book = get_book(book_id)
                if book:
                    self._send_response(200, book)
                else:
                    self._send_response(404, {'error': 'Book not found'})
            except ValueError:
                self._send_response(400, {'error': 'Invalid book ID'})
        elif self.path.startswith('/booksbyauthorid/'):
            try:
                author_id = int(self.path.split('/')[-1])
                books = get_books_byauthor(author_id)
                if books:
                    self._send_response(200, books)
                else:
                    self._send_response(404, {'error': 'No books found for this author'})
            except ValueError:
                self._send_response(400, {'error': 'Invalid author ID'})
        elif self.path.startswih('/authordetailsbybookid/'):
            try:
                book_id = int(self.path.split('/')[2])
                author = get_author_by_book(book_id)
                if author:
                    self._send_response(200, author)
                else:
                    self._send_response(404, {'error': 'Author not found for this book'})
            except ValueError:
                self._send_response(400, {'error': 'Invalid book ID'})
        else:
            self._send_response(404, {'error': 'Not found'})

    def do_POST(self):
        if self.path == '/books':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                new_book = json.loads(post_data)
                response = insert_book(new_book)
                if 'error' in response:
                    self._send_response(400, response)
                else:
                    self._send_response(201, response)
            except ValueError:
                self._send_response(400, {'error': 'Invalid request'})
        else:
            self._send_response(404, {'error': 'Not found'})

    def do_PUT(self):
        if self.path.startswith('/books/'):
            try:
                book_id = int(self.path.split('/')[-1])
                content_length = int(self.headers['Content-Length'])
                put_data = self.rfile.read(content_length)
                updated_book = json.loads(put_data)
                result = update_book(book_id, updated_book)
                if 'error' in result:
                    if 'Book not found' in result['error']:
                        self._send_response(404, result)
                    else:
                        self._send_response(400, result)
                else:
                    self._send_response(200, result)
            except ValueError:
                self._send_response(400, {'error': 'Invalid book ID'})
        else:
            self._send_response(404, {'error': 'Not found'})

    def do_DELETE(self):
        if self.path.startswith('/books/'):
            try:
                book_id = int(self.path.split('/')[-1])
                response = delete_book(book_id)
                if 'error' in response:
                    self._send_response(404, response)
                else:
                    self._send_response(200, response)
            except ValueError:
                self._send_response(400, {'error': 'Invalid book ID'})
        else:
            self._send_response(404, {'error': 'Not found'})

def run1(server_class=HTTPServer, handler_class=RequestHandler2, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__":
    run1()