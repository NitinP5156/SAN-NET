<<<<<<< HEAD
# SAN-NET

A modern social media web application built with Django.

## Features
- User authentication (login, signup, logout)
- Real-time messaging with beautiful dark mode
- Responsive, modern UI with Tailwind CSS
- Profile pictures and user profiles
- Conversation list and search
- Last seen and online indicators

## Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd SAN-NET
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the app:**
   Open [http://localhost:8000](http://localhost:8000) in your browser.

## Deployment

- Configure environment variables for production (e.g., `DEBUG=0`, `ALLOWED_HOSTS`, database settings).
- Use a production-ready database (PostgreSQL recommended).
- Collect static files:
  ```bash
  python manage.py collectstatic
  ```
- Deploy to your preferred platform (Render, Heroku, etc.).

## License

MIT License 
=======
# SAN-NET
>>>>>>> 77b300dce1fb83e9aa6577c51628713d63c1ef07
