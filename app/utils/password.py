import bcrypt

salt = bcrypt.gensalt()

def hash_password(password: str) -> str:
    # Convert the password to bytes
    password_bytes = password.encode('utf-8')
    
    # Hash the password using the generated salt
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    
    # Return the hashed password as a decoded string
    return hashed_password.decode('utf-8')

import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Convert the plain password to bytes
    plain_password_bytes = plain_password.encode('utf-8')
    
    # Convert the hashed password to bytes
    hashed_password_bytes = hashed_password.encode('utf-8')
    
    # Verify the password
    return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
