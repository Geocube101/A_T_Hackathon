import multiprocessing
import os
import threading
import typing

import dill
import pickle


class StreamError(IOError):
	pass


class StreamFullError(StreamError):
	pass


class StreamEmptyError(StreamError):
	pass


class Stream:
	def __init__(self, max_len: int = -1, fifo: bool | None = True):
		self.__buffer__ = []
		self.__state__ = True
		self.__fifo__ = bool(fifo)
		self.__max_length__ = int(max_len)
		self.__pipes__ = []  # type: list[tuple[Stream, typing.Callable]]

	def __len__(self):
		return self.size()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.__state__:
			self.close()

	def __del__(self):
		if self.__state__:
			self.close()

	def closed(self) -> bool:
		return not self.__state__

	def opened(self) -> bool:
		return self.__state__

	def fifo(self) -> bool:
		return False if self.__fifo__ is None else self.__fifo__

	def lifo(self) -> bool:
		return False if self.__fifo__ is None else not self.__fifo__

	def close(self) -> None:
		if not self.__state__:
			raise StreamError('Stream is closed')
		else:
			self.flush()
			self.__buffer__.clear()
			self.__state__ = False

	def empty(self) -> bool:
		return len(self.__buffer__) == 0

	def full(self) -> bool:
		return len(self.__buffer__) >= self.__max_length__ if self.__max_length__ >= 0 else False

	def size(self) -> int:
		return len(self.__buffer__)

	def open(self) -> None:
		if self.__state__:
			raise StreamError('Stream is open')
		else:
			self.__buffer__.clear()
			self.__state__ = True

	def write(self, *data) -> 'Stream':
		if self.__state__:
			for obj in data:
				if 0 <= self.__max_length__ <= len(self.__buffer__):
					raise StreamFullError('Stream is full')
				else:
					self.__buffer__.append(obj)
			return self
		else:
			raise StreamError('Stream is closed')

	def read(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(self.__buffer__.pop(0 if self.__fifo__ else -1))
			return tuple(data)
		else:
			raise StreamError('Stream is closed')

	def peek(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(self.__buffer__[i] if self.__fifo__ else self.__buffer__[-(i + 1)])
			return tuple(data)
		else:
			raise StreamError('Stream is closed')

	def pipe(self, other: 'Stream', converter: typing.Callable = None) -> 'Stream':
		assert issubclass(type(other), Stream), 'Expected stream to pipe to'
		self.__pipes__.append((other, converter))
		return self

	def flush(self) -> 'Stream':
		if self.__state__:
			if len(self.__pipes__) == 0:
				self.__buffer__.clear()
			else:
				while len(self.__buffer__) > 0:
					element = self.read(1)

					for other, converter in self.__pipes__:
						other.write(element if converter is None else converter(element))

			return self
		else:
			raise StreamError('Stream is closed')


class FileStream(Stream):
	def __init__(self, path: str, mode: str = 'r'):
		super().__init__()

		if os.path.isdir(path):
			raise IsADirectoryError(f'The object at "{path}" is a directory')
		else:
			self.__stream__ = open(path, mode)
			self.__state__ = True
			self.__fpath__ = path
			self.__mode__ = mode

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.flush()
		self.close()

	def empty(self) -> bool:
		return self.__stream__.tell() >= self.size()

	def full(self) -> bool:
		return False

	def size(self) -> int:
		cursor = self.__stream__.tell()
		self.__stream__.seek(0, 2)
		size = self.__stream__.tell()
		self.__stream__.seek(cursor, 0)
		return size

	def close(self):
		if not self.__state__:
			raise StreamError('Stream is closed')
		else:
			self.__stream__.flush()
			self.__stream__.close()
			self.__state__ = False

	def open(self):
		if self.__state__:
			raise StreamError('Stream is open')
		else:
			self.__stream__ = open(self.__fpath__, self.__mode__)
			self.__state__ = True

	def write(self, *data) -> 'FileStream':
		if self.__state__:
			din = (b'' if 'b' in self.__mode__ else '').join([x if 'b' in self.__mode__ else str(x) for x in data])
			self.__stream__.write(din)
			return self
		else:
			raise StreamError('Stream is closed')

	def read(self, count: int = -1) -> bytes | str:
		if self.__state__:
			return self.__stream__.read() if count < 0 else self.__stream__.read(count)
		else:
			raise StreamError('Stream is closed')

	def peek(self, count: int = -1) -> bytes | str:
		if self.__state__:
			cursor = self.__stream__.tell()
			dout = self.__stream__.read() if count < 0 else self.__stream__.read(count)
			self.__stream__.seek(cursor, 0)
			return dout
		else:
			raise StreamError('Stream is closed')

	def cursor(self, pos: int = None, rel: int = 0) -> 'Stream | int':
		if self.__state__:
			if pos is None:
				return self.__stream__.tell()
			else:
				self.__stream__.seek(pos, rel)
				return self
		else:
			raise StreamError('Stream is closed')

	def flush(self) -> 'FileStream':
		if self.__state__:
			self.__stream__.flush()
			return self
		else:
			raise StreamError('Stream is closed')

	def delete(self) -> 'FileStream':
		if self.__state__:
			self.close()

		os.remove(self.__fpath__)
		return self

	def create(self) -> 'FileStream':
		if self.__state__:
			raise StreamError('Stream is open')
		else:
			open(self.__fpath__, 'x').close()
			self.open()
			return self


class TypedStream(Stream):
	def __init__(self, max_len: int = -1, fifo: bool = True, *types):
		super().__init__(max_len, fifo)
		self.__types__ = []  # type: list[type]

		for t in types:
			if type(t) is not type:
				raise TypeError(f'Expected object of type "type" for type limiter, got {type(t)}')
			else:
				self.__types__.append(t)

	def types(self) -> tuple[type]:
		return tuple(self.__types__)

	def write(self, *data) -> 'Stream':
		if self.__state__:
			for obj in data:
				if 0 <= self.__max_length__ <= len(self.__buffer__):
					raise StreamFullError('Stream is full')
				elif type(obj) not in self.__types__:
					raise TypeError(f'Object "{obj}" ( type {type(obj)} ) is not in types list')
				else:
					self.__buffer__.append(obj)
			return self
		else:
			raise StreamError('Stream is closed')


class StringStream(TypedStream):
	def __init__(self, max_len: int = -1, fifo: bool = True):
		super().__init__(max_len, fifo, str)

	def read(self, count: int = -1) -> str:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(self.__buffer__.pop(0 if self.__fifo__ else -1))
			return ''.join(data)
		else:
			raise StreamError('Stream is closed')

	def peek(self, count: int = -1) -> str:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(self.__buffer__[i] if self.__fifo__ else self.__buffer__[-(i + 1)])
			return ''.join(data)
		else:
			raise StreamError('Stream is closed')


class ByteStream(TypedStream):
	def __init__(self, max_len: int = -1, fifo: bool = True):
		super().__init__(max_len, fifo, bytes, bytearray)

	def read(self, count: int = -1) -> bytes:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(self.__buffer__.pop(0 if self.__fifo__ else -1))
			return b''.join(data)
		else:
			raise StreamError('Stream is closed')

	def peek(self, count: int = -1) -> bytes:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(self.__buffer__[i] if self.__fifo__ else self.__buffer__[-(i + 1)])
			return b''.join(data)
		else:
			raise StreamError('Stream is closed')


class PickleStream(Stream):
	def __init__(self, max_len: int = -1, fifo: bool = True):
		super().__init__(max_len, fifo)

	def write(self, *data) -> 'Stream':
		if self.__state__:
			for obj in data:
				if 0 <= self.__max_length__ <= len(self.__buffer__):
					raise StreamFullError('Stream is full')
				else:
					self.__buffer__.append(pickle.dumps(obj))
			return self
		else:
			raise StreamError('Stream is closed')

	def read(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(pickle.loads(self.__buffer__.pop(0 if self.__fifo__ else -1)))
			return tuple(data)
		else:
			raise StreamError('Stream is closed')

	def read_bytes(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(self.__buffer__.pop(0 if self.__fifo__ else -1))
			return tuple(data)
		else:
			raise StreamError('Stream is closed')

	def peek(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(pickle.loads(self.__buffer__[i] if self.__fifo__ else self.__buffer__[-(i + 1)]))
			return tuple(data)
		else:
			raise StreamError('Stream is closed')

	def peek_bytes(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(self.__buffer__[i] if self.__fifo__ else self.__buffer__[-(i + 1)])
			return tuple(data)
		else:
			raise StreamError('Stream is closed')


class DillStream(Stream):
	def __init__(self, max_len: int = -1, fifo: bool = True):
		super().__init__(max_len, fifo)

	def write(self, *data) -> 'Stream':
		if self.__state__:
			for obj in data:
				if 0 <= self.__max_length__ <= len(self.__buffer__):
					raise StreamFullError('Stream is full')
				else:
					self.__buffer__.append(dill.dumps(obj))
			return self
		else:
			raise StreamError('Stream is closed')

	def read(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(dill.loads(self.__buffer__.pop(0 if self.__fifo__ else -1)))
			return tuple(data)
		else:
			raise StreamError('Stream is closed')

	def read_bytes(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(self.__buffer__.pop(0 if self.__fifo__ else -1))
			return tuple(data)
		else:
			raise StreamError('Stream is closed')

	def peek(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(dill.loads(self.__buffer__[i] if self.__fifo__ else self.__buffer__[-(i + 1)]))
			return tuple(data)
		else:
			raise StreamError('Stream is closed')

	def peek_bytes(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				data.append(self.__buffer__[i] if self.__fifo__ else self.__buffer__[-(i + 1)])
			return tuple(data)
		else:
			raise StreamError('Stream is closed')


class EventedStream(Stream):
	def __init__(self, max_len: int = -1, fifo: bool | None = True):
		super().__init__(max_len, fifo)
		self.__events__ = {'open': [], 'close': [], 'state_change': [], 'read': [], 'write': [], 'peek': []}  # type: dict[str, list[tuple[typing.Callable, int, tuple, dict]]]

	def __exec__(self, eid: str, *args):
		if eid in self.__events__:
			for func, threaded, bargs, bkwargs in self.__events__[eid]:
				if threaded == 0:
					func(*args, *bargs, **bkwargs)
				elif threaded == 1:
					threading.Thread(target=func, args=(*args, *bargs), kwargs=bkwargs).start()
				elif threaded == 2:
					multiprocessing.Process(target=func, args=(*args, *bargs), kwargs=bkwargs).start()

	def close(self) -> None:
		if not self.__state__:
			raise StreamError('Stream is closed')
		else:
			self.__buffer__.clear()
			self.__state__ = False
			self.__exec__('close')
			self.__exec__('state_change')

	def open(self) -> None:
		if self.__state__:
			raise StreamError('Stream is open')
		else:
			self.__buffer__.clear()
			self.__state__ = True
			self.__exec__('open')
			self.__exec__('state_change')

	def write(self, *data) -> 'Stream':
		if self.__state__:
			for obj in data:
				if 0 <= self.__max_length__ <= len(self.__buffer__):
					raise StreamFullError('Stream is full')
				else:
					self.__buffer__.append(obj)
					self.__exec__('write', obj)
			return self
		else:
			raise StreamError('Stream is closed')

	def read(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				obj = self.__buffer__.pop(0 if self.__fifo__ else -1)
				data.append(obj)
				self.__exec__('read', obj)
			return tuple(data)
		else:
			raise StreamError('Stream is closed')

	def peek(self, count: int = -1) -> tuple:
		if self.__state__:
			data = []
			for i in range(count if count >= 0 else len(self.__buffer__)):
				obj = self.__buffer__[i] if self.__fifo__ else self.__buffer__[-(i + 1)]
				data.append(obj)
				self.__exec__('peek', obj)
			return tuple(data)
		else:
			raise StreamError('Stream is closed')

	def pipe(self, other: 'Stream', converter: typing.Callable = None) -> 'Stream':
		assert issubclass(type(other), Stream), 'Expected stream to pipe to'

		if not self.empty():
			other.write(*(self.read() if converter is None else [converter(x) for x in self.read()]))

		return self

	def on(self, eid: str, callback: typing.Callable = None, *args, **kwargs):
		if eid not in self.__events__:
			raise KeyError(f'Invalid Event ID: \'{eid}\'')
		elif callback is None:
			def binder(func: typing.Callable):
				self.__events__[eid].append((func, 0, args, kwargs))

			return binder
		elif callable(callback):
			self.__events__[eid].append((callback, 0, args, kwargs))
		else:
			raise TypeError('Callback must be callable')

	def on_threaded(self, eid: str, callback: typing.Callable = None, *args, **kwargs):
		if eid not in self.__events__:
			raise KeyError(f'Invalid Event ID: \'{eid}\'')
		elif callback is None:
			def binder(func: typing.Callable):
				self.__events__[eid].append((func, 1, args, kwargs))

			return binder
		elif callable(callback):
			self.__events__[eid].append((callback, 1, args, kwargs))
		else:
			raise TypeError('Callback must be callable')

	def on_processes(self, eid: str, callback: typing.Callable = None, *args, **kwargs):
		if eid not in self.__events__:
			raise KeyError(f'Invalid Event ID: \'{eid}\'')
		elif callback is None:
			def binder(func: typing.Callable):
				self.__events__[eid].append((func, 2, args, kwargs))

			return binder
		elif callable(callback):
			self.__events__[eid].append((callback, 2, args, kwargs))
		else:
			raise TypeError('Callback must be callable')
