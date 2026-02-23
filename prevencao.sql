# NUNCA faça isso (vulnerável):
query = f"SELECT * FROM users WHERE email = '{email}'"

# SEMPRE use parâmetros parametrizados:
cursor.execute(
    "SELECT * FROM users WHERE email = %s AND password_hash = crypt(%s, password_hash)",
    (email, password)
)

# Use SQLAlchemy com textos puros:
from sqlalchemy import text
result = db.session.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": user_email}
)