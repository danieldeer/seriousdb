from threading import Barrier, Thread

import pytest

from seriousdb import disk_manager
from seriousdb.disk_manager import DiskManager
from seriousdb.exceptions import DiskManagerError
from seriousdb.storage_format import PAGE_SIZE
from seriousdb.types import UInt32


@pytest.fixture
def path(tmp_path):
    return tmp_path / "test.sdb"


def page(byte: int) -> bytes:
    return bytes([byte]) * PAGE_SIZE


def test_new_file_is_empty_and_first_append_is_page_zero(path):
    with DiskManager(path) as dm:
        assert dm.page_count == 0
        assert dm.allocate_page() == 0
        assert dm.allocate_page() == 1
        assert dm.page_count == 2
        assert path.stat().st_size == 2 * PAGE_SIZE


def test_round_trip_and_reopen(path):
    with DiskManager(path) as dm:
        for i in range(3):
            dm.write_page(dm.allocate_page(), page(i + 1))
        dm.sync()
    with DiskManager(path) as dm:
        assert dm.page_count == 3
        assert [dm.read_page(UInt32(i)) for i in range(3)] == [
            page(1),
            page(2),
            page(3),
        ]


def test_fresh_page_is_zeroed(path):
    with DiskManager(path) as dm:
        pid = dm.allocate_page()
        assert dm.read_page(pid) == bytes(PAGE_SIZE)


def test_misaligned_file_rejected(path):
    path.write_bytes(bytes(PAGE_SIZE + 10))
    with pytest.raises(DiskManagerError):
        DiskManager(path)
    assert path.stat().st_size == PAGE_SIZE + 10  # untouched


def test_repair_truncates_only_the_torn_tail(path):
    path.write_bytes(page(7) + page(8) + b"x" * 100)
    with DiskManager(path, repair_torn_page=True) as dm:
        assert dm.page_count == 2
        assert dm.read_page(UInt32(0)) == page(7)
        assert dm.read_page(UInt32(1)) == page(8)
    assert path.stat().st_size == 2 * PAGE_SIZE


@pytest.mark.parametrize("size", [PAGE_SIZE - 1, PAGE_SIZE + 1, 0])
def test_wrong_size_write_rejected(path, size):
    with DiskManager(path) as dm:
        dm.allocate_page()
        with pytest.raises(DiskManagerError):
            dm.write_page(UInt32(0), bytes(size))


@pytest.mark.parametrize("bad", [UInt32(1), UInt32(99), UInt32(UInt32.MAX)])
def test_out_of_range_page_id_rejected(path, bad):
    with DiskManager(path) as dm:
        dm.allocate_page()
        with pytest.raises(DiskManagerError):
            dm.read_page(bad)
        with pytest.raises(DiskManagerError):
            dm.write_page(bad, bytes(PAGE_SIZE))


def test_write_never_grows_file(path):
    with DiskManager(path) as dm:
        with pytest.raises(DiskManagerError):
            dm.write_page(UInt32(0), bytes(PAGE_SIZE))
        assert dm.page_count == 0


def test_in_range_io_does_not_call_fstat(path, monkeypatch):
    with DiskManager(path) as dm:
        dm.write_page(dm.allocate_page(), page(1))
        calls: list[int] = []
        real = disk_manager.os.fstat
        monkeypatch.setattr(
            disk_manager.os, "fstat", lambda fd: calls.append(fd) or real(fd)
        )
        dm.read_page(UInt32(0))
        dm.write_page(UInt32(0), page(2))
        assert calls == []


def test_page_allocated_by_another_handle_is_readable(path):
    with DiskManager(path) as a, DiskManager(path) as b:
        a.write_page(a.allocate_page(), page(4))
        assert b.read_page(UInt32(0)) == page(4)
        with pytest.raises(DiskManagerError):
            b.read_page(UInt32(1))


def test_close_during_io_raises(path, monkeypatch):
    with DiskManager(path) as dm:
        dm.write_page(dm.allocate_page(), page(1))
        real = dm._read_at

        def read_at(fd, size, offset):
            with pytest.raises(DiskManagerError):
                dm.close()
            return real(fd, size, offset)

        monkeypatch.setattr(dm, "_read_at", read_at)
        assert dm.read_page(UInt32(0)) == page(1)
    # The with-block closed it, so no I/O call leaked its in-flight count.
    with pytest.raises(DiskManagerError):
        dm.read_page(UInt32(0))


def test_failed_io_does_not_block_close(path):
    dm = DiskManager(path)
    with pytest.raises(DiskManagerError):
        dm.read_page(UInt32(5))
    dm.close()


def test_use_after_close_raises(path):
    dm = DiskManager(path)
    dm.close()
    dm.close()  # idempotent
    for call in (dm.allocate_page, dm.sync, lambda: dm.read_page(UInt32(0))):
        with pytest.raises(DiskManagerError):
            call()


def test_page_count_sees_other_handles_appends(path):
    with DiskManager(path) as a, DiskManager(path) as b:
        a.allocate_page()
        assert b.page_count == 1
        assert b.read_page(UInt32(0)) == bytes(PAGE_SIZE)


@pytest.mark.skipif(disk_manager._pread is None, reason="needs os.pread")
def test_short_reads_are_retried(path, monkeypatch):
    real = disk_manager._pread
    assert real is not None
    monkeypatch.setattr(
        disk_manager, "_pread", lambda fd, n, off: real(fd, min(n, 1000), off)
    )
    with DiskManager(path) as dm:
        dm.write_page(dm.allocate_page(), page(5))
        assert dm.read_page(UInt32(0)) == page(5)


@pytest.mark.skipif(disk_manager._pwrite is None, reason="needs os.pwrite")
def test_short_writes_are_retried(path, monkeypatch):
    real = disk_manager._pwrite
    assert real is not None
    monkeypatch.setattr(
        disk_manager, "_pwrite", lambda fd, data, off: real(fd, bytes(data[:1000]), off)
    )
    with DiskManager(path) as dm:
        dm.write_page(dm.allocate_page(), page(9))
        assert dm.read_page(UInt32(0)) == page(9)
    assert path.read_bytes() == page(9)


@pytest.mark.skipif(disk_manager._pread is None, reason="needs os.pread")
def test_eof_mid_page_raises(path, monkeypatch):
    with DiskManager(path) as dm:
        dm.allocate_page()
        monkeypatch.setattr(disk_manager, "_pread", lambda fd, n, off: b"")
        with pytest.raises(DiskManagerError):
            dm.read_page(UInt32(0))


def test_concurrent_allocations_get_unique_ids(path):
    with DiskManager(path) as dm:
        ids: list[int] = []
        start = Barrier(8)

        def work():
            start.wait()
            ids.extend(int(dm.allocate_page()) for _ in range(25))

        threads = [Thread(target=work) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert sorted(ids) == list(range(200))
        assert dm.page_count == 200
