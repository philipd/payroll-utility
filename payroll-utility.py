#ShiftPlanning API

import requests,json,urllib,urllib.request,urllib.parse,datetime,os
from datetime import timedelta

api_key = os.environ['SHIFTPLANNING_API_KEY']
api_url = 'http://www.shiftplanning.com/api/'

data = { 'key': api_key, 'output': 'json', 'request': {'module':'api.config'} }
headers = {'content-type': 'application/x-www-form-urlencoded'}

querycache = {}

ktotalhours = 0
stotalhours = 0
ktotaltips = 0
stotaltips = 0

#API query caching TODO
def cachequery():
    return null

#Get shift as a readable string
def shiftstring(shift):
    return shift['employeename'] + '\t' + shift['date'] + '\t' + str(shift['length']) + ' hours'

#Simplify API requests
def query(data):
    r = requests.post(api_url, data='data='+json.dumps(data), headers=headers)
    response = r.json()['data']
    return response

#Allow to search array of dicts
def search(array, field, value):
	return (item for item in array if item[field] == value).__next__()

#Custom rounding
def myround(x, base=5):
    return int(base * round(float(x)/base))

#Authentication
def gettoken(name, pw):
	data = {
	  "key": api_key,
	  "output": "json",
	  "request": {
	    "module": "staff.login",
	    "method": "GET",
	    "username": uname,
	    "password": pw
	  }
	}

	r = requests.post(api_url, data='data='+json.dumps(data), headers=headers)
	token = r.json()['token']
	   
	return token

#Get employee unique id by name
def uid(name):
    data = {
        "module":"staff.employees",
        "method":"GET",
        "request":{
           'token': token
           }
    }
    
    response = query(data)

    for entry in response:
        if entry['name'] == name:
            return entry['id']

#Get employee eid by name
def eid(name):
    data = {
        "module":"staff.employees",
        "method":"GET",
        "request":{
           'token': token
           }
    }
    
    response = query(data)

    for entry in response:
        if entry['name'] == name:
            return entry['eid']

#Get employee name by unique id
def name(uid):
    data = {
       "module":"staff.employee",
       "method":"GET",
       "request":{
           'token': token,
            "id":str(uid)
        }
    }

    response = query(data)
    
    return response['name']

#Get location name by location id
def locationname(locationid):
    data = {
       "module":"location.locations",
       "method":"GET",
       "request":{
            'token': token,
            "type":"1"
       }
    }

    response = query(data)

    for entry in response: 
        if entry['id'] == locationid:
            return entry['name']

#Get location id by location name
def locationid(locationname):
    data = {
       "module":"location.locations",
       "method":"GET",
       "request":{
            'token': token,
            "type":"1"
       }
    }

    response = query(data)
    for entry in response: 
        if entry['name'] == locationname:
            return entry['id']

#Get employee location id by unique id
def emplocation(uid):

    #Create a dict of locations

    data = {
       "module":"location.locations",
       "method":"GET",
       "request":{
            'token': token,
            "type":"1"
       }
    }

    response = query(data)
    
    locations = {}

    for entry in response: 
        locations[entry['name']] = entry['id']

    #Search employees by location
    
    for location in locations:        
        data = {
           "module":"staff.employees",
           "method":"GET",
           "request":{
               'token': token,
               "location": locations[location]
           }
        }

        response = query(data)

        for entry in response: 
            if entry['id'] == uid:
                return locations[location]

#Get Employees by location
def getempsbyloc(locationid):      
	data = {
	   "module":"staff.employees",

	   "method":"GET",
	   "request":{
	       'token': token,
	       "location": locationid
	   }
	}

	response = query(data)

	return response

#BUILD TIMESHEETS
def buildtimesheets():
	output = []
	
	data = {
	   "module":"timeclock.timeclocks",
	   "method":"GET",
	   "request":{
	       "token": token,
	       "start_date": (payperiodstartdate).strftime("%Y-%m-%d"),
	       "end_date": (payperiodenddate + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
	   }
	}

	response = query(data)

	for entry in response:
		uid = entry['employee']['id']
		name = entry['employee']['name']
		output.append	(
					{
						'employeename':name,
						'uid':uid,
						'date':entry['in_time']['day'],
						'length':entry['length']['total_hours'] if entry['length'] else 0,
                                                'complete':True if entry['length'] else False
					}
				)
	return output

#BUILD A TABLE OF LOCATION INFO
def buildlocations():
	output = []
	
	data = {
	   "module":"location.locations",
	   "method":"GET",
	   "request":{
		'token': token,
		"type":"1"
	   }
	}

	response = query(data)

	for entry in response: 
	    output.append(
				{
					'locationname':entry['name'],
					'locationid':entry['id']
				}
			)

	return output

#BUILD A TABLE OF EMPLOYEE INFO
def buildemployees():
	output = []

	data = {
	   "module":"staff.employees",
	   "method":"GET",
	   "request":{
	       'token': token
	   }
	}

	response = query(data)

	for entry in response:
	    output.append(
				{
					'employeename':entry['name'],
					'uid':entry['id'],
					'eid':entry['eid']
				}
			)
	
	return output

#BUILD TABLE WITH "JOINS"
def buildtable(timesheets, employees, locations):
	output = []

	for shift in timesheets:
		uid = shift['uid']
		name = shift['employeename']
		output.append	(
					{
						'employeename':name,
						'uid':uid,
						'date':shift['date'],
						'length':shift['length'],
            'complete':shift['complete']
					}
				)

	#Add each employee's eid to the table
	for shift in output:
		uid = shift['uid']
		employee = search(employees, 'uid', uid)
		eid = employee['eid']

		shift['eid'] = eid	

	#Add each employee's location data to the table
	for location in locations:
		empsbyloc = getempsbyloc(location['locationid'])
		
		for emp in empsbyloc:
			for shift in output:
				if shift['uid'] == emp['id']:
					shift['locationid'] = location['locationid']
					shift['locationname'] = location['locationname']
		

	return output

#AUTH

uname = input('uname:')
pw = input('pw:')

token = gettoken(uname, pw)

#GET INFO FROM USER
payperiodenddate = datetime.datetime.strptime(input('Last day of pay period? (YYYY-MM-DD):'),"%Y-%m-%d")
tiptotal = int(input('Total tip money?'))

payperiodstartdate = payperiodenddate - datetime.timedelta(days=13)

#BUILD A TABLE!

timesheets = buildtimesheets()
employees = buildemployees()
locations = buildlocations()
shifts = buildtable(timesheets, employees, locations)

#LOCATION TIP TOTALS

ktotaltips = tiptotal * 0.4
stotaltips = tiptotal * 0.6

#LOCATION TOTAL HOURS

for shift in shifts:
	if shift['locationname'] == 'Kitchen':
		ktotalhours += float(shift['length'])
	elif shift['locationname'] == 'Service':
		stotalhours += float(shift['length'])

#LOCATION TIP RATES

ktiprate = ktotaltips / ktotalhours
stiprate = stotaltips / stotalhours

print( stiprate )
print( ktiprate	)

##PRINT TOTAL HOURS AND TIPS

for employee in employees:
	employeetotalhours = 0
	for shift in shifts:
		if shift['uid'] == employee['uid']:
			employeetotalhours += float(shift['length'])
			locationname = shift['locationname']
			locationid = shift['locationid']
	employee['totalhours'] = employeetotalhours
	employee['locationname'] = locationname
	employee['locationid'] = locationid
	
	if employee['locationname'] == 'Service':
		employee['tiptotal'] = myround( stiprate * float(employee['totalhours']) )
	elif employee['locationname'] == 'Kitchen':
		employee['tiptotal'] = myround( ktiprate * float(employee['totalhours']) )
	else:
		employee['tiptotal'] = 0

	print( employee['employeename'] + '\t$' + str(employee['tiptotal']) + '\t' + '%.2f' % employee['totalhours'] )

######TESTS

print('\nIncomplete Shifts: ')
for shift in shifts:
    if not shift['complete']:
        print(shiftstring(shift))

print('\nUnusually Short Shifts: ')
for shift in shifts:
    if shift['complete'] and float(shift['length']) <= 0.5:
        print(shiftstring(shift))

print('\nUnusually Long Shifts: ')
for shift in shifts:
    if float(shift['length']) >= 12:
        print(shiftstring(shift))

for shift in shifts:
    print ( shift )

input('\n\nPress ENTER to quit')