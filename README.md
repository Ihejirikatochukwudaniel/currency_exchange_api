
## 🌍 Currency Exchange & Country Data API

A modern **FastAPI** service that integrates country and currency data from public APIs, stores it in a PostgreSQL database, and provides endpoints to query and analyze countries, their currencies, and estimated GDPs.

---

### 🚀 Features

* Fetches live data from:

  * 🌐 [REST Countries API](https://restcountries.com/)
  * 💱 [Open Exchange Rates API](https://open.er-api.com/)
* Computes **estimated GDP** values per country
* Stores country data in **PostgreSQL**
* Provides RESTful endpoints for:

  * Listing countries (with filters and sorting)
  * Fetching one country by name
  * Refreshing data from external APIs
  * Checking service status (total countries, last refresh time)
* Interactive **Swagger UI** documentation

---

### 🧱 Tech Stack

| Layer       | Technology                                                                          |
| ----------- | ----------------------------------------------------------------------------------- |
| Framework   | [FastAPI](https://fastapi.tiangolo.com/)                                            |
| ORM         | [SQLAlchemy (async)](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) |
| Database    | PostgreSQL                                                                          |
| HTTP Client | [HTTPX (async)](https://www.python-httpx.org/)                                      |
| Environment | Python 3.10+                                                                        |
| Docs UI     | Swagger (built-in with FastAPI)                                                     |

---

## 🗂️ Project Structure

```
currency-exchange-fastapi/
│
├── app/
│   ├── __init__.py
│   ├── main.py               # App entry point
│   ├── database.py           # DB connection setup
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic response models
│   ├── crud.py               # Database CRUD operations
│   ├── utils.py              # External API + helper functions
│   └── routers/
│       └── countries.py      # API endpoints for country data
│
├── .env                      # Environment variables (DB config, etc.)
├── requirements.txt           # Python dependencies
└── README.md
```

---

## ⚙️ Setup Guide

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/currency-exchange-fastapi.git
cd currency-exchange-fastapi
```

---

### 2️⃣ Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # On macOS/Linux
venv\Scripts\activate           # On Windows
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Create and configure the database

Make sure **PostgreSQL** is running.

Create a database, for example:

```bash
psql -U postgres
CREATE DATABASE currency_db;
```

Then exit with `\q`.

---

### 5️⃣ Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://postgres:<yourpassword>@localhost:5432/currency_db
```

If using a different user or port, adjust accordingly.

---

### 6️⃣ Initialize the database tables

You can use this script once to create your tables:

```bash
python -m app.models
```

Alternatively, if your `main.py` handles automatic creation via SQLAlchemy metadata, you can skip this step.

---

### 7️⃣ Run the app

```bash
uvicorn app.main:app --reload
```

Server will start at:

👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

Swagger Docs:
📘 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧭 API Endpoints

| Method | Endpoint             | Description                                     |
| ------ | -------------------- | ----------------------------------------------- |
| `GET`  | `/countries/`        | List all countries (supports filters & sorting) |
| `GET`  | `/countries/{name}`  | Get one country by name                         |
| `POST` | `/countries/refresh` | Refresh data from APIs and update DB            |
| `GET`  | `/countries/status`  | Show total count & last refresh timestamp       |

---

### 🔍 Example Requests

#### ✅ Get all countries

```bash
GET /countries/
```

#### ✅ Get country by name

```bash
GET /countries/Nigeria
```

#### ✅ List countries by region

```bash
GET /countries/?region=Africa
```

#### ✅ Sort by GDP (descending)

```bash
GET /countries/?sort=gdp_desc
```

#### ✅ Refresh all data

```bash
POST /countries/refresh
```

---

## 🧠 How the Data Works

1. The `/countries/refresh` endpoint:

   * Fetches all countries from **REST Countries API**
   * Fetches exchange rates from **Open Exchange Rates API**
   * Computes **estimated GDP** = `(population × random multiplier) ÷ exchange rate`
   * Saves the data into the database

2. `/countries/status` shows:

   * Total number of countries in the DB
   * Timestamp of the last refresh

---

## 🧰 Example `.env` File

```env
# Database config
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/currency_db

# Optional app settings
APP_ENV=development
LOG_LEVEL=info
```

---

## 🧪 Testing the Endpoints

Once the server is running, open Swagger UI:

📘 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Try executing:

* `POST /countries/refresh`
* `GET /countries/`
* `GET /countries/status`

All responses are automatically validated with **Pydantic schemas**.

---

## 🧩 Example Response

**GET /countries/Nigeria**

```json
{
  "name": "Nigeria",
  "capital": "Abuja",
  "region": "Africa",
  "population": 206139589,
  "currency_code": "NGN",
  "exchange_rate": 1567.88,
  "estimated_gdp": 275631.09,
  "flag": "https://flagcdn.com/w320/ng.png",
  "last_refreshed_at": "2025-10-24T17:23:50.300Z"
}
```

---

## 🧹 Common Issues

| Error                                                | Cause                               | Fix                                   |
| ---------------------------------------------------- | ----------------------------------- | ------------------------------------- |
| `Internal Server Error`                              | Missing table or DB not initialized | Recreate DB & run migrations          |
| `AttributeError: crud has no attribute 'get_status'` | Missing `get_status()`              | Use updated `crud.py`                 |
| `OperationalError`                                   | Wrong DB URL                        | Double-check `.env` connection string |
| `404 Not Found`                                      | Wrong route path                    | Confirm endpoint in Swagger UI        |

---

## 🧑‍💻 Development Notes

* Built with **async I/O** for efficiency (`httpx.AsyncClient`, `AsyncSession`).
* Follows clean modular architecture.
* Ideal for extension (e.g., caching with Redis, Celery for scheduling refreshes, etc.)

---

## 🏁 Future Improvements

* Add authentication & role-based access
* Integrate Redis for caching
* Include scheduled background refresh tasks
* Dockerize for production deployment

---

## 🪪 License

This project is licensed under the **MIT License** 

---

Would you like me to make it **auto-generate the database on startup** (so you don’t need a manual SQL step)?
I can show the code snippet to add that inside `main.py`.
