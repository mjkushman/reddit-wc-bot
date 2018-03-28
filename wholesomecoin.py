#! reddit wholesome coin bot. Monitors a subreddit 
#and hands out Wholesome Coin #when someone says !wholesomecoin


import praw, pprint, datetime, sqlite3, string, time, sys



conn = sqlite3.connect('wholesomeCoin.db')
c = conn.cursor()


SEARCHQ = 'you' #must be lowercase
REPLY_TEXT= '\nHere\'s +1 WholesomeCoin for u/{}!\n\nCurrent wholesome coinage: **{}**.\n\n*****\n\n*^Bleep ^bloop. ^How\'s ^your ^day?*'
HOTSUBSTORUN = 0  #number of HOT submissions to check in each subreddit
NEWSUBSTORUN = 20  #number of NEW submissions to check in each subreddit
#SUBREDDITS_WHITELIST = ['AskReddit','testingground4bots','todayilearned']
SUBREDDITS_WHITELIST = ['testingground4bots']
DENY_TEXT= 'Hey don\'t do that!\nI\'m taking away half your WholesomeCoins :(\n\n*****\n\n*^Bleep ^bloop. ^How\'s ^your ^day?*'
coinsGiven = 0 #keeps track of how many coins given out per script run
coinUp = 1 #how many coins a user should get
lastPostTime = int(time.time())
POSTINTERVAL = 60 #how long to wait between replies, in seconds
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
	#print('executing wholesomeUserTracker')
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

#def forestExplorer(redditObject):
#	commentAuthor = redditObject.author #define the object's author
#	parentComment = redditObject.parent() #define the object's parent
#	parentCommentAuthor = parentComment.author #define the object's parent's author
#	bodyCopy = redditObject.body.lower() #make text lowercase
#	qFinder(redditObject)
#	return

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
	copy = redditObject.body.lower().translate(str.maketrans('','',string.punctuation)) #removes punctuation
	if SEARCHQ in copy.split():
		#print('object:')
		#pprint.pprint(vars(redditObject))
		#print('parent:')
		#pprint.pprint(vars(redditObject.parent()))
		#print('valid test:', isObjectValid(redditObject))

		if redditObject.author == redditObject.parent().author: #Will TAKE coins if the user tried to reward themselves
			
			c.execute('SELECT comment_id FROM wholesome_coining')
			coinData = c.fetchall() #coinData is a list of touples
			commentIdList = [t[0] for t in coinData]
			if redditObject.id not in commentIdList:
				#pprint.pprint(vars(redditObject))
				
				#pprint.pprint(vars(redditObject.parent()))
				coinScore = coinPenalty(redditObject)
				print(DENY_TEXT)
				print('Pretend Reply Sent! (- coins)')
				#sendReply(redditObject, parent, coinScore)
				repliesSent += 1


		elif redditObject.author != redditObject.parent().author and isObjectValid(redditObject) == True:			 #Will GIVE coins

			
			coinScore = coinGiver(redditObject) #also adds coining action to wholesome_coining table (coiningTracker)
							
			
				
			sendReply(redditObject, coinScore)
	elif SEARCHQ not in copy.split():
		pass
	return
		


def coinGiver(redditObject):
	#print('STARTING coinGiver')
#1- record the coining action in coining table
	coiningTracker(redditObject, coinUp)
#2 - IF the parent is not already tracked in users table, add to table
	wholesomeUserTracker(redditObject)
	#coinScore = 0
	c.execute('SELECT total_coins FROM wholesome_score WHERE username=(?)',(redditObject.parent().author.name,))
	coinScore = c.fetchone()
	coinScore = round(coinScore[0],2)
	return coinScore

def sendReply(redditObject, coinScore):
	#print('starting SENDREPLY')
	global lastPostTime
	global repliesSent
	now = int(time.time())
	if repliesSent < REPLYLIMIT:
		if now - lastPostTime > POSTINTERVAL: #requires the last post to be at least 6 seconds ago
			c.execute('SELECT replied_to FROM wholesome_coining WHERE comment_id =(?)', (redditObject.id,))
			coinData = c.fetchone() #coinData is a touple
			if	coinData[0] == False: #checks to see if this one has been replied to or not.
				#Uncommet the next line to enable replies !!GOES LIVE!!
				redditObject.reply(REPLY_TEXT.format(redditObject.parent().author, coinScore))
				print('Pretend Reply Sent! (+ coin)')
				lastPostTime = int(time.time())
				repliesSent += 1
				c.execute('''UPDATE wholesome_coining
					SET replied_to = (?)
					WHERE comment_id=(?)''', (True, redditObject.id, ))
				conn.commit()
			else:
				print('Didn\'t send reply because already replied')
		else:
			print('Didn\'t send reply because Now - lastPostTime =',(now - lastPostTime))

def coinPenalty(redditObject):
	#print('STARTING coinPenalty')
	global coinsGiven #TODO: remove for production
	coinScore = 0
#1 - IF the parent is not already tracked in users table, add to table
	parent = redditObject.parent().author.name
	c.execute('SELECT username FROM wholesome_users')
	coinData = c.fetchall() #coinData is a list of touples
	authorsList = [t[0] for t in coinData]
	if parent not in authorsList:
		wholesomeUserTracker(redditObject)
		coinScore = 0

#2- record the coining action in coining table. In this case, 0 coins were awarded.
#2.1 define the penalty

	c.execute('SELECT username, total_coins FROM wholesome_score WHERE username = (?)', (parent,))
	coinData = c.fetchall()
	
	if len(coinData) > 0:
		penalty = ((coinData[0][1])/2)*-1
	else:
		penalty = 0
	print('PENALTY:', penalty)
	coiningTracker(redditObject, penalty)

	
	return

#=============POGRAM START=========

createTable()
createView()

#reddit instance

print('Getting reddit instance...')
reddit = praw.Reddit(
	user_agent='Wholesome Coin (by /u/Didusayabelincoln)',
	client_id='WhFzg-ZtBJZghg',
	client_secret='bCTO22tmD4in3BDtSwBJlM8qlBE',
	username='wholesomecoinbot',
	password=str(sys.argv[1]) #TODO: change password to pw 
	)
print('..done getting reddit instance!')

#subreddit = reddit.subreddit('testingground4bots').hot(limit=15)
#for submission in subreddit.stream.submissions():
subCount = 0
subredRuns = 0

while True:
	for subreddit in SUBREDDITS_WHITELIST[:]:
		#subreddit = 'testingground4bots' #here temporarily
		
		print('Getting subreddit:', subreddit)
		subreddit = reddit.subreddit(subreddit)
		#for submission in subreddit.stream.submissions(): #TODO: use this version for stream of new
# ----------program, for HOT-------------------------------------------------------
		for subIndex, submission in enumerate(subreddit.hot(limit=HOTSUBSTORUN)):
			repliesSent = 0 #resets replies to 0. track replies per submission
			print('===starting "{}" ==='.format(submission.title))

			submission.comments.replace_more(limit=5) #removes MoreComments objects

			for indexx, redditObject in enumerate(submission.comments.list()):
				qFinder(redditObject)	
				#pprint.pprint(vars(comment)) #FOR DEBUG
				
			print('pretend replies sent', repliesSent)
			subCount = subIndex +1	
# ----------same, but for new-----------------------------------------------------
		for subIndex, submission in enumerate(subreddit.new(limit=NEWSUBSTORUN)):
			repliesSent = 0 #track replies per submission
			print('===starting "{}" ==='.format(submission.title))

			submission.comments.replace_more(limit=5) #removes MoreComments objects

			for indexx, redditObject in enumerate(submission.comments.list()):
				qFinder(redditObject)	
				#pprint.pprint(vars(comment)) #FOR DEBUG
				
			print('pretend replies sent', repliesSent)
			subCount = subIndex +1	
# --------------------------------------------------------------------------------
		print('Scanned the following submissions in HOT:\n')
		for index, submission in enumerate(subreddit.hot(limit=HOTSUBSTORUN)):
			print(index+1, submission.title)
#------------------		
		print('Scanned the following submissions in NEW:\n')
		for index, submission in enumerate(subreddit.new(limit=NEWSUBSTORUN)):
			print(index+1, submission.title)
#------------------
		print('\n!!Completed {} submissions in {} and gave out {} WholesomeCoins!!'.format(subCount, subreddit, coinsGiven))
		subredRuns += 1
		print('subredRuns currently at:', subredRuns)


c.close()
conn.close()

#RESULTS: 
#	Bot found a new submission, but did not find a qualifying new comment on that submission 
#	after it ran through the initial submission. Didn't find a new reply with 'test' in it

#	Proposed new solution is to write the script so that it looks through the top 50 posts and
# 	all their comments and replies. Then hands out coins. Then repeats this process every minute.
#	Another script or process is needed to run this script every minute

#TODO: Wrap everything in a While function and make it sleep 60 secs at the end:

#while True:
#	ENTIRE PROGRAM
#	time.sleep(60)


