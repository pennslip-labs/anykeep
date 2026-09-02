from types import SimpleNamespace

from src.takeout_watcher import TakeoutWatcher, start_watcher


def test_watcher_processes_zip_and_deletes_after_success(tmp_path):
    archive = tmp_path / "takeout.zip"
    archive.write_bytes(b"archive")
    processed = []
    watcher = TakeoutWatcher(processed.append)

    watcher.on_created(SimpleNamespace(is_directory=False, src_path=str(archive)))

    assert processed == [archive]
    assert not archive.exists()


def test_watcher_ignores_non_zip_and_retains_failed_archive(tmp_path):
    text_file = tmp_path / "takeout.txt"
    text_file.write_text("not an archive")
    archive = tmp_path / "takeout.zip"
    archive.write_bytes(b"archive")

    processed = []

    def fail(_archive):
        processed.append("failed")
        raise ValueError("invalid archive")

    watcher = TakeoutWatcher(fail)
    watcher.on_created(SimpleNamespace(is_directory=False, src_path=str(text_file)))
    watcher.on_created(SimpleNamespace(is_directory=False, src_path=str(archive)))

    assert processed == ["failed"]
    assert text_file.exists()
    assert archive.exists()


class RecordingObserver:
    def __init__(self):
        self.scheduled = None
        self.started = False
        self.stopped = False
        self.join_count = 0

    def schedule(self, handler, path, recursive):
        self.scheduled = (handler, path, recursive)

    def start(self):
        self.started = True

    def join(self):
        self.join_count += 1
        if self.join_count == 1:
            raise KeyboardInterrupt

    def stop(self):
        self.stopped = True


def test_start_watcher_stops_observer_on_interrupt(tmp_path):
    observer = RecordingObserver()

    start_watcher(tmp_path, lambda _archive: None, observer=observer)

    assert observer.started is True
    assert observer.stopped is True
    assert observer.scheduled[1] == str(tmp_path)
    assert observer.scheduled[2] is False
    assert observer.join_count == 2