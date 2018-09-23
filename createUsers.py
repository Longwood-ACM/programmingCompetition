from pymongo import MongoClient
import os
from hashlib import md5

def createUsers():
	client = MongoClient("mongodb://localhost:27018/")
	db = client.acm
	users = db.users

	users.create_index("username", unique=True)

	password = md5("password".encode('utf-8')).hexdigest()
	user ={"firstName": "Longwood",
	"lastName": "ACM",
	"password": password,
	"username": "longwoodacm",
	"position": "instructor",
	"question": "petName",
	"answer": "Captain"
	}
	inserted = users.insert_one(user).inserted_id
	print(inserted)
	userdir = r'./userdirs/longwoodacm'
	if not os.path.exists(userdir):
		os.makedirs(userdir)

	password = md5("password".encode('utf-8')).hexdigest()
	user ={"firstName": "First",
	"lastName": "Team",
	"password": password,
	"username": "Team1",
	"position": "student",
	"question": "petName",
	"answer": "Captain"
	}
	inserted = users.insert_one(user).inserted_id
	print(inserted)
	userdir = r'./userdirs/Team1'
	if not os.path.exists(userdir):
		os.makedirs(userdir)

	password = md5("password".encode('utf-8')).hexdigest()
	user ={"firstName": "Second",
	"lastName": "Team",
	"password": password,
	"username": "Team2",
	"position": "student",
	"question": "petName",
	"answer": "Captain"
	}
	inserted = users.insert_one(user).inserted_id
	print(inserted)
	userdir = r'./userdirs/Team2'
	if not os.path.exists(userdir):
		os.makedirs(userdir)
'''
# Create the schema
def createUsers():
	conn = sqlite3.connect('acm.db')
	c = conn.cursor()

	password = md5("password".encode('utf-8')).hexdigest()
	c.execute('INSERT INTO login(firstName, lastName, password, email, position, question, answer) VALUES("Longwood", "ACM", ?, "longwoodacm@gmail.com", "INSTRUCTOR", "petName", "Captain")',  (password,))
	userdir = r'./userdirs/longwoodacm@gmail.com'
	if not os.path.exists(userdir):
		os.makedirs(userdir)

	password = md5("password".encode('utf-8')).hexdigest()
	c.execute('INSERT INTO login(firstName, lastName, password, email, position, question, answer, score) VALUES("First", "Team", ?, "Team1", "STUDENT", "petName", "Captain", 0)',  (password,))
	userdir = r'./userdirs/Team1'
	if not os.path.exists(userdir):
		os.makedirs(userdir)

	password = md5("password".encode('utf-8')).hexdigest()
	c.execute('INSERT INTO login(firstName, lastName, password, email, position, question, answer, score) VALUES("Second", "Team", ?, "Team2", "STUDENT", "petName", "Captain", 0)',  (password,))
	userdir = r'./userdirs/Team1'
	if not os.path.exists(userdir):
		os.makedirs(userdir)
	
	c.execute('INSERT INTO class(instructorID, title, section, semester, year) VALUES(1, "Programming Competition 2018", 1, "Fall", 2018)')
	
	c.execute('INSERT INTO takes(userID, classID) VALUES(2, 1)')
	c.execute('INSERT INTO takes(userID, classID) VALUES(3, 1)')


	c.execute('INSERT INTO assignment(title, body, classID, dueDate) VALUES("Problem #1","Placeholder", 1, "2018-10-10")')


	conn.commit()
	conn.close()
'''
# Could put more in later
def main():
	createUsers()

if __name__ == "__main__":
	print("Running database user creation script.")
	main()