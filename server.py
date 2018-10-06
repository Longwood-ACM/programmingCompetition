from flask import Flask, g, render_template, request, redirect, url_for, escape, session
from werkzeug.utils import secure_filename
import sqlite3
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import os, sys, platform
from hashlib import md5
from datetime import datetime as d

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = (['cpp', 'c'])
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MONGO_URI'] = "mongodb://localhost:27018/acm"
app.config.from_object(__name__)
app.config.update(dict(
	SECRET_KEY="acmdongle",
	DATABASE="acm.db",
	USERNAME="admin",
	PASSWORD="default",
))
mongo = PyMongo(app)

def checkLogged():
	if 'username' in session:
		return True
	return False

def checkInstructor():
	db = getDB()
	instr = db.execute("SELECT * FROM login WHERE position='INSTRUCTOR' and email=?", (session['username'],)).fetchall()
	if instr:
		return True
	return False

def checkTeaches(courseID):
	db = getDB()
	instr = db.execute("SELECT * FROM class JOIN login ON login.userID=class.instructorID WHERE position='INSTRUCTOR' and email=? and classID=?", (session['username'], courseID)).fetchall()
	if instr:
		return True
	return False

def checkOwnsAssign(assignmentID):
	db = getDB()
	instr = db.execute("SELECT * FROM assignment JOIN class ON class.classID=assignment.classID JOIN login ON login.userID=class.instructorID WHERE login.email=? AND assignmentID=?", (session['username'], assignmentID)).fetchall()
	if instr:
		return True
	return False

#HAAAAAAAAH
#I'm not funny
def valiDate(unfdate):
	if unfdate[1] > "12":
		return False
	if ["01", "03", "05", "07", "08", "10", "12"].count(unfdate[1]):
		if unfdate[0] > "31":
			return False
	if ["04", "06", "09", "11"].count(unfdate[1]):
		if unfdate[0] > "30":
			return False
	if ["02"].count(unfdate[1]):
		if unfdate > "29":
			return False

	date = "%s-%s-%s" % (unfdate[2], unfdate[1], unfdate[0])
	if not checkToday(date):
		return False
	return True

def checkToday(date):
	today = d.today()
	darray = date.split("-")
	tarray = str(today).split("-")
	tarray[2] = tarray[2].split(" ")[0]

	if int(darray[0]) < int(tarray[0]):
		return False
	elif int(darray[0]) == int(tarray[0]) and int(darray[1]) < int(tarray[1]):
		return False
	elif int(darray[0]) == int(tarray[0]) and int(darray[1]) == int(tarray[1]) and int(darray[2]) < int(tarray[2]):
		return False
	return True

def connectDB():
	rv = sqlite3.connect(app.config['DATABASE'])
	return rv

def getDB():
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = connectDB()
	return g.sqlite_db

def allowedFile(filename):
	if '.' in filename:
		fileparts = filename.rsplit('.',1)
		if fileparts[len(fileparts) - 1] in ALLOWED_EXTENSIONS:
			return True
	return False

def home():
	return redirect(url_for('root'))

@app.route('/')
def root():
	if not checkLogged():
		return redirect(url_for('login'))
	return redirect(url_for("courses"))

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		error = None
		validlogin = False
		password = md5(request.form['password'].encode('utf-8')).hexdigest()
		validlogin = mongo.db.users.find_one({"username": request.form['username'], "password": password})
		if validlogin:
			session['username'] = request.form['username']
			session['password'] = request.form['password']
			return redirect(url_for('courses'))
		else:
			userexists = mongo.db.users.find_one({'username': request.form['username']})
			if userexists:
				error = "Password does not match"
			else:
				error = "Username is not registered"
			return render_template('login.html', loginerror=error)
	return render_template('login.html')

@app.route('/logout')
def logout():
	if not checkLogged():
		return home()
	session.pop('username', None)
	return redirect(url_for('root'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'POST':
		db = getDB()
		error = None

		emailexists = db.execute('SELECT * FROM login WHERE email=?', (request.form['email'],)).fetchall()
		if emailexists:
			return render_template('signup.html', loginerror="That email is already registered")

		password = md5(request.form['password'].encode('utf-8')).hexdigest()

		db.execute('INSERT INTO login (firstName, lastName, email, password, position, question, answer) VALUES (?, ?, ?, ?, ?, ?, ?)', (request.form['firstName'], request.form['lastName'], request.form['email'], password, request.form['type'], request.form['securityQuestion'], request.form['answer']))
		db.commit()
		session['username'] = request.form['email']
		session['password'] = request.form['password']
		session['type'] = request.form['type']
		userdir = r'./userdirs/%s' % request.form['email']
		if not os.path.exists(userdir):
			os.makedirs(userdir)
		return redirect(url_for('courses'))
	return render_template('signup.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
	if request.method == "POST":
		db = getDB()
		email = request.form['username']
		exists = db.execute("SELECT userID FROM login WHERE email=?", (email,)).fetchall()
		if exists:
			userID = exists[0][0]
			return redirect(url_for('forgot2', userID=userID))
		return render_template('forgotpw.html', error="That user does not exists.")
	return render_template('forgotpw.html')

@app.route('/forgot2/<userID>', methods=['GET', 'POST'])
def forgot2(userID):
	db = getDB()
	question = db.execute("SELECT question FROM login WHERE userID = ?", (userID,)).fetchall()[0][0]
	q = ""
	if question == 'petName':
		q = 'What was the name of your first pet?'
	elif question == 'maidenName':
		q = "What is your mother's maiden name?"
	elif question == 'firstStreet':
		q = "What is the name of the street on which you grew up?"
	elif question == 'elemSchool':
		q = "What is the name of your elementary school?"
	elif question == 'firstCar':
		q = "What is the name of your first car?"
	if request.method == "POST":
		ans = db.execute("SELECT answer FROM login WHERE userID=?", (userID,)).fetchall()[0][0]
		if ans == request.form['answer']:
			password = request.form['password']
			pw = md5(password.encode('utf-8')).hexdigest()
			db.execute("UPDATE login SET password = ? WHERE userID = ?", (pw, userID))
			db.commit()
			return redirect(url_for('login'))
		else:
			return render_template('forgotpw2.html', question = q, error="Answer to security question is wrong")
	return render_template('forgotpw2.html', question = q)

@app.route('/courses')
def courses():
	if checkLogged():
		utype = mongo.db.users.find_one({"username": session['username']})['position']
		if utype == 'instructor':
			cs = []
			i = 0
			for c in mongo.db.courses.find({"instructor": session['username']}):
				cc =[]
				cc.append(c['title'])
				cc.append(c['_id'])
				assigns = []
				for a in mongo.db.assignments.find({"class": c['_id']}):
					cassign = []
					cassign.append(a['title'])
					cassign.append(str(a['_id']))
					assigns.append(cassign)
				cc.append(assigns)
				cs.append(cc)		
			return render_template('professor.html', user=session['username'], courses=cs)
		elif utype == 'student':
			cs = []
			i = 0
			for c in mongo.db.courses.find({"students": session['username']}):
				cc =[]
				cc.append(c['title'])
				assigns = []
				for a in mongo.db.assignments.find({"class": c['_id']}):
					cassign = []
					cassign.append(a['title'])
					cassign.append(str(a['_id']))
					assigns.append(cassign)
				cc.append(assigns)
				cs.append(cc)		
			return render_template('courses.html', user=session['username'], courses=cs)
	return redirect(url_for('root'))

@app.route('/create', methods=['GET', 'POST'])
def create():
	if not checkLogged():
		return home()
	if not checkInstructor():
		return home()
	if request.method == 'POST':
		db = getDB()
		title = request.form['title']
		secNum = request.form['secNumber']
		semester = request.form['semester']
		year = request.form['courseYear']
		instructorID = db.execute("SELECT userID FROM login WHERE email=?", (session['username'],)).fetchall()
		exists=db.execute("SELECT classID from class WHERE title = ? and section = ? and semester = ? and year = ?",(title,secNum,semester,year)).fetchall()
		if not exists:
			db.execute("INSERT INTO class(instructorID, title, section, semester, year) VALUES(?, ?, ?, ?, ?)", (instructorID[0][0], title, secNum, semester, year))
			db.commit()
		else:
			return render_template("addcourse.html", title = title, secNumber = secNum, semester = semester, year = year, error = "Class already exists")
		names = request.form['listStudent']
		courseID=db.execute("SELECT classID from class WHERE title = ? and section = ? and semester = ? and year = ?",(title,secNum,semester,year)).fetchall()[0][0]
		if ', ' in names:
			names = names.split(', ')
			if names:
				for name in names:
					studentID = db.execute("SELECT userID FROM login WHERE email=?", (name,)).fetchall()
					if studentID:
						takes = db.execute('SELECT * FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0])).fetchall()
					else:
						takes = 1
					if not takes:
						db.execute('INSERT INTO takes(classID, userID) VALUES(?, ?)', (courseID, studentID[0][0]))
		elif ',' in names:
			names = names.split(',')
			if names:
				for name in names:
					studentID = db.execute("SELECT userID FROM login WHERE email=?", (name,)).fetchall()
					if studentID:
						takes = db.execute('SELECT * FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0])).fetchall()
					else:
						takes = 1
					if not takes:
						db.execute('INSERT INTO takes(classID, userID) VALUES(?, ?)', (courseID, studentID[0][0]))
		elif names:
				name = names
				studentID = db.execute("SELECT userID FROM login WHERE email=?", (name,)).fetchall()
				if studentID:
					takes = db.execute('SELECT * FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0])).fetchall()
				else:
					takes = 1
				if not takes:
					db.execute('INSERT INTO takes(classID, userID) VALUES(?, ?)', (courseID, studentID[0][0]))
		db.commit()
		return redirect(url_for('courses'))
	return render_template('addcourse.html', user=session['username'])

@app.route('/editCourse/<courseID>', methods=['GET', 'POST'])
def editCourse(courseID):
	if not checkLogged():
		return home()
	if not checkInstructor():
		return home()
	if not checkTeaches(courseID):
		return home()
	db = getDB()
	if request.method == 'POST':
		title = request.form['title']
		secNum = request.form['secNumber']
		semester = request.form['semester']
		year = request.form['courseYear']
		db.execute('UPDATE class SET title=?, section = ?, semester = ?, year = ? WHERE classID=?', (title, secNum, semester, year, courseID))
		instructorID = db.execute("SELECT userID FROM login WHERE email=?", (session['username'],)).fetchall()
		names = request.form['listStudent']
		if ', ' in names:
			names = names.split(', ')
			if names:
				for name in names:
					studentID = db.execute("SELECT userID FROM login WHERE email=?", (name,)).fetchall()
					if studentID:
						takes = db.execute('SELECT * FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0])).fetchall()
					else:
						takes = 1
					if not takes:
						db.execute('INSERT INTO takes(classID, userID) VALUES(?, ?)', (courseID, studentID[0][0]))
		elif ', ' in names:
			names = names.split(',')
			if names:
				for name in names:
					studentID = db.execute("SELECT userID FROM login WHERE email=?", (name,)).fetchall()
					if studentID:
						takes = db.execute('SELECT * FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0])).fetchall()
					else:
						takes = 1
					if not takes:
						db.execute('INSERT INTO takes(classID, userID) VALUES(?, ?)', (courseID, studentID[0][0]))
		elif names:
				name = names
				studentID = db.execute("SELECT userID FROM login WHERE email=?", (name,)).fetchall()
				if studentID:
					takes = db.execute('SELECT * FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0])).fetchall()
				else:
					takes = 1
				if not takes:
					db.execute('INSERT INTO takes(classID, userID) VALUES(?, ?)', (courseID, studentID[0][0]))

		names = request.form['deleteStudent']
		if ', ' in names:
			names = names.split(', ')
			if names:
				for name in names:
					studentID = db.execute("SELECT userID FROM login WHERE email=?", (name,)).fetchall()
					if studentID:
						takes = db.execute('SELECT * FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0])).fetchall()
					else:
						takes = 0
					if takes:
						db.execute('DELETE FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0]))
		elif ',' in names:
			names = names.split(',')
			if names:
				for name in names:
					studentID = db.execute("SELECT userID FROM login WHERE email=?", (name,)).fetchall()
					if studentID:
						takes = db.execute('SELECT * FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0])).fetchall()
					else:
						takes = 0
					if takes:
						db.execute('DELETE FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0]))
		elif names:
				name = names
				studentID = db.execute("SELECT userID FROM login WHERE email=?", (name,)).fetchall()
				if studentID:
					takes = db.execute('SELECT * FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0])).fetchall()
				else:
					takes = 0
				if takes:
					db.execute('DELETE FROM takes WHERE classID = ? and userID = ?', (courseID, studentID[0][0]))
		db.commit()
		return redirect(url_for('courses'))
	info = db.execute('SELECT * FROM class WHERE classID=?', (courseID,)).fetchall()
	students = db.execute("SELECT firstName, lastName, email FROM login JOIN takes ON takes.userID=login.userID WHERE takes.classID=?", (courseID,)).fetchall()
	return render_template('editcourse.html', user=session['username'], title=info[0][2], secNum=info[0][3], year=info[0][5], sem=info[0][4], students = students)

@app.route('/assignments/<assignmentID>', methods=["GET", "POST"])
def assignmentsID(assignmentID):
	if not checkLogged():
		return home()
	a = mongo.db.assignments.find_one({"_id": ObjectId(assignmentID)})
	unfdate = a['dueDate']
	undate = unfdate.split("-")
	date = "%s/%s/%s" % (undate[2], undate[1], undate[0])
	utype = mongo.db.users.find_one({"username": session['username']})['position']
	if utype == "student":
		code = ""
		output = ""
		comment = ""
		uexist = mongo.db.uploads.find_one({"username": session["username"], "assignment": ObjectId(assignmentID)})
		completed = ""
		if uexist:
			completed = uexist['completed']
		else:
			completed = 0
		filename = ""
		language = "C++"
		f = mongo.db.uploads.find_one({"username": session['username'], "assignment": ObjectId(assignmentID)})
		if f:
			fexist = f['fileLocation']
			if fexist:
				filename = fexist
				language = f['language']
		ifilename = './userdirs/%s/infile' % session['username']
		ofilename = './userdirs/%s/outfile' % session['username']
		exe = './userdirs/%s/assignment%s-%s' % (session['username'], assignmentID, session['username'])
		if request.method == "POST":
			language = request.form['language']
			if not checkToday(unfdate):
				return render_template("assignment.html", user=session['username'], title = a['title'], body = a['body'], date = date, assignmentID = assignmentID, comment=comment, error="Overdue", language=language)
			if language == "C++":
				filename = './userdirs/%s/assignment%s-%s.cpp' % (session['username'], assignmentID, session['username'])
				exe = './userdirs/%s/assignment%s-%s' % (session['username'], assignmentID, session['username'])
			elif language == "Python":
				filename = './userdirs/%s/assignment%s-%s.py' % (session['username'], assignmentID, session['username'])
			elif language == "Go":
				filename = './userdirs/%s/assignment%s-%s.go' % (session['username'], assignmentID, session['username'])
			code = request.form['code']
			inp = request.form.get('cin')
			timeout = 60
			codefile = open(filename, "w")
			codefile.write(code)
			codefile.close()
			if inp:
				infile = open(ifilename, "w")
				infile.write(inp)
				infile.close()
			if request.form['sandbox'] == 'runTest':
				if language == "C++":
					os.system('g++ %s -o %s 2> %s' % (filename, exe, ofilename))
					if os.path.exists(ofilename):
						opfile = open(ofilename, "r")
						output = opfile.read()
						opfile.close()
						#if output:
						#	os.remove(ofilename)
						#RENDER ERROR
				elif language == "Go":
					pass
				elif language == "Python":
					pass
				submitted = mongo.db.uploads.find_one({"assignment": ObjectId(assignmentID), "username": session['username']})
				if not submitted:
					inserted = mongo.db.uploads.insert_one({"username": session["username"], "assignment": ObjectId(assignmentID), "fileLocation": filename, "type": "SUBMISSION", "language": language, "completed": 0}).inserted_id
				diffFile = "./userdirs/%s/diffFile" % session['username']
				if os.path.exists(diffFile):
					os.remove(diffFile)
				eOutFile = "./userdirs/%s/expectedOut" % session['username']
				eOut = open(eOutFile, "w")
				for t in mongo.db.testCases.find({"username": session['username'], "priv": "private", "assignment": ObjectId(assignmentID)}):
					infile = open(ifilename, "w")
					infile.write(t['inputValue'])
					infile.close()
					eOut.write(t['outputValue'])
					if platform.system() == 'Linux':
						exitstat = os.system('timeout %d %s < %s >> %s' % (timeout, exe, ifilename, ofilename))
						if os.WEXITSTATUS(exitstat) == 124:
							os.system('echo "Program timed out on test %s" >> %s' % (t[0], diffFile))
					elif platform.system() == 'Darwin':
						exitstat = os.system('gtimeout %d %s < %s >> %s' % (timeout, exe, ifilename, ofilename))
						if os.WEXITSTATUS(exitstat) == 124:
							os.system('echo "Program timed out on test %s" >> %s' % (t[0], diffFile))
				eOut.close()
				os.system('diff %s %s > %s' % (ofilename, eOutFile, diffFile))
				outfile = open(diffFile, "r")
				output = outfile.read()
				outfile.close()
				return render_template('assignment.html', user=session['username'], title = a['title'], body = a['body'], date = date, assignmentID = assignmentID, grade=grade, comment=comment, code=code, output=output, language=language)
			elif request.form['sandbox'] == 'assignment':
				if language == "C++":
					os.system('g++ -Wall %s -o %s 2> %s' % (filename, exe, ofilename))
					if os.path.exists(ofilename):
						opfile = open(ofilename, "r")
						output = opfile.read()
						opfile.close()
						if output:
							os.remove(ofilename)
				elif language == "Go":
					pass
				elif language == "Python":
					pass
				submitted = mongo.db.uploads.find_one({"assignment": ObjectId(assignmentID), "username": session['username']})
				if not submitted:
					inserted = mongo.db.uploads.insert_one({"username": session["username"], "assignment": ObjectId(assignmentID), "fileLocation": filename, "type": "SUBMISSION", "language": language, "completed": 0}).inserted_id
				diffFile = "./userdirs/%s/diffFile" % session['username']
				if os.path.exists(diffFile):
					os.remove(diffFile)
				eOutFile = "./userdirs/%s/expectedOut" % session['username']
				eOut = open(eOutFile, "w")
				for t in mongo.db.testCases.find({ "assignment": ObjectId(assignmentID), "priv": "hidden"}):
					infile = open(ifilename, "w")
					infile.write(t['inputValue'])
					infile.close()
					eOut.write(t['outputValue'])
					if platform.system() == 'Linux':
						exitstat = os.system('timeout %d %s < %s >> %s' % (timeout, exe, ifilename, ofilename))
						if os.WEXITSTATUS(exitstat) == 124:
							os.system('echo "Program timed out on test %s" >> %s' % (t[0], diffFile))
					elif platform.system() == 'Darwin':
						exitstat = os.system('gtimeout %d %s < %s >> %s' % (timeout, exe, ifilename, ofilename))
						if os.WEXITSTATUS(exitstat) == 124:
							os.system('echo "Program timed out on test %s" >> %s' % (t[0], diffFile))
				eOut.close()
				os.system('diff %s %s > %s' % (ofilename, eOutFile, diffFile))
				outfile = open(diffFile, "r")
				output = outfile.read()
				outfile.close()
				if not output:
					#INCREMENT SCORE
					completed = mongo.db.uploads.find_one({"assignment": ObjectId(assignmentID)})['completed']
					if not completed:
						completed = mongo.db.uploads.update_one({"assignment": ObjectId(assignmentID)}, {"$set": {"completed": 1}})
						score = mongo.db.users.find_one({"username": session['username']})['score']
						update = mongo.db.users.update_one({"username": session['username']}, {"$set": {"score": score+1}})
						return render_template("assignment.html", user=session['username'], title = a['title'], body = a['body'], date = date, assignmentID = assignmentID, grade=grade, comment="COMPLETED", code=code, output=output, language=language)
				elif output:
					return render_template("assignment.html", user=session['username'], title = a['title'], body = a['body'], date = date, assignmentID = assignmentID, grade=grade, comment=comment, code=code, output=output, language=language)
		if os.path.exists(filename):
			cfile = open(filename, "r")
			code = cfile.read()
			cfile.close()
		if completed:
			return render_template("assignment.html", user=session['username'], title = a['title'], body = a['body'], date = date, assignmentID = assignmentID, grade=grade, comment="COMPLETED", code=code)
		return render_template("assignment.html", user=session['username'], title = a['title'], body = a['body'], date = date, assignmentID = assignmentID, grade=grade, comment=comment, code=code)
	elif utype == "instructor":
		'''uploads = db.execute("SELECT login.firstName, login.lastName, login.userID, uploads.fileLocation FROM login NATURAL JOIN uploads WHERE uploads.assignmentID = ?", (assignmentID,)).fetchall()
		userID = request.form.get('student')
		if userID == "default" or userID == None:
			userID = -1
		if request.method == 'POST':
			filename = ""
			ofilename = './userdirs/%s/outfile' % session['username']
			ifilename = './userdirs/%s/infile' % session['username']
			exe = "./userdirs/%s/assignment%s" % (session['username'], assignmentID)
			if request.form['sandbox'] == 'compile':
				if userID == -1:
					return render_template("profAssignment.html", user=session['username'], title = a[0][1], body = a[0][2], date = date, assignmentID = assignmentID, userID=userID, uploads=uploads)
				for u in uploads:
					if int(u[2]) == int(userID):
						filename = u[3]
				os.system('g++ -Wall %s -o %s 2> %s' % (filename, exe, ofilename))
				if os.path.exists(ofilename):
					opfile = open(ofilename, "r")
					output = opfile.read()
					opfile.close()
					os.remove(ofilename)
				cfile = open(filename, "r")
				code = cfile.read()
				cfile.close()
				return render_template("profAssignment.html", user=session['username'], title = a[0][1], body = a[0][2], date = date, code = code, output=output, assignmentID = assignmentID, userID=userID, uploads=uploads)
			elif request.form['sandbox'] == 'runCases':
				tests = db.execute("SELECT inputValue, outputValue FROM testCases WHERE (type = 'PUBLIC' OR type = 'HIDDEN')").fetchall()
				diffFile = "./userdirs/%s/diffFile" % session['username']
				if os.path.exists(diffFile):
					os.remove(diffFile)
				if os.path.exists(ofilename):
					os.remove(ofilename)
				eOutFile = "./userdirs/%s/expectedOut" % session['username']
				eOut = open(eOutFile, "w")
				for t in tests:
					infile = open(ifilename, "w")
					infile.write(t[0])
					infile.close()
					eOut.write(t[1])
					if platform.system() == 'Linux':
						exitstat = os.system('timeout %d %s < %s >> %s' % (timeout, exe, ifilename, ofilename))
						if os.WEXITSTATUS(exitstat) == 124:
							os.system('echo "Program timed out on test %s" >> %s' % (t[0], diffFile))
					elif platform.system() == 'Darwin':
						exitstat = os.system('gtimeout %d %s < %s >> %s' % (timeout, exe, ifilename, ofilename))
						if os.WEXITSTATUS(exitstat) == 124:
							os.system('echo "Program timed out on test %s" >> %s' % (t[0], diffFile))
				eOut.close()
				os.system('diff %s %s > %s' % (ofilename, eOutFile, diffFile))
				outfile = open(diffFile, "r")
				output = outfile.read()
				outfile.close()
				if os.path.exists(exe):
					os.remove(exe)
				if os.path.exists(ofilename):
					os.remove(ofilename)
				if os.path.exists(diffFile):
					os.remove(diffFile)
				if os.path.exists(ifilename):
					os.remove(ifilename)
				return render_template("profAssignment.html", user=session['username'], title = a[0][1], body = a[0][2], date = date, code = request.form['code'], output = output, assignmentID = assignmentID, userID=userID, uploads=uploads)'''
		return render_template("profAssignment.html", user=session['username'], title = a['title'], body = a['body'], date = date, assignmentID = assignmentID)

@app.route('/createAssignment/<courseID>', methods=['GET', 'POST'])
def createAssignment(courseID):
	if not checkLogged():
		return home()
	if not checkInstructor():
		return home()
	if request.method == 'POST':
		db = getDB()
		title = request.form['title']
		body = request.form['assignmentDesc']
		undate = request.form['dueDate']
		unfdate = undate.split("/")
		if len(unfdate[0]) == 1:
			unfdate[0] = "0" + unfdate[0]
		if len(unfdate[1]) == 1:
			unfdate[1] = "0" + unfdate[1]
		if not valiDate(unfdate):
			return render_template('createassignment.html', title = title, body = body, date = undate, error = "Bad Date") 
		date = "%s-%s-%s" % (unfdate[2], unfdate[1], unfdate[0])
		db.execute("INSERT INTO assignment(classID, title, body, dueDate) VALUES(?, ?, ?, ?)", (courseID, title, body, date))
		db.commit()
		return redirect(url_for('courses'))
	return render_template('createassignment.html', user=session['username'])

@app.route('/editAssignment/<assignmentID>', methods=['GET', 'POST'])
def editAssignment(assignmentID):
	if not checkLogged():
		return home()
	info = mongo.db.assignments.find_one({"_id": ObjectId(assignmentID)})
	cinfo = mongo.db.courses.find_one({"_id": info['class']})
	if cinfo['instructor'] != session['username']:
		return home()
	if request.method == 'POST':
		title = request.form['title']
		body = request.form['assignmentDesc']
		undate = request.form['dueDate']
		unfdate = undate.split("/")
		if len(unfdate[0]) == 1:
			unfdate[0] = "0" + unfdate[0]
		if len(unfdate[1]) == 1:
			unfdate[1] = "0" + unfdate[1]
		if not valiDate(unfdate):
			return render_template('editassignment.html', title = title, body = body, date = undate, error = "Bad Date")
		date = "%s-%s-%s" % (unfdate[2], unfdate[1], unfdate[0])
		mongo.db.assignments.update_one({"_id": ObjectId(assignmentID)}, {"$set": {"title": title, "body": body, "dueDate": date}})
		#db.execute("UPDATE assignment SET title = ?, body = ?, dueDate=? WHERE assignmentID = ?", (title, body, date, assignmentID))
		#db.commit()
		#return redirect(url_for('courses'))
		return render_template('editassignment.html', title = info['title'], body = info['body'], date = date)
	#info = db.execute("SELECT * FROM assignment WHERE assignmentID = ?", (assignmentID,)).fetchall()
	unfdate = info['dueDate']
	unfdate = unfdate.split("-")
	date = "%s/%s/%s" % (unfdate[2], unfdate[1], unfdate[0])
	return render_template('editassignment.html', title = info['title'], body = info['body'], date = date)

@app.route('/test/<assignmentID>', methods=["GET", "POST"])
def test(assignmentID):
	if not checkLogged():
		return home()
	u = mongo.db.users.find_one({"username": session['username']})
	title = mongo.db.assignments.find_one({'_id': ObjectId(assignmentID)})['title']
	if u['position'] == "student":
		if request.method == "POST":
			inpV = request.form['input'] + '\n'
			outV = request.form['output'] + '\n'
			if not inpV and outV:
				return render_template('testCases.html', user=session['username'], cases = cases, input = inpV, output = outV, error = "Please add an input and output.") 
			exists = mongo.db.testCases.find_one({"username": session['username'], "assignment": ObjectId(assignmentID), "inputValue": inpV, "outputValue": outV, "priv": "private"})
			if exists:
				cases = []
				for case in mongo.db.testCases.find({"username": session['username'], "assignment": ObjectId(assignmentID), "inputValue": inpV, "outputValue": outV, "priv": "private"}):
					cases.append(case)
				return render_template('testCases.html', user=session['username'], cases = cases, input = inpV, output = outV, error = "Test Case already exists.", assignmentID=assignmentID) 
			mongo.db.testCases.insert_one({"username": session['username'], "inputValue": inpV, "outputValue": outV, "priv": "private", "assignment": ObjectId(assignmentID)})
			cases = []
			for case in mongo.db.testCases.find({"username": session['username'], "assignment": ObjectId(assignmentID), "inputValue": inpV, "outputValue": outV, "priv": "private"}):
				c = []
				c.append(case['inputValue'])
				c.append(case['outputValue'])
				cases.append(c)
			return render_template('testCases.html', user=session['username'], cases = cases, assignmentID=assignmentID)
		cases = []
		for case in mongo.db.testCases.find({"username": session['username'], "assignment": ObjectId(assignmentID), "priv": "private"}):
			c = []
			c.append(case['inputValue'])
			c.append(case['outputValue'])
			cases.append(c)
		return render_template('testCases.html', user=session['username'], cases = cases, title = title, assignmentID=assignmentID)
	elif u['position'] == "instructor":
		cases = []
		if request.method == "POST":
			inpv = request.form['input'] +'\n'
			outv = request.form['output'] + '\n'
			if not inpv and outv:
				return render_template('professorCases.html', user=session['username'], cases = cases, input = inpV, output = outV, error = "Please add an input and output.")
			if not mongo.db.testCases.find_one({"username": session['username'], "assignment": ObjectId(assignmentID), "inputValue": inpv, "outputValue": outv, "priv": 'hidden'}):
				mongo.db.testCases.insert_one({"username": session['username'], "assignment": ObjectId(assignmentID), "inputValue": inpv, "outputValue": outv, "priv": 'hidden'})
		for case in mongo.db.testCases.find({"assignment": ObjectId(assignmentID), "priv": "hidden"}):
			c = []
			c.append(case['inputValue'])
			c.append(case['outputValue'])
			cases.append(c)
		return render_template('professorCases.html', user=session['username'], cases = cases, title = title, assignmentID=assignmentID)

@app.route('/grade/<assignmentID>/<userID>', methods=['GET', 'POST'])
def grade(assignmentID, userID):
	if not checkLogged():
		return home()
	if not checkInstructor():
		return home()
	if not checkOwnsAssign(assignmentID):
		return home()
	if userID < 0:
		return redirect(url_for('/assignment', assignmentID=assignmentID))
	grade = ""
	comment = ""
	db = getDB()
	exists = db.execute("SELECT grade, comment FROM grades WHERE userID = ? AND assignmentID =?", (userID, assignmentID)).fetchall()
	if exists:
		grade = exists[0][0]
		comment = exists[0][1]
	if request.method == "POST":
		grade = int(request.form['grade'])
		comment = request.form.get('comment')
		if grade > 100 or grade < 0:
			return render_template('grade.html', user=session['username'], grade=grade, comment=comment, error="Grade not in 0 - 100 range")
		if exists:
			db.execute("UPDATE grades SET grade = ?, comment = ? WHERE userID =? AND assignmentID=?", (grade, comment, userID, assignmentID))
		else:
			db.execute("INSERT INTO grades(userID, assignmentID, grade, comment) VALUES(?, ?, ?, ?)", (userID, assignmentID, grade, comment))
		db.commit()
		return render_template('grade.html', user=session['username'], grade=grade, comment=comment)
	return render_template('grade.html', user=session['username'], grade=grade, comment=comment)

@app.route('/faq')
def faq():
	if not checkLogged():
		return home()
	return render_template('faq.html', user=session['username'])

@app.route('/about')
def about():
	if not checkLogged():
		return home()
	return render_template('about.html', user=session['username'])

@app.route('/scoreboard')
def scoreboard():
	db = getDB()
	students = mongo.db.users.find({"position": "student"})
	return render_template('scoreboard.html', scores = students)

@app.teardown_appcontext
def closeDB(error):
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()

if __name__ == "__main__":
	app.run()
