# 🧠 Project-2 — Full Stack Application

This project contains a **FastAPI backend** and a **React (Vite) frontend**.

Follow the instructions below to set up and run both parts.

---

## 🖥️ Backend Setup

1. Navigate to the backend directory  
   cd backend

2. Create a virtual environment  
   - For Windows:  
     python -m venv env  
     env\Scripts\activate  

   - For Linux / macOS:  
     python3 -m venv env  
     source env/bin/activate  

3. Install dependencies  
   pip install -r requirements.txt

4. Run the backend server  
   uvicorn main:app --reload

The backend will be running at:  
👉 http://127.0.0.1:8000

---

## 💻 Frontend Setup

1. Navigate to the frontend directory  
   cd frontend

2. Install dependencies  
   npm install

3. Run the development server  
   npm run dev

The frontend will be running at:  
👉 http://localhost:5173

---

## ⚙️ Notes

- Ensure that both the **backend** and **frontend** servers are running simultaneously.  
- Update any API URLs in your frontend code (if applicable) to point to the correct backend address.  
- Use different terminal windows/tabs for frontend and backend.

---

## 🧩 Project Structure

project-2/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── __pycache__/
│   └── env/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── node_modules/
│
└── README.md
