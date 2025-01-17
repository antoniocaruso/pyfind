import os
import sys
from datetime import datetime,timezone
import sqlite3
from rich import print as pprint
from rich.console import Console
from rich.table import Table
import time

def sizeof_fmt(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "Ei", "Zi"):
        if abs(num) < 1000.0:
            return f"{num:3.2f} {unit}{suffix}"
        num /= 1000.0
    return f"{num:.2f} Y{suffix}"

def createdb():
    conn = sqlite3.connect('fs.db')
    cur = conn.cursor()
    #initialize tables
    try:
        cur.execute("""CREATE TABLE dir
                 (id INT PRIMARY KEY NOT NULL,
                  name TEXT NOT NULL,
                  codedpath TEXT NOT NULL);""")
        conn.commit()
        cur.execute("""CREATE TABLE filesystem
                 (id INT PRIMARY KEY NOT NULL,
                  filename TEXT NOT NULL,
                  id_path INT NOT NULL,
                  ctime BIGINT NOT NULL,
                  mtime BIGINT NOT NULL,
                  atime BIGINT NOT NULL,
                  btime BIGINT NOT NULL,
                  fsize BIGINT NOT NULL,
                  FOREIGN KEY (id_path) references dir (id));""")
        conn.commit()
        cur.execute("""CREATE INDEX idx_mdate ON filesystem(mdate);""")
    except:
        pass
    return conn,cur

def add_to_map(name,parent,mappa,cur,conn):
    l = len(mappa)
    s = '/0/' if l == 0 else parent+f'{l}/'
    mappa[l] = {'name': name, 'path': s}
    query = f'INSERT INTO dir (id,name,codedpath) VALUES ({l},"{name}","{s}");'
#    print(query)
    cur.execute(query)
    conn.commit()
    return l

def find_map(path,mappa):
    root = '/'+mappa[0]['name']
    l = len(root)
    names = path[l+1:].split('/')
    pos = 1
    coded = [0]
    end = len(mappa)
    for index,n in enumerate(names):
        trovato = False
        for i in range(pos,end):
            p = mappa[i]['path'][1:-1]
            if mappa[i]['name'] == n and '/'.join(map(str,coded+[i]))==p:
                coded += [i]
                pos = i+1
                trovato = True
                break
        if (not trovato):
            print('error:',path,",",mappa)
    return '/'+'/'.join(map(str,coded))+'/',pos-1    
                
#used
def check_path(mappa,path,codedpath):
    values = codedpath[1:-1].split('/')
    p = ''
    for v in values:
        p = p+'/'+mappa[int(v)]['name']
    return path == p
        
def checkerror(error):
    print(error)
    #sys.exit(1)

def dump_map(mappa):
    table = Table(title=f"[yellow] Mappa [/yellow]")
    table.add_column("Id", style="white")
    table.add_column("Name", style="magenta")
    table.add_column("Code", style="green")
    for k in mappa.keys():
        table.add_row(str(k),mappa[k]['name'],mappa[k]['path'])
    console = Console()
    console.print(table)
        
       
def scan(name,conn,cur,limit=30):
    mappa = {}
    filecount = 1
    dircount = 0
    depth = 1
    
    insert_query = """INSERT INTO filesystem (id, filename, id_path, ctime, mtime, atime, btime, fsize) 
                      VALUES (?,?,?,?,?,?,?,?);"""
                
    for path,folders,files in os.walk(name, onerror=checkerror):
        if depth == 1:
            mindex = add_to_map(name[1:-1],'',mappa,cur,conn)
            codedpath = mappa[mindex]['path']
        else:
            codedpath,mindex = find_map(path,mappa)
        pprint(f'{depth}: [blue]{path}[/blue]')
        folders[:] = sorted([d for d in folders \
                            if (not d.startswith(('.','$')) and d!='System Volume Information')], key=str.casefold)
        root_index = mindex
        for d in folders:
            #p = path+d if path[-1]=='/' else path+'/'+d
            dircount += 1
#            pprint(f"[red]{d}[/red]")            
            mindex = add_to_map(d,codedpath,mappa,cur,conn)
        for f in sorted(files,key=str.casefold):
            if f[0] == '.': continue
            filecount += 1
            fullname = path+"/"+f
            statinfo = os.stat(fullname)
            ctime = int(statinfo.st_ctime)
            atime = int(statinfo.st_atime)
            mtime = int(statinfo.st_mtime)
            btime = int(statinfo.st_birthtime)
            fsize = int(statinfo.st_size)
            data_tuple = (filecount,f,root_index,ctime,mtime,atime,btime,fsize)
            cur.execute(insert_query,data_tuple)            
            #print(query)
            a = time.localtime(mtime)  
            c = time.strftime('%d/%m/%Y',a)
#            pprint(f"[cyan]{sizeof_fmt(fsize) :>11}[/cyan] [grey89]{c}[/grey89] [yellow]{f}[/yellow]")
        conn.commit()
        depth += 1
        #if depth > limit: break
    dump_map(mappa)
    return filecount,dircount

if __name__ == "__main__":
    name = sys.argv[1]
    if name[-1] != '/':
        name = name + '/'
    print("Scan: ",name)
    conn,cur = createdb() 
    fc,dc = scan(name,conn,cur)
    print("indexed: ",fc," files, ", dc, ' folders.')
    conn.close()
    
