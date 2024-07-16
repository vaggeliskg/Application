# ----- CONFIGURE YOUR EDITOR TO USE 4 SPACES PER TAB ----- #
import settings
import sys,os
sys.path.append(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'lib'))
import lib.pymysql as db
import random
from datetime import date, timedelta

def connection():
    ''' User this function to create your connections '''
    con = db.connect(
        settings.mysql_host, 
        settings.mysql_user, 
        settings.mysql_passwd, 
        settings.mysql_schema)
    
    return con

def  findTrips(x,a,b):
    # Query to retrieve trip details
    sql_trip = """
        SELECT distinct tp.cost_per_person, tp.max_num_participants, e.surname, e.name, tp.trip_start, tp.trip_end,tp.trip_package_id
        FROM travel_agency_branch t, reservation r, trip_package tp, guided_tour gt, employees e
        WHERE t.travel_agency_branch_id = '%s'
            AND t.travel_agency_branch_id = r.travel_agency_branch_id
            AND r.offer_trip_package_id = tp.trip_package_id
            AND tp.trip_package_id = gt.trip_package_id
            AND gt.travel_guide_employee_AM = e.employees_AM
            AND tp.trip_start>='%s'
            AND tp.trip_end<='%s'
    """ % (x, a, b)

    # Query to retrieve reservations count
    sql_reservations = """
        SELECT tp.trip_package_id, COUNT(r.Reservation_id) AS reservations
        FROM travel_agency_branch t, reservation r, trip_package tp
        WHERE t.travel_agency_branch_id='%s'
            AND t.travel_agency_branch_id=r.travel_agency_branch_id
            AND r.offer_trip_package_id=tp.trip_package_id
            AND tp.trip_start>='%s'
            AND tp.trip_end<='%s'
        GROUP BY tp.trip_package_id
    """ % (x, a, b)

    # Create a new connection
    con = connection()
    # Create a cursor on the connection
    cur = con.cursor()

    # Execute the trip query
    cur.execute(sql_trip)
    results_trip = cur.fetchall()

    # Execute the reservations query
    cur.execute(sql_reservations)
    results_reservations = cur.fetchall()

    list_of_tuples = []  # Create an empty list to store the tuples

    for row_trip in results_trip:
        cost_per_person = row_trip[0]
        max_num_participants = row_trip[1]
        guide_surname = row_trip[2]
        guide_name = row_trip[3]
        trip_start = row_trip[4]
        trip_end = row_trip[5]
        
        
        # Find the matching reservations count for the trip
        reservations = None
        for row_reservations in results_reservations:
            if row_reservations[0] == row_trip[6]:
                reservations = row_reservations[1]
                break
        empty_seats = max_num_participants-reservations
        touple = (cost_per_person, max_num_participants, reservations, empty_seats, guide_surname, guide_name, trip_start, trip_end)
        list_of_tuples.append(touple)  # Append each tuple to the list

    final_list = [
        ("cost_per_person", "max_num_participants", "reservations", "empty_seats", "guide_surname", "guide_name", "trip_start", "trip_end"),
    ] + list_of_tuples
    
    return final_list


def findRevenue(x):
    # General query
    sql_general="""SELECT t.travel_agency_branch_id, COUNT(r.Reservation_id) AS reservations, SUM(o.cost) AS total_income
    FROM travel_agency_branch t, reservation r, offer o
    WHERE t.travel_agency_branch_id=r.travel_agency_branch_id
        AND r.offer_id=o.offer_id
    GROUP BY t.travel_agency_branch_id
    ORDER BY total_income %s """%(x)

    # Employee query
    sql_employees="""SELECT t.travel_agency_branch_id, COUNT(e.employees_AM) AS employees, SUM(e.salary) AS total_salary
    FROM travel_agency_branch t, employees e
    WHERE t.travel_agency_branch_id = e.travel_agency_branch_travel_agency_branch_id
    GROUP BY t.travel_agency_branch_id"""

   # Create a new connection
    con=connection()
    
    # Create a cursor on the connection
    cur=con.cursor()

    # Execute general_sql
    cur.execute(sql_general)
    general_results=cur.fetchall()

    # Execute sql_employees
    cur.execute(sql_employees)
    employees_results=cur.fetchall()

    list_of_tuples = []
    for row in general_results:
        travel_agency_branch_id = row[0]
        total_num_reservations = row[1]
        total_income = row[2]
        
        # Find the matching employees count for the travel_agency_branch
        for row_employees in employees_results:
            if row_employees[0] == row[0]:
                total_num_employees = row_employees[1]
                total_salary = row_employees[2]
                break
        touple = (travel_agency_branch_id,total_num_reservations, total_income, total_num_employees, total_salary)
        list_of_tuples.append(touple)

    final_list = [
        ("travel_agency_branch_id", "total_num_reservations", "total_income", "total_num_employees", "total_salary"),
    ] + list_of_tuples

    return final_list

def bestClient(x):
    sql_traveler =  """ SELECT t.name, t.surname, SUM(o.cost) AS total_revenue, t.traveler_id
    FROM traveler t, reservation r, offer o
    WHERE t.traveler_id = r.Customer_id
        AND r.offer_id = o.offer_id
    GROUP BY t.traveler_id
    ORDER BY total_revenue DESC
    """
    sql_attraction =  """ SELECT t.traveler_id, ta.name
    FROM traveler t, reservation r, trip_package_has_destination tpd, destination d, tourist_attraction ta
    WHERE t.traveler_id = r.Customer_id
        AND r.offer_trip_package_id = tpd.trip_package_trip_package_id
        AND tpd.destination_destination_id = d.destination_id
        AND d.destination_id = ta.destination_destination_id
    """
    sql_destination = """ SELECT t.traveler_id, COUNT(DISTINCT d.country) AS country_number, COUNT(DISTINCT d.destination_id) AS destination_number 
    FROM traveler t, reservation r, trip_package_has_destination tpd, destination d
    WHERE t.traveler_id = r.Customer_id
        AND r.offer_trip_package_id = tpd.trip_package_trip_package_id
        AND tpd.destination_destination_id = d.destination_id
    GROUP BY t.traveler_id
    
    """
    # Create a new connection
    con=connection()
    # Create a cursor on the connection
    cur=con.cursor()
    # Execute sql_traveler
    cur.execute(sql_traveler)
    traveler_results=cur.fetchall()

    # Execute sql_destination
    cur.execute(sql_destination)
    destination_results=cur.fetchall()

    # Execute sql_attraction
    cur.execute(sql_attraction)
    attraction_results=cur.fetchall()

    list_of_tuples = []
    list_of_attractions= []
    max_revenue = 0
    for row in traveler_results:
        if row[2]>=max_revenue:                 #row[2] has revenue
            first_name = row[0]
            last_name = row[1]

            # Find the matching traveler_id for the destinations
            for row2 in destination_results:
                if row2[0] == row[3]:          #row2[0] and row[3] have traveler_id
                    total_countries_visited = row2[1]
                    total_cities_visited = row2[2]
                    break
            # Find the matching traveler_id for tourist_attractions
            for row3 in attraction_results:
                if row3[0] == row[3]:
                    attractions = row3[1]
                    touple2 = (attractions)
                    list_of_attractions.append(touple2)

            touple = (first_name, last_name, total_countries_visited, total_cities_visited, list_of_attractions)
            list_of_tuples.append(touple)
            max_revenue=row[2]
        else:
            break
    
    final_list = [("first_name", "last_name", "total_countries_visited", "total_cities_visited", "list_of_attractions"),] + list_of_tuples
    
    return final_list
    

def giveAway(N):

    # Travelers
    sql_traveler = """SELECT t.traveler_id, t.name, t.surname, t.gender FROM traveler t"""

    # All packages
    sql_all_packages = """SELECT distinct tpd.trip_package_trip_package_id
        FROM trip_package_has_destination tpd """
    
    # Packages that are not used
    sql_not_used_packages = """SELECT DISTINCT t.traveler_id, tpd.trip_package_trip_package_id, tp.cost_per_person
        FROM traveler t, trip_package_has_destination tpd, trip_package tp
        WHERE tpd.trip_package_trip_package_id = tp.trip_package_id
        AND NOT EXISTS (
            SELECT 1
            FROM reservation r
            where t.traveler_id = r.Customer_id
        AND r.offer_trip_package_id = tpd.trip_package_trip_package_id
        )"""
    
    # Max offer_id
    sql_max_offer_id = """SELECT max(o.offer_id)
        FROM  offer o"""
    
    # Create a new connection
    con=connection()

    # Create a cursor on the connection
    cur=con.cursor()

    # Execute sql scripts and fetchall data in variables
    cur.execute(sql_traveler)
    travelers = cur.fetchall()

    cur.execute(sql_all_packages)
    sql_all_packages = cur.fetchall()

    cur.execute(sql_not_used_packages)
    sql_not_used_pack = cur.fetchall()

    cur.execute(sql_max_offer_id)
    sql_max_offer_number = cur.fetchall()

    # Select N random travelers
    num = int(N)
    lucky_travelers = random.sample(travelers, num)

    # List for not used packages for a traveler
    list_with_not_used_packages = []
    # List for costs of not used packages
    list_with_costs = []
    # List with packages that have been already suggested to a traveler
    list_with_already_suggested_packages = []
    # List with all package's id
    list_with_all_packages = []
    # List for destinations of the suggested package
    list_of_destinations = []
    # List for the final messages of the giveaway
    list_of_tuples = []

    # Insert all packages to list
    for row in sql_all_packages:
        list_with_all_packages.append(row[0])

    # Insert number of offers per traveler in list
    for row in sql_max_offer_number:
        unique_offer_id = row[0] + 1

    # Start loop for each traveler individually
    for row in lucky_travelers:
        traveler_id = row[0]
        name = row[1]
        surname = row[2]
        gender = row[3]

        # Start loop for not used packages
        for row2 in sql_not_used_pack:
            if traveler_id == row2[0]:                          # If package corresponds to traveler_id
                list_with_not_used_packages.append(row2[1])     # Insert package_id to list
                list_with_costs.append(row2[2])                 # Insert cost_per_person to list

        # Choose a random package from list with not used packages, and save it's cost_per_person to a variable    
        suggested_package = random.choice(list_with_not_used_packages)
        cost_per_person = list_with_costs[list_with_not_used_packages.index(suggested_package)]

        # If suggested_package has already been suggested in the past, pick randomly another one
        while suggested_package in list_with_already_suggested_packages:
            suggested_package = random.choice(list_with_not_used_packages)
            cost_per_person = list_with_costs[list_with_not_used_packages.index(suggested_package)]
        
        # Insert the suggested package to list
        list_with_already_suggested_packages.append(suggested_package)
        
        # If traveler has booked more than one packages in the past, form the right discount and offer_category
        if (len(list_with_all_packages) - len(list_with_not_used_packages)) > 1 :
            discount = 25/100
            category = "group_discount"
        else:
            discount = 0
            category = "full_price"

        # Information values getting ready for insertion in database
        offer_start = date.today()
        offer_end =  offer_start + timedelta(days=30)
        cost_per_person = cost_per_person - (cost_per_person * discount)
        description = " Happy traveler tour "
        
        # Insert values in sql database
        sql_insert = """ INSERT INTO offer
        VALUES(%s,'%s','%s', %f, '%s', %s, '%s') 
        """ %(unique_offer_id, offer_start, offer_end, cost_per_person, description, suggested_package, category)
        
        # Next unique_id for the next loop
        unique_offer_id = unique_offer_id + 1

        # Clear lists so they are empty in the next loop
        list_with_not_used_packages.clear()
        list_with_costs.clear()
        
        # Execute sql_insert
        cur.execute(sql_insert)     
        con.commit()

        # Getting ready for the congratulations message output
        if gender=="male":
            prefix = "Mr"
        else:
            prefix = "Ms"
        
        destinations_names = """ SELECT d.name
                                 FROM destination d, trip_package_has_destination tpd
                                    WHERE tpd.trip_package_trip_package_id = %d
                                      AND d.destination_id = tpd.destination_destination_id  """\
                                        %(suggested_package)

        cur.execute(destinations_names)
        destination_names = cur.fetchall()

        for destination in destination_names:
            list_of_destinations.append(destination[0])


        message = """Congratulations %s %s %s!
        Pack your bags and get ready to enjoy the %s! At ART TOUR travel we
        acknowledge you as a valued customer and we have selected the most incredible
        tailor-made travel package for you. We offer you the chance to travel to %s at the incredible price of %s . Our offer ends on %s. Use code
        OFFER %d to book your trip. Enjoy these holidays that you deserve so much!"""\
            %(prefix, name, surname, description, list_of_destinations, cost_per_person, offer_end, unique_offer_id)
        
        tuple_of_strings = (message,)
        list_of_tuples.append(tuple_of_strings)

        list_of_destinations.clear()
    final_list = [("CONGRATULATIONS MESSAGE",),] + list_of_tuples

    return final_list
