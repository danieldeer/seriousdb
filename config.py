DB_FILE=".sdb" #the permanent database file on disk
WAL_FILE="changes.log" #temporary file to keep track of changes untill next compaction is done
COMPACT_THRESHOLD=50 #after 50 new entry we update our DB_FILE on disk
WAL_SYNC_ON_WRITE=True #make each PUT call crash safe by forcing the OS to write to WAL file.safe but slow.
