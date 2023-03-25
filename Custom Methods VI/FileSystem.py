import os
import shutil

import Stream


class File:
	def __init__(self, path: str):
		self.__fpath__ = str(path)
		self.__streams__ = []  # type: list[Stream.FileStream]

		if os.path.isdir(self.__fpath__):
			raise IsADirectoryError(f'The object at "{self.__fpath__}" is a directory')

	def __repr__(self) -> str:
		return f'<FILE: "{self.__fpath__}">'

	def exists(self) -> bool:
		return os.path.isfile(self.__fpath__)

	def open(self, mode='r') -> Stream.FileStream:
		fstream = Stream.FileStream(self.__fpath__, mode)
		self.__streams__.append(fstream)
		return fstream

	def delete(self) -> bool:
		if os.path.isfile(self.__fpath__):
			for fstream in self.__streams__:
				if fstream.opened():
					fstream.close()

			self.__streams__.clear()
			os.remove(self.__fpath__)
			return True
		else:
			return False

	def create(self) -> bool:
		if os.path.isfile(self.__fpath__):
			return False
		else:
			open(self.__fpath__, 'x').close()
			return True

	def filepath(self) -> str:
		return self.__fpath__

	def filename(self) -> str:
		return os.path.basename(self.__fpath__).split('.')[0]

	def extension(self) -> str:
		return os.path.basename(self.__fpath__).split('.')[-1]

	def full_extension(self) -> str:
		return os.path.basename(self.__fpath__).split('.', 1)[-1]

	def extensions(self) -> tuple[str]:
		return tuple(os.path.basename(self.__fpath__).split('.')[1:])

	def basename(self) -> str:
		return os.path.basename(self.__fpath__)


class Directory:
	def __init__(self, path: str):
		self.__dpath__ = str(path).replace('\\', '/').rstrip('/') + '/'

		if os.path.isfile(self.__dpath__):
			raise OSError(f'The object at "{self.__dpath__}" is a file')

	def __repr__(self) -> str:
		return f'<DIRECTORY: "{self.__dpath__}">'

	def contents(self) -> dict[str, tuple['File | Directory']]:
		try:
			data = next(os.walk(self.__dpath__, True))
			return {'files': tuple(File(data[0] + x) for x in data[2]), 'dirs': tuple(Directory(data[0] + x) for x in data[1])}
		except StopIteration:
			return {}

	def files(self) -> tuple[File]:
		try:
			data = next(os.walk(self.__dpath__, True))
			return tuple(File(data[0] + x) for x in data[2])
		except StopIteration:
			return tuple()

	def dirs(self) -> tuple['Directory']:
		try:
			data = next(os.walk(self.__dpath__, True))
			return tuple(Directory(data[0] + x) for x in data[1])
		except StopIteration:
			return tuple()

	def cd(self, rel_path: str) -> 'Directory':
		return Directory(self.__dpath__ + rel_path.replace('\\', '/').lstrip('/'))

	def up(self) -> 'Directory':
		return Directory(self.__dpath__.rsplit('/', 2)[0])

	def exists(self) -> bool:
		return os.path.isdir(self.__dpath__)

	def create(self) -> bool:
		if not self.exists():
			os.makedirs(self.__dpath__)
			return True
		else:
			return False

	def createdir(self, subdir: str) -> 'Directory':
		subdir = self.cd(subdir)
		subdir.create()
		return subdir

	def delete(self) -> bool:
		if os.path.isdir(self.__dpath__):
			shutil.rmtree(self.__dpath__)
			return True
		else:
			return False

	def deletedir(self, subdir: str) -> bool:
		return self.cd(subdir).delete()

	def delfile(self, path: str) -> bool:
		fpath = self.__dpath__ + path.replace('\\', '/').lstrip('/')
		if os.path.isfile(fpath):
			os.remove(fpath)
			return True
		else:
			return False

	def file(self, path: str) -> File:
		return File(self.__dpath__ + path.replace('\\', '/').lstrip('/'))

	def directory(self, path: str) -> 'Directory':
		return Directory(self.__dpath__ + path.replace('\\', '/').lstrip('/'))

	def dirpath(self) -> str:
		return self.__dpath__

	def dirname(self) -> str:
		return self.__dpath__.split('/')[-2]
