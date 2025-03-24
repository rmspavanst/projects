class Config:
    SECRET_KEY = '1234!@#$Qwerty'  
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost/server_monitoring'
    SQLALCHEMY_TRACK_MODIFICATIONS = False