#! reddit wholesome coin bot. Monitors a subreddit 
#and hands out Wholesome Coin #when someone summons the bot explicitly.
#Currently very much a work in progress. Expect messy code and notes"


import praw, pprint, datetime, sqlite3, string, time, sys


conn = sqlite3.connect('wholesomeCoin.db')
c = conn.cursor()


SEARCHQ = '!secretkeyword' #must be lowercase
AWARD_TEXT= '\n+1 WholesomeCoin for u/{}!\nCurrent wholesome coinage: **{}**.\n\n*****\n\n*^Bleep ^bloop. ^How ^are ^you? ^I\'m ^a ^work ^in ^progress. ^| [^message ^me](https://reddit.com/message/compose/?to=wholesomecoinbot)^| [^Info ^placeholder](https://google.com) ^|*'
HOT_SUBSTORUN = 20  #number of HOT submissions to check in each subreddit
NEW_SUBSTORUN = 20  #number of NEW submissions to check in each subreddit
#SUBREDDITS_WHITELIST = ['AskReddit','testingground4bots','todayilearned']
SUBREDDITS_WHITELIST = ['testingground4bots']
DENY_TEXT= 'Hey don\'t do that!\nI\'m taking away half your WholesomeCoins :(\n\n*****\n\n*^Bleep ^bloop. ^How ^are ^you? ^I\'m ^a ^work ^in ^progress. ^| [^message ^me](https://reddit.com/message/compose/?to=wholesomecoinbot)^| [^Info ^placeholder](https://google.com) ^|*'
coinsGiven = 0 #keeps track of how many coins given out per script run
coinUp = 1 #how many coins a user should get
POSTINTERVAL = 60 #how long to wait between replies, in seconds
lastPostTime = POSTINTERVAL
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
	if SEARCHQ in copy.split():
		#print('object:')
		#pprint.pprint(vars(redditObject))
		#print('parent:')
		#pprint.pprint(vars(redditObject.parent()))
		#print('valid test:', isObjectValid(redditObject))

		if redditObject.author == redditObject.parent().author: #Will TAKE coins if the user tried to reward themselves
			
			#c.execute('SELECT comment_id FROM wholesome_coining')
			#coinData = c.fetchall() #coinData is a list of touples
			#commentIdList = [t[0] for t in coinData]
			#if redditObject.id not in commentIdList:
				#pprint.pprint(vars(redditObject))
				
				#pprint.pprint(vars(redditObject.parent()))
			coinScore = coinPenalty(redditObject)
				
			sendReply(redditObject, coinScore, DENY_TEXT)

			#remove ---- below
				#print(DENY_TEXT)
				#print('Pretend Reply Sent! (- coins)')
				#sendReply(redditObject, parent, coinScore)
				#repliesSent[redditObject._submission] += 1
			#------- til here	

		elif redditObject.author != redditObject.parent().author and isObjectValid(redditObject) == True:			 #Will GIVE coins

			
			coinScore = coinGiver(redditObject) #also adds coining action to wholesome_coining table (coiningTracker)
							
			
				
			sendReply(redditObject, coinScore, AWARD_TEXT)
	elif SEARCHQ not in copy.split():
		pass
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
		print('if triggered')
		penalty = 0
		coinScore = 0.0
	else:
		print('elif2 triggered')
		penalty = (coinScore[0]/2)*-1
		coinScore = round(coinScore[0],2)
		
	print('PENALTY:', penalty) #remove for prod

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
				#Uncommet the next line to enable replies !!GOES LIVE!!
				redditObject.reply(replyText.format(redditObject.parent().author, coinScore))
				print('Pretend Reply Sent!')
				print(replyText)
				lastPostTime = int(time.time())
				repliesSent[redditObject._submission] += 1
				c.execute('''UPDATE wholesome_coining
					SET replied_to = (?)
					WHERE comment_id=(?)''', (True, redditObject.id, ))
				conn.commit()
			else:
				print('Didn\'t send reply because already replied')
		else:
			print('Didn\'t send reply because (Now-lastPostTime)=',(now - lastPostTime))
	else:
		print('Didn\'t reply because already 5+ replies in this submission')


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
repliesSent = {}

while True:
	for subreddit in SUBREDDITS_WHITELIST[:]:
		#subreddit = 'testingground4bots' #here temporarily
		
		print('Getting subreddit:', subreddit)
		subreddit = reddit.subreddit(subreddit)
		#for submission in subreddit.stream.submissions(): #TODO: use this version for stream of new
# ----------program, for HOT-------------------------------------------------------
		for subIndex, submission in enumerate(subreddit.hot(limit=HOT_SUBSTORUN)):
			#repliesSent = 0 #resets replies to 0. track replies per submission
			#repliesSent[submission] =0
			print('===starting "{}" ==='.format(submission.title))

			submission.comments.replace_more(limit=5) #removes MoreComments objects

			for indexx, redditObject in enumerate(submission.comments.list()):
				qFinder(redditObject)	
				#pprint.pprint(vars(comment)) #FOR DEBUG
				
			#print('pretend replies sent', repliesSent[submission])
			subCount = subIndex +1	
# ----------same, but for new-----------------------------------------------------
		for subIndex, submission in enumerate(subreddit.new(limit=NEW_SUBSTORUN)):
			#repliesSent[submission] = 0 #track replies per submission
			print('===starting "{}" ==='.format(submission.title))

			submission.comments.replace_more(limit=5) #removes MoreComments objects

			for indexx, redditObject in enumerate(submission.comments.list()):
				qFinder(redditObject)
				#pprint.pprint(vars(comment)) #FOR DEBUG
				
			#print('pretend replies sent', repliesSent[submission])
			subCount = subIndex +1	
# --------------------------------------------------------------------------------
		print('Scanned the following submissions in HOT:\n')
		for index, submission in enumerate(subreddit.hot(limit=HOT_SUBSTORUN)):
			print(index+1, submission.title)
#------------------		
		print('Scanned the following submissions in NEW:\n')
		for index, submission in enumerate(subreddit.new(limit=NEW_SUBSTORUN)):
			print(index+1, submission.title)
#------------------
		print('\n!!Completed {} submissions in {} and gave out {} WholesomeCoins!!'.format(subCount, subreddit, coinsGiven))
		pprint.pprint(repliesSent)
		subredRuns += 1
		print('subredRuns currently at:', subredRuns)


c.close()
conn.close()
