#!/usr/bin/python3

import MySQLdb
import aims.name_cleanup as nc

connection = MySQLdb.connect(db="logbook", connect_timeout=180)

lc_replacements = dict([(X.lower(), Y) for X, Y in nc.replacements.items()])
cursor = connection.cursor()
cursor.execute("select distinct Name collate utf8mb3_bin from Crew order by Name")
replace = []
for row in cursor.fetchall():
    name = row[0]
    if name.lower() in lc_replacements:
        replace.append((lc_replacements[name.lower()], name))
        continue
    new_name = nc.clean(name)
    if new_name != name:
        replace.append((new_name, name))
update_cursor = connection.cursor()
for pair in replace:
    print(pair[1], "-->", pair[0])
    update_cursor.execute(
        "update Crew set Name = %s where Name = %s",
        pair)
response = input("Do it? [yes/no] > ")
if response == "yes":
    connection.commit()
