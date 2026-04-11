# 📈 StockSense AI — Stock Market Prediction by Machine Learning

> **B.Tech AIML Final Year Project** | Web-based stock prediction system powered by Linear Regression, Random Forest, and LSTM neural networks.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![Django](https://img.shields.io/badge/Django-4.2-green?style=flat-square)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3-orange?style=flat-square)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-red?style=flat-square)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue?style=flat-square)

---

## 🏗️ System Architecture

```
User → Browser (HTML/CSS/JS + Chart.js)
     → Django REST API (JWT Auth)
     → yFinance (Live Market Data)
     → ML Pipeline (Preprocess → Train → Predict)
     → JSON Response → Charts & Dashboard
     → MySQL (History & Logs)
```

---

## 📁 Folder Structure

```
stockmarket/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── stockmarket/               # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── predictor/                 # Main Django app
│   ├── models.py              # PredictionHistory, SearchLog
│   ├── views.py               # API views (Register, Login, Predict, History)
│   ├── urls.py                # URL routing
│   ├── serializers.py         # DRF serializers
│   ├── admin.py               # Admin panel config
│   ├── apps.py
│   ├── utils.py               # Error handler, helpers
│   └── services/              # Business logic layer
│       ├── data_fetcher.py    # yfinance integration
│       ├── preprocessing.py   # Feature engineering, scaling
│       ├── model_trainer.py   # Linear / RF / LSTM training
│       └── predictor.py       # Orchestration pipeline
│
├── templates/
│   ├── auth/
│   │   ├── login.html         # Glassmorphism login page
│   │   └── register.html      # Registration with password strength
│   └── dashboard/
│       └── dashboard.html     # Main trading dashboard
│
├── static/
│   ├── css/
│   ├── js/
│   └── img/
│
└── logs/                      # App logs (auto-created)
```

---

## 🚀 Setup & Run Locally

### 1. Prerequisites

- Python 3.10+
- MySQL 8.0+
- Git

### 2. Clone the repository

```bash
git clone https://github.com/yourusername/stocksense-ai.git
cd stocksense-ai
```

### 3. Create virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment

```bash
cp .env.example .env
# Edit .env with your MySQL credentials and secret key
```

### 6. Create MySQL database

```sql
-- Run in MySQL shell
CREATE DATABASE stockmarket_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'stockuser'@'localhost' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON stockmarket_db.* TO 'stockuser'@'localhost';
FLUSH PRIVILEGES;
```

### 7. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Create superuser

```bash
python manage.py createsuperuser
# Follow the prompts to set username, email, password
```

### 9. Create logs directory

```bash
mkdir logs
```

### 10. Run development server

```bash
python manage.py runserver
```

Open your browser: **http://127.0.0.1:8000**

---

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/register/` | No | Create new account |
| POST | `/api/login/` | No | Get JWT tokens |
| POST | `/api/logout/` | Yes | Invalidate token |
| GET | `/api/me/` | Yes | Current user profile |
| GET | `/api/predict/?symbol=AAPL&model=linear&days=7` | Yes | Run prediction |
| GET | `/api/history/` | Yes | Prediction history |
| GET | `/api/popular/` | No | Popular ticker list |
| POST | `/api/token/refresh/` | No | Refresh JWT |

### Sample Prediction Response

```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "company_name": "Apple Inc.",
    "sector": "Technology",
    "currency": "USD",
    "current_price": 189.34,
    "price_change_pct": 1.24,
    "model_used": "linear",
    "historical_prices": [
      {"date": "2024-01-15", "price": 185.20},
      ...
    ],
    "predicted_prices": [
      {"date": "2025-03-03", "price": 191.45},
      ...
    ],
    "metrics": {
      "r2_score": 0.9312,
      "mse": 4.87,
      "rmse": 2.21
    },
    "prediction_days": 7,
    "last_updated": "2025-03-01T12:00:00Z"
  }
}
```

---

## 🤖 ML Models

### Model 1: Linear Regression
- Feature engineering with lag features (1, 3, 7, 14 days)
- Rolling mean and standard deviation
- EMA-12 technical indicator
- Day-of-week and month encoding
- MinMax scaling
- 80/20 train-test split

### Model 2: Random Forest
- 200 estimators, max depth 10
- Same feature set as Linear Regression
- Handles non-linear relationships
- More robust to outliers

### Model 3: LSTM Neural Network
- 128-unit LSTM → Dropout(0.2) → 64-unit LSTM → Dense(32) → Dense(1)
- 60-day lookback window
- EarlyStopping with patience=10
- MinMax scaled prices

### Forecasting Method
All models use **iterative forecasting** — predicting one day at a time, rolling the window forward for multi-step predictions.

---

## 📊 Database Schema

```sql
-- PredictionHistory
id, user_id, symbol, company_name, model_used,
current_price, price_change_pct, r2_score, mse, rmse,
prediction_days, created_at

-- SearchLog
id, user_id, symbol, searched_at, success, error_message
```

---

## 🌐 Deployment (Render)

### 1. Build command

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

### 2. Start command

```bash
gunicorn stockmarket.wsgi:application --bind 0.0.0.0:$PORT
```

### 3. Environment variables (set in Render dashboard)

```
SECRET_KEY=<your-production-secret-key>
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
DB_NAME=<production-db-name>
DB_USER=<production-db-user>
DB_PASSWORD=<production-db-password>
DB_HOST=<production-db-host>
```

### AWS EC2 Deployment

```bash
# On EC2 Ubuntu instance
sudo apt update && sudo apt install python3-pip nginx mysql-server -y
git clone <repo>
cd stockmarket && pip install -r requirements.txt
# Configure Nginx + Gunicorn as system service
# See nginx.conf template below
```

---

## 🎓 Project Information

- **Title**: Stock Market Prediction by Machine Learning
- **Degree**: B.Tech Computer Science & Engineering (AIML Specialization)
- **Technologies**: Python, Django, REST Framework, scikit-learn, TensorFlow, yfinance, MySQL, Chart.js
- **Architecture**: MVC + Service Layer + REST API

---

## 📝 License

This project is built for academic purposes.

---

*Made with ❤️ for B.Tech Final Year Review*
