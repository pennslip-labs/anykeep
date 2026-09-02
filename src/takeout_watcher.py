"""Watch a local directory for Google Takeout ZIP archives."""

from pathlib import Path
from typing import Callable, Optional, Union
import logging

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


ArchiveProcessor = Callable[[Path], None]
WatchDirectory = Union[str, Path]


class TakeoutWatcher(FileSystemEventHandler):
	"""Dispatch newly created Takeout archives to an ingestion callback."""

	def __init__(self, process_archive: ArchiveProcessor, auto_delete_zip: bool = True):
		super().__init__()
		self.process_archive = process_archive
		self.auto_delete_zip = auto_delete_zip
		self.logger = logging.getLogger(__name__)

	def on_created(self, event) -> None:
		"""Process newly created ZIP files and retain failed archives for retry."""
		if event.is_directory:
			return

		archive_path = Path(event.src_path)
		if archive_path.suffix.lower() != ".zip":
			return

		try:
			self.process_archive(archive_path)
		except Exception:
			self.logger.exception("Failed to process Takeout archive: %s", archive_path)
			return

		if self.auto_delete_zip:
			try:
				archive_path.unlink()
			except FileNotFoundError:
				self.logger.warning("Takeout archive disappeared before cleanup: %s", archive_path)
			except OSError:
				self.logger.exception("Failed to delete processed archive: %s", archive_path)


def start_watcher(
	watch_directory: WatchDirectory,
	process_archive: ArchiveProcessor,
	auto_delete_zip: bool = True,
	observer: Optional[Observer] = None,
) -> None:
	"""Run a blocking watchdog observer for ``watch_directory``."""
	path = Path(watch_directory).expanduser()
	if not path.exists():
		path.mkdir(parents=True, exist_ok=True)
	if not path.is_dir():
		raise NotADirectoryError(f"Watch path is not a directory: {path}")

	watcher = TakeoutWatcher(process_archive, auto_delete_zip=auto_delete_zip)
	active_observer = observer or Observer()
	active_observer.schedule(watcher, str(path), recursive=False)
	active_observer.start()
	try:
		active_observer.join()
	except KeyboardInterrupt:
		pass
	finally:
		active_observer.stop()
		active_observer.join()
