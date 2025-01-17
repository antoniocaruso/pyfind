from datetime import datetime,timezone
from dateutil.relativedelta import relativedelta

import sqlite3
import sys
import os
from rich import print as pprint
from rich.console import Console
from rich.table import Table
import argparse

def read_map(conn,cur):
    readmap = """select * from dir;"""
    cur.execute(readmap)
    s = cur.fetchall()
    mappa = {}
    for x in s:
        mappa[x[0]] = {'name': x[1], 'path': x[2]}
    #for k in mappa.keys():
    #    print(k,mappa[k])
    return mappa

def mp_to_path(mp,mappa):
    """ materialized path to real path"""
    values = mp[1:-1].split('/')
    p = ''
    for v in values:
        p = p+'/'+mappa[int(v)]['name']
    return p[18:]



def sizeof_fmt(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "Ei", "Zi"):
        if abs(num) < 1000.0:
            return f"{num:3.2f} {unit}{suffix}"
        num /= 1000.0
    return f"{num:.2f} Y{suffix}"

def search(conn,cur,begin,end,mappa,s,filters,filetype):
    print("filetype",filetype)
    begin = str(begin.date())
    end = str(end.date())
    exclude = []
    include = []
    for f in filters or []:
        if f[0] == '^':
            exclude.append(f[1:])
        else:
            include.append(f)
    query_bydate = f"""select filename,datetime(mtime,'unixepoch') as t, fsize, dir.codedpath 
        from filesystem inner join dir on filesystem.id_path = dir.id
        where t between '{begin}' and '{end}' order by t;
        """
    query_byname = f"""select filename,datetime(mtime,'unixepoch') as t, fsize, dir.codedpath as Path
        from filesystem inner join dir on filesystem.id_path = dir.id
        where t between '{begin}' and '{end}' order by Path;
        """
    query_bysize = f"""select filename,datetime(mtime,'unixepoch') as t, fsize, dir.codedpath as Path
        from filesystem inner join dir on filesystem.id_path = dir.id
        where t between '{begin}' and '{end}' order by fsize;
        """
    if s == 0:
        query = query_bydate
    elif s == 1:
        query = query_byname
    else:
        query = query_bysize
          
    cur.execute(query)
    finished = False
    count = 0
    table = Table(title=f"[yellow]from {begin} to {end}[/yellow]")
    table.add_column("Date", justify="right", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Size", justify="right", style="blue")
    while not finished:
        rows = cur.fetchmany(50)
        if len(rows) < 50:
            finished = True      
        for row in rows:
            name = row[0]
            if filetype!='':
                n,e = os.path.splitext(name)
                if e.lower() != filetype:
                    continue
            path = mp_to_path(row[3],mappa)
   
            skip = False
            for x in exclude:
                if x in path: skip = True
            if skip: continue
            
            d = datetime.fromisoformat(row[1])
            size = sizeof_fmt(row[2])
            mdate = d.strftime("%d/%m/%y %H:%M")
            skip = True
            for x in include:
                if x in path:
                    skip = False
            if len(include)==0 or not skip:
                table.add_row(mdate,path+'/'+name,size)
                count +=1
    conn.close()
    console = Console()
    console.print(table)
    print(f"Found {count} files")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("start", help="start date")
    parser.add_argument("end", help="end date")
    parser.add_argument("name", help="filename")
    parser.add_argument("-s","--sort", help="sort order", type=int, choices=[0,1,2])
    parser.add_argument("-o","--offset", help="year offset", type=int)
    parser.add_argument("-t","--type", help="file type")
    parser.add_argument("filter", help="filter", nargs="*")
    args = parser.parse_args()
    
    if args.sort:
        s = args.sort
    else:
        s = 0
    try:
        b = datetime.strptime(args.start, "%d/%m/%Y")
        e = datetime.strptime(args.end, "%d/%m/%Y")
    except:
        b = datetime.strptime("01/12/2024", "%d/%m/%Y")
        e = datetime.strptime("31/12/2024", "%d/%m/%Y")
    if args.offset:
        b = b+relativedelta(years=args.offset)
        e = e+relativedelta(years=args.offset)
    ftype = ""
    if args.type:
        ftype = '.'+args.type
        print(f"Filter with filetype = {ftype}")
    conn = sqlite3.connect(args.name)
    cur = conn.cursor()
    mappa = read_map(conn,cur)    
    search(conn,cur,b,e,mappa,s,args.filter,ftype)
    