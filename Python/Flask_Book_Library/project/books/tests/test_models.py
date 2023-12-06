import unittest

from project.books.models import Book
from project import db, app
from parameterized import parameterized


class BookModelTest(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_ctxt = self.app.app_context()
        self.app_ctxt.push()
        db.create_all()

    def tearDown(self):
        db.drop_all()
        self.app_ctxt.pop()
        self.app = None
        self.app_ctxt = None

    @parameterized.expand([
        ('Example Book', 'Curtis', 1952, 'Fiction', 'available'),
        ('Example Book', 'Curtis Joel', 2000, 'Crime', 'unavailable'),
        ('Example Book', 'Curtis Joel Darcy', 2023, 'Fantasy', 'available'),
    ])
    def test_valid_input(self, name, author, year_published, book_type, status):
        book = Book(name=name, author=author, year_published=year_published, book_type=book_type, status=status)
        db.session.add(book)
        db.session.commit()

        self.assertIsNotNone(book.id)
        retrieved_book = Book.query.filter_by(id=book.id).first()
        self.assertEqual(retrieved_book.author, author)
        self.assertEqual(retrieved_book.year_published, year_published)
        self.assertEqual(retrieved_book.book_type, book_type)
        self.assertEqual(retrieved_book.status, status)

    @parameterized.expand([
        ('Example Book', 'Curtis', 'Year', 'Fiction', 'available'),
        ('Example Book', 'Curtis', -7, 'Fiction', 'available'),
        ('Example Book', 'Curtis', 4.5, 'Fiction', 'available'),
    ])
    def test_invalid_year(self, name, author, year_published, book_type, status):
        with self.assertRaises(Exception):
            book = Book(name=name, author=author, year_published=year_published, book_type=book_type, status=status)
            db.session.add(book)
            db.session.commit()

    def test_name_not_unique(self):
        with self.assertRaises(Exception):
            book1 = Book(name='Example Book', author='Curtis', year_published=1952, book_type='Fiction',
                         status='available')
            book2 = Book(name='Example Book', author='Curtis Joel', year_published=2000, book_type='Crime',
                         status='available')
            db.session.add(book1)
            db.session.add(book2)
            db.session.commit()

    @parameterized.expand([
        ("' OR '1'='1'; --", 'Curtis', 1952, 'Fiction', 'available'),
        ('Example Book', "1; DROP TABLE users; --", 1952, 'Fiction', 'available'),
        ('Example Book', 'Curtis', '-- or # ', 'Fiction', 'available'),
        ('Example Book', 'Curtis', 1952, "' OR IF(1=1, SLEEP(5), 0); --", 'available'),
        ('Example Book', 'Curtis', 1952, 'Fiction', "' OR 1=CONVERT(int, (SELECT @@version)); --"),
    ])
    def test_invalid_input_SQL_injection(self, name, author, year_published, book_type, status):
        with self.assertRaises(Exception):
            book = Book(name=name, author=author, year_published=year_published, book_type=book_type, status=status)
            db.session.add(book)
            db.session.commit()

    @parameterized.expand([
        ("<script>alert('XSS')</script>", 'Curtis', 2000, 'Fiction', 'available'),
        ('Example Book', "<img src=\"javascript:alert('XSS')\" alt=\"XSS\">", 2000, 'Fiction', 'available'),
        ('Example Book', 'Curtis', "<img src=\"x\" onerror=\"alert('XSS')\">", 'Fiction', 'available'),
        ('Example Book', 'Curtis', 2000, "<a href=\"javascript:alert('XSS')\">XSS</a>", 'available'),
        ('Example Book', 'Curtis', 2000, 'Fiction', "<a href=\"data:text/html;base64,"
                                                    "PHNjcmlwdD5hbGVydCgnWFNTJyk8L3NjcmlwdD4=\">XSS</a>"),
    ])
    def test_invalid_input_XSS(self, name, author, year_published, book_type, status):
        with self.assertRaises(Exception):
            book = Book(name=name, author=author, year_published=year_published, book_type=book_type, status=status)
            db.session.add(book)
            db.session.commit()

    @parameterized.expand([
        ('Example Book', 'b' * 200000, 1952, 'Fiction', 'available'),
        ('Example Book', 'Curtis', float('inf'), 'Fiction', 'available'),
        ('Example Book', 'Curtis', 1952, 'c' * 400000, 'available'),
        ('Example Book', 'Curtis', 1952, 'Fiction', 'd' * 800000),
    ])
    def test_extreme_input(self, name, author, year_published, book_type, status):
        book = Book(name=name, author=author, year_published=year_published, book_type=book_type, status=status)
        with self.assertRaises(Exception):
            db.session.add(book)
            db.session.commit()
