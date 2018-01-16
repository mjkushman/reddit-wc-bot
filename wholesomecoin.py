#! reddit wholesome coin bot. Monitors a subreddit 
#and hands out Wholesome Coin #when someone says !wholesomecoin


import praw

#reddit instance
pw = input('bot password: ')
reddit = praw.Reddit(
	user_agent='Wholesome Coin (test) (by /u/Didusayabelincoln)',
	client_id='Ks5H9hq3zDAbfg',
	client_secret='	T0UGg53thEw-NRvDiB4yzAotWlw',
	username='Didusayabelincoln',
	password=pw
	)

#test to see if bot is in read only state
#print(reddit.read_only)

subreddit = reddit.subreddit('testingground4bots')
#for submission in subreddit.stream.submissions():

print(subreddit.display_name)
#print(subreddit.title)