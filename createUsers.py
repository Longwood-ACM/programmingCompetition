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
	"answer": "Captain",
	"score": 0
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
	"answer": "Captain",
	"score": 0
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
	"answer": "Captain",
	"score": 0
	}
	inserted = users.insert_one(user).inserted_id
	print(inserted)
	userdir = r'./userdirs/Team2'
	if not os.path.exists(userdir):
		os.makedirs(userdir)

	courses = db.courses
	course = {"instructor": "longwoodacm",
	"title": "Programming Competition 2018",
	"section": 1,
	"semester": "Fall",
	"year": 2018,
	"students": ["Team1", "Team2"]
	}
	cinserted = courses.insert_one(course).inserted_id
	print(cinserted)

	assignments = db.assignments
	assignment =[{"title": "Problem #0",
	"body": "Placeholder",
	"class": cinserted,
	"dueDate": "2018-10-10"
	},{"title": "Problem #1",
	"body": "Placeholder",
	"class": cinserted,
	"dueDate": "2018-10-10"
	},{"title": "Problem #2",
	"body": "Placeholder",
	"class": cinserted,
	"dueDate": "2018-10-10"
	},{"title": "Problem #3",
	"body": "Placeholder",
	"class": cinserted,
	"dueDate": "2018-10-10"
	},{"title": "Problem #4",
	"body": "Placeholder",
	"class": cinserted,
	"dueDate": "2018-10-10"
	},{"title": "Problem #5",
	"body": "Placeholder",
	"class": cinserted,
	"dueDate": "2018-10-10"
	},{"title": "Problem #6",
	"body": "Placeholder",
	"class": cinserted,
	"dueDate": "2018-10-10"
	},{"title": "Problem #7",
	"body": "Placeholder",
	"class": cinserted,
	"dueDate": "2018-10-10"
	},{"title": "Problem #8",
	"body": "Placeholder",
	"class": cinserted,
	"dueDate": "2018-10-10"
	},{"title": "Problem #9",
	"body": "Placeholder",
	"class": cinserted,
	"dueDate": "2018-10-10"
	}]
	inserted = assignments.insert_many(assignment).inserted_ids
	print(inserted)

def main():
	createUsers()

if __name__ == "__main__":
	print("Running database user creation script.")
	main()