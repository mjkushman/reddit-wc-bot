#! reddit wholesome coin bot. Monitors a subreddit 
#and hands out Wholesome Coin #when someone says !wholesomecoin


import praw, pprint, datetime, sqlite3, string, time, sys



conn = sqlite3.connect('wholesomeCoin.db')
c = conn.cursor()


SEARCHQ = 'bot' #must be lowercase
REPLY_TEXT= '\nHere\'s +1 WholesomeCoin for u/{}!\nCurrent wholesome coinage: {}.\n\nBleep bloop. If I did something wrong, please message my developer.'
SUBSTORUN = 5
DENY_TEXT= 'Hey don\'t do that!\nI\'m taking away half your WholesomeCoins :(\n\nBleep bloop. If I did something wrong, please message my developer. '
coinsGiven = 0 #keeps track of how many coins given out per script run
coinUp = 1 #how many coins a user should get


'''#TODO: Prevent multiple coins from being given out for the same !wholesomecoin comment
	Add a column to the table that records the comment ID. 
	Each row in the table should be a time a coin was given out, comment ID being unique ident
	If the comment ID already exists, that means a coin was already given out for that comment.


'''
#Creates the table to keep track of everyone's coins
#Create the following tables:
#wholesome_coining; wholesome_users; coinned_comments; wholesome_score
def createTable():
	c.execute('''CREATE TABLE IF NOT EXISTS wholesome_coining(
		comment_id TEXT NOT NULL, 
		giver_username TEXT, 
		parent_comment_id TEXT, 
		receiver_username TEXT, 
		award REAL, 
		PRIMARY KEY(comment_id))'''
		)
	
	c.execute('''CREATE TABLE IF NOT EXISTS wholesome_users(
		username TEXT NOT NULL, 
		PRIMARY KEY(username))
		''')
	c.execute('''CREATE TABLE IF NOT EXISTS wholesome_comments(
		comment_id TEXT NOT NULL,
		PRIMARY KEY(comment_id))
		''')
	
#	c.execute('''CREATE TABLE IF NOT EXISTS wholesome_score( 
#		username TEXT NOT NULL, 
#		score REAL,
#		PRIMARY KEY(username))
#		''')

def coiningTracker(redditObject):
	#record all coining actions in the main table
	c.execute('''INSERT INTO wholesome_coining 
		(comment_id, giver_username, parent_comment_id, receiver_username, award) 
		VALUES (?,?,?,?,?)''', (redditObject.id, redditObject.author.name, redditObject.parent().id, redditObject.parent().author.name,coinUp,))
	conn.commit()

def wholesomeUserTracker(redditObject):
	c.execute('''INSERT INTO wholesome_users 
		(username)
		VALUES (?)''', (redditObject.author,))
	conn.commit()


def createView():
	c.execute('''CREATE VIEW IF NOT EXISTS wholesome_score AS SELECT
		wholesome_users.username AS username, 
		wholesome_coining.award AS total_coins
		FROM wholesome_users, wholesome_coining
		WHERE wholesome_users.username = wholesome_coining.receiver_username''')

def forestExplorer(redditObject):
	commentAuthor = redditObject.author #define the object's author
	parentComment = redditObject.parent() #define the object's parent
	parentCommentAuthor = parentComment.author #define the object's parent's author
	bodyCopy = redditObject.body.lower() #make text lowercase
	qFinder(bodyCopy, commentAuthor, parentCommentAuthor, redditObject)
	return

def qFinder(copy, author, parent, redditObject):
	print('STARTING qFinder')
	#print('qFinder:', copy, author, parent, redditObject)
	copy = copy.translate(str.maketrans('','',string.punctuation)) #removes punctuation
	if SEARCHQ in copy.split():
		if author != parent:			 #Will GIVE coins
			c.execute('SELECT comment_id FROM wholesome_coining')
			coinData = c.fetchall() #coinData is a list of touples
			commentIdList = [t[0] for t in coinData]
			if redditObject.id not in commentIdList:
				coinScore = int(coinGiver(parent, redditObject))
				print(REPLY_TEXT.format(parent, coinScore))
			#sendReply(redditObject, parent, coinScore)
		else: 								#Will TAKE coins
			coinScore = int(coinPenalty(parent, redditObject))
			print(DENY_TEXT)
			#sendReply(redditObject, parent, coinScore)
			#TODO: do NOT give a coin and punish the user!
			#TODO: add functionality that punishes users for giving themselves wholesomecoins


def coinGiver(author, redditObject):
	print('STARTING coinGiver')
	global coinsGiven #TODO: remove for production
	author = str(author)
	coinsGiven += 1 #TODO: remove for prod

#1- record the coining action in coining table
	coiningTracker(redditObject)	
		
#2 - record the coinned comment

#3 - IF the author is not already tracked in users table, add to table
	c.execute('SELECT username FROM wholesome_users')
	coinData = c.fetchall() #coinData is a list of touples
	authorsList = [t[0] for t in coinData]
	coinScore = 0
	if author not in authorsList:
		c.execute("INSERT INTO wholesome_users (username) VALUES (?)", (author,))
		#c.execute("INSERT INTO wholesome_coins (username, total_coins) VALUES (?,?)", (author, coinUp,))
		#c.execute("INSERT INTO wholesome_coining (username, total_coins) VALUES (?,?)", (author, coinUp,))
		conn.commit()
		coinScore = coinUp
	else: #actually I don't need this else statement
#		print('author found. increasig coinage.')
#		print(authorsList)
#		print(authorsList.index(author))
#		print(coinData[authorsList.index(author)][1])

#		coinScore = round(coinData[authorsList.index(author)][1] +coinUp) #new coin score of author
		#Updates the coin score to be current coins + 1 / coinScore
		#c.execute("UPDATE wholesome_coins SET coins = ? WHERE username = ?", (coinScore, author,))
		#conn.commit()
		pass
	return coinScore
			
		
def sendReply(redditObject, parent, coinScore):
	#TODO set up function that replies to the message
	redditObject.reply(REPLY_TEXT.format(parent, coinScore))
	time.sleep(10)


def coinPenalty(author, redditObject):
	print('STARTING coinPenalty')
	global coinsGiven #TODO: remove for production
	author = str(author)
	#c.execute('SELECT username, coins FROM wholesome_coins')
	coinData = c.fetchall() #coinData is a list of touples
	authorsList = [t[0] for t in coinData]
	coinScore = 0
	
	if author not in authorsList:
		#c.execute("INSERT INTO wholesome_coins (username, coins) VALUES (?,?)", (author, coinUp,))
		#conn.commit()
		coinScore = 0
	else:
#		print('author found. increasig coinage.')
#		print(authorsList)
#		print(authorsList.index(author))
#		print(coinData[authorsList.index(author)][1])

		coinScore = round(coinData[authorsList.index(author)][1] / 2) #new coin score of author
		#Updates the coin score to be current coins + 1 / coinScore
		#c.execute("UPDATE wholesome_coins SET coins = ? WHERE username = ?", (coinScore, author,))
		#conn.commit()
	return coinScore

createTable()
createView()

#reddit instance
#pw = input('bot password: ') TODO: uncomment for password input

print('Getting reddit instance...')
reddit = praw.Reddit(
	user_agent='Wholesome Coin (test) (by /u/Didusayabelincoln)',
	client_id='Ks5H9hq3zDAbfg',
	client_secret='T0UGg53thEw-NRvDiB4yzAotWlw',
	username='Didusayabelincoln',
	password=str(sys.argv[1]) #TODO: change password to pw 
	)
print('..done getting reddit instance!')

print('Getting subreddit object...')
subreddit = reddit.subreddit('testingground4bots')
print('..done getting subreddit object!')
#subreddit = reddit.subreddit('testingground4bots').hot(limit=15)
#for submission in subreddit.stream.submissions():

subCount = 0
#for submission in subreddit.stream.submissions(): #TODO: use this version for stream of new
for subIndex, submission in enumerate(subreddit.hot(limit=SUBSTORUN)):
	commentCount = 0
	print('===starting "{}"==='.format(submission.title))
#	print('New submission found:', submission.title)
#	print(submission.author)
	submission.comments.replace_more(limit=None) #removes MoreComments objects

#	Need to turn this into a while loop, and loop while there are replies to be looped on

	for indexx, comment in enumerate(submission.comments.list()):
		#print()
		#print('{}C  -- Found a comment in {} --'.format((indexx+1), submission.title))
		forestExplorer(comment)
		print(comment)
		print(comment.author)
		#pprint.pprint(vars(comment)) #FOR DEBUG
		commentCount += 1	

#	print('Completed submission: {}'.format(submission.title))
#	print('Ran on {} comments to {}'.format(commentCount, submission.author))	
	subCount = subIndex +1	


print('Scanned the following submissions:\n')
for submission in subreddit.hot(limit=SUBSTORUN):
	print(submission.title)
print('\n!!Completed {} submissions and gave out {} WholesomeCoins!!'.format(subCount, coinsGiven))



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


