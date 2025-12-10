# test_app.py
import unittest
import os
from app import app, init_db, get_db
class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        # Use test-mode database
        app.config["TESTING"] = True
        app.config["DATABASE"] = "test.db"
        # Delete old test DB
        if os.path.exists("test.db"):
            os.remove("test.db")
        # Create fresh test DB
        init_db()
        # Create test client
        self.client = app.test_client()


    # TEST 1: Home page loads correctly
    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to RZA Zoo", response.data)


    # TEST 2: Education page loads
    def test_education_page_loads(self):
        response = self.client.get("/education")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Education Centre", response.data)


    # TEST 3: About page loads
    def test_about_page_loads(self):
        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"About RZA Zoo", response.data)


    # TEST 4: Animals fact page loads
    def test_animals_fact_page_loads(self):
        response = self.client.get("/animalsfact")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Bat", response.data)


    # TEST 5: Booking creation test (FULL WORKING VERSION)
    def test_booking_creation(self):
        # Step 1 — Register user (needed for login)
        self.client.post("/register", data={
            "username": "Bob",
            "email": "bob@gmail.com",
            "password": "1234",
            "confirm_password": "1234"
        }, follow_redirects=True)
        # Step 2 — Login user (booking requires login)
        self.client.post("/login", data={
            "email": "bob@gmail.com",
            "password": "1234"
        }, follow_redirects=True)
        # Step 3 — Submit booking
        self.client.post("/booking/submit", data={
            "name": "Bob",
            "email": "bob@gmail.com",
            "date": "2025-12-15",   # Correct format
            "tickets": "1",         # Correct name
            "ticket_type": "Single"
        }, follow_redirects=True)
        # Step 4 — Check if booking saved
        conn = get_db()
        result = conn.execute(
            "SELECT * FROM bookings WHERE name='Bob'"
        ).fetchone()
        conn.close()
        self.assertIsNotNone(result)  # booking should be saved


    # TEST 6: Registration saves user
    def test_user_can_register(self):
        self.client.post("/register", data={
            "username": "Bean",
            "email": "bean@gmail.com",
            "password": "5678",
            "confirm_password": "5678"
        }, follow_redirects=True)
        conn = get_db()
        result = conn.execute(
            "SELECT * FROM users WHERE username='Bean'"
        ).fetchone()
        conn.close()
        self.assertIsNotNone(result)


    def tearDown(self):
        # Delete test DB after each test
        if os.path.exists("test.db"):
            os.remove("test.db")


if __name__ == "__main__":
    unittest.main()
 