import requests

# 1. Login as teacher and set password for a class
requests.post("http://localhost:8000/api/auth/register", json={"username": "teacher1", "email": "t1@t.com", "password": "123", "role": "teacher"})
t_login = requests.post("http://localhost:8000/api/auth/login", json={"username": "teacher1", "password": "123"}).json()
t_token = t_login["token"]

# Set password
requests.put("http://localhost:8000/api/classrooms/cls-101/info", 
    headers={"Authorization": f"Bearer {t_token}"},
    json={"password": "xyz"}
)

# 2. Login as student
requests.post("http://localhost:8000/api/auth/register", json={"username": "student1", "email": "s1@s.com", "password": "123", "role": "student"})
s_login = requests.post("http://localhost:8000/api/auth/login", json={"username": "student1", "password": "123"}).json()

# 3. Try to join
res = requests.post("http://localhost:8000/api/classrooms/cls-101/join", 
    json={"username": "student1", "role": "student", "password": "xyz"}
)
print("Join response:", res.status_code, res.text)
