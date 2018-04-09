#! reddit wholesome coin bot. Monitors a subreddit 
#and hands out Wholesome Coin #when someone summons the bot explicitly.
#Currently very much a work in progress. Expect messy code and notes"


import praw, pprint, datetime, sqlite3, string, time, sys, pickle, os


conn = sqlite3.connect('wholesomeCoin.db')
c = conn.cursor()


SEARCHcoin = '!wholesomecoin' #SEARCHcoin must be lowercase
SEARCHscore = '!wholesomescore' #let user check their score
#AWARD_TEXT= '\nPositively triggered for u/{}!\nScore: **{}**.\n\n*****\n\n*^Bleep ^bloop. ^How ^are ^you? ^I\'m ^a ^work ^in ^progress. ^| [^message ^me](https://reddit.com/message/compose/?to=wholesomecoinbot)^| [^Info ^placeholder](https://google.com) ^|*'
AWARD_TEXT= '\n+1 WholesomeCoin for u/{}!\nCurrent wholesome coinage: **{}**.\n\n*****\n\n*^Bleep ^bloop. ^I\'m ^a ^work ^in ^progress. ^How ^are ^you? ^| [^Feedback](https://reddit.com/message/compose/?to=wholesomecoinbot)^| [^Info ^(placeholder)](https://google.com) ^|*'
SCORE_TEXT= 'You have **{}** WholesomeCoins. Keep going!\n\n*****\n\n*^Bleep ^bloop. ^I\'m ^a ^work ^in ^progress. ^How ^are ^you? ^| [^Feedback](https://reddit.com/message/compose/?to=wholesomecoinbot)^| [^Info ^(placeholder)](https://google.com) ^|*'
HOT_SUBSTORUN = 10  #number of HOT submissions to check in each subreddit
NEW_SUBSTORUN = 10  #number of NEW submissions to check in each subreddit
#SUBREDDITS_WHITELIST = ['AskReddit','testingground4bots','todayilearned']
SUBREDDITS_WHITELIST = ['testingground4bots']
#DENY_TEXT= '\nNegatively triggered for u/{}!\nScore: **{}**.\n\n*****\n\n*^Bleep ^bloop. ^How ^are ^you? ^I\'m ^a ^work ^in ^progress. ^| [^message ^me](https://reddit.com/message/compose/?to=wholesomecoinbot)^| [^Info ^placeholder](https://google.com) ^|*'
DENY_TEXT= 'Hey don\'t do that!\nI\'m taking away half your WholesomeCoins :(\n\n*****\n\n*^Bleep ^bloop. ^I\'m ^a ^work ^in ^progress. ^How ^are ^you? ^| [^Feedback](https://reddit.com/message/compose/?to=wholesomecoinbot)^| [^Info ^(placeholder)](https://google.com) ^|*'
coinsGiven = 0 #keeps track of how many coins given out per script run
coinUp = 1 #how many coins a user should get
POSTINTERVAL = 60 #how long to wait between replies, in seconds
lastPostTime = POSTINTERVAL #enables bot to reply to the first eligible candidate
REPLYLIMIT = 5	 #max number of replies to send in a given submission.



#Creates the table to keep track of everyone's coins
#Create the following tables:
#wholesome_coining; wholesome_users; wholesome_score
def createTable():
	c.execute('''CREATE TABLE IF NOT EXISTS wholesome_coining(
		comment_id TEXT NOT NULL, 
		giver_username TEXT, 
		parent_comment_id TEXT, 
		receiver_username TEXT, 
		award REAL,
		replied_to BOOLEAN,  
		PRIMARY KEY(comment_id))'''
		) #replied to is new new
	
	c.execute('''CREATE TABLE IF NOT EXISTS wholesome_users(
		username TEXT NOT NULL, 
		PRIMARY KEY(username))
		''')

def coiningTracker(redditObject, award): #record all coining actions in the main table
	global coinsGiven #TODO: remove for production
	c.execute('SELECT comment_id FROM wholesome_coining')
	coinData = c.fetchall() #coinData is a list of touples
	commentIdList = [t[0] for t in coinData]
	if redditObject.id not in commentIdList:
		c.execute('''INSERT INTO wholesome_coining 
			(comment_id, giver_username, parent_comment_id, receiver_username, award, replied_to) 
			VALUES (?,?,?,?,?,?)''', (redditObject.id, redditObject.author.name, redditObject.parent().id, redditObject.parent().author.name,award, False, ))
		coinsGiven += 1
	conn.commit()

def wholesomeUserTracker(redditObject): #just adds users to the user table
	parent = redditObject.parent().author.name
	c.execute('SELECT username FROM wholesome_users')
	coinData = c.fetchall() #coinData is a list of touples
	authorsList = [t[0] for t in coinData]
	if parent not in authorsList:
		c.execute('''INSERT INTO wholesome_users 
			(username)
			VALUES (?)''', (redditObject.parent().author.name,))
	conn.commit()


def createView():
	c.execute('''CREATE VIEW IF NOT EXISTS wholesome_score AS 
		SELECT wholesome_users.username username, SUM(wholesome_coining.award) total_coins
		FROM wholesome_users INNER JOIN wholesome_coining
		ON wholesome_users.username = wholesome_coining.receiver_username
		GROUP BY wholesome_users.username
		''')


def isObjectValid(redditObject):
	if redditObject.author == None:
		#print('False because redditObject.author == None')
		return False
	if redditObject.parent().author == None:
		#print('False because redditObject.parent().author == None')
		return False
	if redditObject.body == '[deleted]':
		#print('False because redditObject.body == [deleted]')
		return False
	else:
		return True

def qFinder(redditObject):
	#print('STARTING qFinder')
	global repliesSent
	copy = redditObject.body.lower().translate(str.maketrans('','',string.punctuation[1:])) #removes punctuation EXCEPT FOR ! which is at index 0 of string.punctuation
	if SEARCHcoin in copy.split():
		if redditObject.author == redditObject.parent().author: 
			#Rule to TAKE coins if the user tried to reward themselves
			coinScore = coinPenalty(redditObject)	
			sendReply(redditObject, coinScore, DENY_TEXT)
		elif redditObject.author != redditObject.parent().author and isObjectValid(redditObject) == True:
			#Rule to GIVE coins
			#also adds coining action to wholesome_coining table (coiningTracker)			
			coinScore = coinGiver(redditObject) 
			sendReply(redditObject, coinScore, AWARD_TEXT)
	#elif SEARCHcoin not in copy.split():
	#	pass
### WORKING IN PROGRESS
	#if SEARCHscore in copy.split()
		#user check's their score
	#	coinScore = scoreCheck(redditObject)
	#	sendReply(redditObject, coinScore, SCORE_TEXT)
	#	pass
	return
		


def coinGiver(redditObject): #awards Coins for users who are wholesome. Opposite of coinPenalty
#1 - IF the parent is not already tracked in users table, add to table
	wholesomeUserTracker(redditObject)
#2- record the coining action in coining table
	coiningTracker(redditObject, coinUp)
#3 - Get user's coinScore	
	c.execute('SELECT total_coins FROM wholesome_score WHERE username=(?)',(redditObject.parent().author.name,))
	coinScore = c.fetchone()
	coinScore = round(coinScore[0],2)
	return coinScore



def coinPenalty(redditObject): #deducts Coins for users who try to abuse. Opposite of coinGiver
	global coinsGiven #TODO: remove for production
	coinScore = 0
#1 - IF the parent is not already tracked in users table, add to table
	wholesomeUserTracker(redditObject)
#2- Get user's coinScore and define the penalty
	c.execute('SELECT total_coins FROM wholesome_score WHERE username=(?)',(redditObject.parent().author.name,))
	coinScore = c.fetchone()
	if coinScore == None or coinScore[0] == 0:
		penalty = 0
		coinScore = 0.0
	else:
		penalty = (coinScore[0]/2)*-1
		coinScore = round(coinScore[0],2)
#3- record the coining action in coining table.
	coiningTracker(redditObject, penalty) #uses penalty instead of award
	return coinScore


def sendReply(redditObject, coinScore, replyText): #replies to the post
	global lastPostTime
	global repliesSent
	now = int(time.time())
	if redditObject._submission not in repliesSent: #before tracking replies sent, checks to see if the submission hasan entry
		repliesSent[redditObject._submission] =0
	if repliesSent[redditObject._submission] < REPLYLIMIT:
		if now - lastPostTime > POSTINTERVAL: #requires the last post to be at least 6 seconds ago
			c.execute('SELECT replied_to FROM wholesome_coining WHERE comment_id =(?)', (redditObject.id,))
			coinData = c.fetchone() #coinData is a touple
			if	coinData[0] == False: #checks to see if this comment has been replied to or not.
######## #Uncommet the next line to enable replies !!GOES LIVE!!
				redditObject.reply(replyText.format(redditObject.parent().author, coinScore))
				logFile.write(replyText)
				lastPostTime = int(time.time())
				repliesSent[redditObject._submission] += 1
				c.execute('''
					UPDATE wholesome_coining
					SET replied_to = (?)
					WHERE comment_id=(?)''', (True, redditObject.id, ))
				conn.commit()
			else:
				pass
				#print('Didn\'t send reply because already replied')
		else:
			pass
			#print('Didn\'t send reply because (Now-lastPostTime)=',(now - lastPostTime))
	else:
		pass
		#print('Didn\'t reply because already {} replies in this submission'.format(repliesSent[redditObject._submission]))


def scoreCheck(redditObject):
	pass



#=============POGRAM START=========

createTable()
createView()

#reddit instance
if not os.path.exists('logs'):
	os.makedirs('logs')


print('Getting reddit instance...')
reddit = praw.Reddit(
	user_agent='Wholesome Coin (by /u/Didusayabelincoln)',
	client_id='WhFzg-ZtBJZghg',
	client_secret='bCTO22tmD4in3BDtSwBJlM8qlBE',
	username='wholesomecoinbot',
	password=str(sys.argv[1]) #TODO: change password to pw 
	)
print('..done getting reddit instance!')

subCount = 0
subredRuns = 0


while True:
	today = '{}-{}-{}'.format(time.strftime('%m'),time.strftime('%d'),time.strftime('%y'))
	try:
		pfile = open("replies.pickle", "rb")
		repliesSent = pickle.load(pfile)
	except (OSError, IOError) as e:
		repliesSent = {}
	logFile = open('logs/log_{}.txt'.format(today), 'a+')
	startTime = time.time()
	ranHot = []
	ranNew = []
	for subreddit in SUBREDDITS_WHITELIST[:]:
		#print('Getting subreddit:', subreddit)
		subreddit = reddit.subreddit(subreddit)
# ----------program, for HOT-------------------------------------------------------
		for subIndex, submission in enumerate(subreddit.hot(limit=HOT_SUBSTORUN)):
			#logFile.write('\nRunning in Hot: {}'.format(submission.title))
			submission.comments.replace_more(limit=5) #removes MoreComments objects
			for indexx, redditObject in enumerate(submission.comments.list()):
				qFinder(redditObject)
			ranHot.append('{}: {}'.format(subreddit.title,submission.title))
			#print('pretend replies sent', repliesSent[submission])
			subCount += 1	
# ----------same, but for new-----------------------------------------------------
		for subIndex, submission in enumerate(subreddit.new(limit=NEW_SUBSTORUN)):
			#print('===starting "{}" ==='.format(submission.title))
			#logFile.write('\nRunning in New: {}'.format(submission.title))
			submission.comments.replace_more(limit=5) #removes MoreComments objects
			for indexx, redditObject in enumerate(submission.comments.list()):
				qFinder(redditObject)
			ranNew.append('{}: {}'.format(subreddit.title,submission.title))
			subCount += 1
# --------------------------------------------------------------------------------
		#print('Scanned the following submissions in HOT:\n')
		#for index, submission in enumerate(subreddit.hot(limit=HOT_SUBSTORUN)):
		#	print(index+1, submission.title)
#------------------		
		#print('Scanned the following submissions in NEW:\n')
		#for index, submission in enumerate(subreddit.new(limit=NEW_SUBSTORUN)):
		#	print(index+1, submission.title)
#------------------
		subredRuns += 1
	
	timeTaken = round((startTime - time.time())*-1,2)
	logFile.write('\n\n================================')
	logFile.write('\nRunthrough summary:')
	logFile.write('\nCompleted at: {}'.format(time.strftime('%X %x')))
	logFile.write('\nRuntime: {}s'.format(timeTaken))
	logFile.write('\nsubredRuns #: {}'.format(subredRuns))
	logFile.write('\nHOT submissions run:\n')
	logFile.write(pprint.pformat(ranHot))
	logFile.write('\nNEW submission run:\n')
	logFile.write(pprint.pformat(ranNew))
	logFile.write('\nSent replies to:\n')
	logFile.write(pprint.pformat(repliesSent))
	logFile.write('\n================================')
		
	logFile.close()
	pfile = open("replies.pickle","wb")
	pickle.dump(repliesSent, pfile)
	pfile.close()
#loop goes back to beginning


c.close()
conn.close()
