#!/usr/bin/env python3

"""
Find the [git log] for each repo for each branch
"""

import os
import subprocess
import re
import sqlite3
from sqlite3 import Error
from dateutil.parser import parse 
from datetime import datetime

commits = {} 
now = datetime.now() 
basepath = "/Users/r621362/gitstuff/repos2/"
database = "/Users/r621362/gitstuff/sitereader/branch_activity.sqlite"

def parseGitLog_insertIntoDB(lines, repo_name, branch, conn):

    an_author = "undefined"
    a_date = "undefined"
    state = 0
    entry_count = 0

    with conn:
        for line in lines:
            x = line.decode("utf-8")
            commits = re.split("\n",x)
            if "Author: " in x: 
                an_author = x
                state = state + 1
            if "Date: " in x and state == 1:
                a_date = x
                state = state + 1
            if state == 2:
                entry_count += 1
                state = 0
                    
                #Author: Fname Lname <fname.lname@company.com>
                an_author = an_author.replace("Author:","")
                an_author = an_author.split("<")[0]
                an_author = an_author.strip()
                    
                #Date:   Mon Jun 26 14:26:35 2017 -0700
                a_date = a_date.replace("Date:","")
                a_date = a_date.strip()
                then = getDateObject_fromString(a_date)
                    
                #Get num of days ago...  Why here? Because Python > JS dates
                days_ago = ( now - then ).days
                    
                sql = "insert into repo_history(repo_name, branch, who, eventDate, days) values (?,?,?,?,?)"                               
                               
                cur = conn.cursor()
                cur.execute(sql, (repo_name, branch, an_author, then, days_ago))
                               
                #print("|{0}| >{1}<  {3}".format(repo_name, an_author, then, days_ago))
    print("{0} for {1} ".format(entry_count, repo_name))

def gitBranchAll():
    pwd = subprocess.check_output(['pwd'])
    branches = subprocess.run(['git', 'branch', '-a'], stdout=subprocess.PIPE)
    return branches

def gitCheckout(repo):
    subprocess.run(['git', 'checkout', repo], stdout=subprocess.PIPE)

        
def git_log(targetDir):
    gitlog = subprocess.run(['git','log'], stdout=subprocess.PIPE)
    return gitlog


def cd(targetDir):
    os.chdir(targetDir)
 
def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return None
 
def get_repo_names(conn):
    cur = conn.cursor()
    #cur.execute("select repo_name from repo_names where repo_name = 'cms-api'")
    cur.execute("select repo_name from repo_names")
    rows = cur.fetchall()
    return rows

def maybeCreateACommit(couldBeNewCommitBlock, candidate_line):
    # mini state machine 
    if couldBeNewCommitBlock.startswith( 'commit ' ): 
        commits[couldBeNewCommitBlock] = {} 
    
# param: string such as "Mon Jun 26 14:26:35 2017 -0700"
# i.e., EEE MMM d HH:mm:ss yyyy Z
def getDateObject_fromString(ugly_format):
    """
    Q: step1? step2? Because complication is good?!
    A: No. Sometimes these incoming ugly_format date strings which have 
    time zone info and sometimes they don't. Depending on whether 
    they do or don't = getting the delta in days is a headache - 
    Easier to just make sure that it isn't there... Hence step1 + step2. 
    """
    dateTimeObject_step1 = parse(ugly_format)
    y = dateTimeObject_step1.year
    m = dateTimeObject_step1.month
    d = dateTimeObject_step1.day
    dateTimeObject_step2 = datetime(y,m,d)
    return dateTimeObject_step2    
        
def main():
    
    
    conn = create_connection(database)

    repo_names = get_repo_names(conn)
    for tuple_contains_repo_name in repo_names:
        repo_name = tuple_contains_repo_name[0]
        # cd
        cd(basepath + repo_name)
        # branches
        raw_branches = gitBranchAll().stdout.splitlines()

        print("----------------------------------:REPO:  {0}".format(repo_name))
        branches = set()
        for b in raw_branches:
            x = b.decode('ascii')
            x = x.replace("* ","  ")
            x = x.strip()
            # now x will look something like: remotes/origin/pbuf_merge

            #get just the 'pbuf_merge'
            ary = x.split("/")
            x = ary[len(ary) - 1]

            #print("\t|{0}|".format(x))
            branches.add(x)

        for branch in branches:
            gitCheckout(branch)
                
            results = git_log(basepath + repo_name)
            lines = results.stdout.splitlines()
            #print("|{0}| has {1}".format(branch, len(lines)))
            parseGitLog_insertIntoDB(lines, repo_name, branch, conn)

   

if __name__ == '__main__':
    main()    
    
    
    
    





