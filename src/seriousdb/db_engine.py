"""this file will handle db_state and temporary WAL(Write Ahead Log) file and manage compaction"""

import json
import logging
import os
import time
from threading import Lock

from .config import COMPACT_THRESHOLD, DB_FILE, WAL_FILE, WAL_SYNC_ON_WRITE

DEFAULT_DB = {
    "default": "default"
}  # the default entry we will use to populate database when no DB_FILE found
logger = logging.getLogger(__name__)


class Db_Engine:
    def __init__(self):
        self.state = {}  # we create the db_state
        self.uncompacted_writes = 0  # number of entries that is loaded to memory and appended to WAL but not compacted yet
        self.lock = Lock()  # without RLock, when one thread try to acquire a lock that it already holds it will cause deadlock.(e.g put() accquires a lock but later calls self.compact() which also acquires the same lock)

    def boot(self):
        """first loads the DB_FILE.Then checks if any WAL_FILE with uncompacted changes is present.
        If yes then load those uncompacted changes to memory.then call compact to merge with DB_FILE"""
        with self.lock:
            # step1: Check if DB_FILE exists.If not then populate it.
            if not os.path.isfile(DB_FILE):
                with open(DB_FILE, "w") as f:
                    json.dump(DEFAULT_DB, f)
                self.state = dict(DEFAULT_DB)
            # step2: If exists then try to load and if fails save a backup adn load fresh again
            else:
                try:
                    with open(DB_FILE, "r") as f:
                        self.state = json.load(f)
                # if there is error we make a backup and start fresh
                except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
                    backup = f"{DB_FILE}.corrupt-{int(time.time())}"
                    logger.warning(
                        "Corrupt database file %s (%s); moved to %s and starting fresh",
                        DB_FILE,
                        e,
                        backup,
                    )
                    os.replace(
                        DB_FILE, backup
                    )  # atomically replace the backup file with corrupted DB_FILE
                    with open(DB_FILE, "w") as f:
                        json.dump(DEFAULT_DB, f)
                    self.state = dict(DEFAULT_DB)

            # step3: Replay the WAL file if it's present and has contents
            if os.path.isfile(WAL_FILE):
                with open(WAL_FILE, "r") as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(
                                line
                            )  # loads is being used instead of load cause we are loading string(each line in WAL file) not a file object
                            self.state.update(entry)

                # call compact to merge with DB_FILE
                self._compact_locked()

    def put(self, key: str, value: str):
        """updates memory.and also appends to the WAL_FILE. and checks if compaction is needed."""
        with self.lock:
            # step1: Update memory with new key
            self.state[key] = value

            # setp2: Append to WAL file
            with open(WAL_FILE, "a") as f:
                f.write(
                    json.dumps({key: value}) + "\n"
                )  # using dumps instead of dump cause we are working with string.not file object
                """below two lines are to make sure that the OS actually writes the WAL entry to disk before returning success to the client.
                Without flush()+fsync(), calling f.write() only puts data into Python's own internal buffer.
                If the program crashes a millisecond later, that data vanishes before reaching the WAL file on disk.

                So we do flush()+fsync() to make each PUT call crash safe:
                - flush() pushes the data out of Python's buffer via the actual write() syscall, into the OS's page cache.
                - fsync() then asks the OS to push its page cache to the disk, and waits for the disk to commit its own onboard cache to physical storage.

                This makes every single put() a bit slower, so it can be toggled via WAL_SYNC_ON_WRITE in config.py, to choose between maximum durability and high throughput.
                """
                if WAL_SYNC_ON_WRITE:
                    f.flush()  # push python buffer into OS
                    os.fsync(
                        f.fileno()
                    )  # force the OS to block execution until the bytes are stored into WAL file

            # step3: Increment the uncompacted_writes counter
            self.uncompacted_writes += 1

            # step4: Trigger compaction if needed
            if self.uncompacted_writes >= COMPACT_THRESHOLD:
                self._compact_locked()

    def get(self, key: str):
        with self.lock:
            """looks up value of a key"""
            return self.state.get(key)

    # it is the locked version.when the caller function already acquires the self.lock,it should call this function instead of compact().calling compact() will cause deadlock.
    def _compact_locked(self):
        """writes current memory into DB_FILE and clears the WAL_FILE
        NOTE:To prevent DB_FILE corruption due to crash during the compaction process
        we will first write to a temporary file,fsync() and then do a Atomic replace the old DB_FILE with new one"""
        tmp_file = f"{DB_FILE}.tmp"

        # load memory into the temp file
        with open(tmp_file, "w") as f:
            json.dump(self.state, f)
            f.flush()  # push python buffer into OS
            os.fsync(
                f.fileno()
            )  # force the OS to write it to physical disk.this is to make the operating system to actually write data from memory buffers to the physical disk, instead of leaving it sitting in a cache

        os.replace(tmp_file, DB_FILE)  # atomic replace.safe

        open(WAL_FILE, "w").close()  # trunicate the WAL to empty
        self.uncompacted_writes = 0  # set the uncompacted_write counter to zero

    # this function is called from the outside when the caller doesn't acquire the self.lock already
    def compact(self):
        with self.lock:
            self._compact_locked()
