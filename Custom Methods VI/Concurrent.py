import threading
import multiprocessing
import multiprocessing.connection
import time
import typing
import psutil


class ThreadedFunction:
	def __init__(self, func: typing.Callable, catch_exceptions: bool = False):
		assert callable(func)

		self.__cb__ = func
		self.__thread__ = None  # type: None | threading.Thread
		self.__response__ = None
		self.__responded__ = 0  # 0 - False, 1 - True, 2 - Error
		self.__err_handle__ = bool(catch_exceptions)

	def __wrapper__(self, *args: tuple, **kwargs: dict):
		try:
			self.__response__ = self.__cb__(*args, **kwargs)
			self.__responded__ = 1
		except (SystemExit, KeyboardInterrupt, Exception) as err:
			self.__response__ = err
			self.__responded__ = 2

			if not self.__err_handle__:
				raise err from None

	def __call__(self, *args, **kwargs) -> None:
		self.__thread__ = threading.Thread(target=self.__wrapper__, args=args, kwargs=kwargs)
		self.__thread__.start()

	def join(self, timeout: int):
		self.__thread__.join(timeout)

	def response(self):
		if self.__responded__ == 0:
			raise RuntimeError('No response given')
		else:
			return self.__response__

	def has_erred(self) -> bool:
		if self.__responded__ == 0:
			raise RuntimeError('No response given')
		else:
			return self.__responded__ == 2

	def has_responded(self) -> bool:
		return bool(self.__responded__)


class ConcurrentFunction:
	def __init__(self, func: typing.Callable, catch_exceptions: bool = False):
		assert callable(func)

		self.__cb__ = func
		self.__thread__ = None  # type: None | multiprocessing.Process
		self.__response__ = None
		self.__responded__ = 0  # 0 - False, 1 - True, 2 - Error
		self.__err_handle__ = bool(catch_exceptions)
		self.__pipe__ = None  # type: None | multiprocessing.connection.PipeConnection

	@staticmethod
	def __wrapper__(func: typing.Callable, pipe: multiprocessing.connection.PipeConnection, *args: tuple, **kwargs: dict):
		try:
			pipe.send((True, func(*args, **kwargs)))
		except (SystemExit, KeyboardInterrupt, Exception) as err:
			pipe.send((False, err))

	def __call__(self, *args, **kwargs) -> None:
		self.__pipe__, sender = multiprocessing.Pipe(False)
		self.__thread__ = multiprocessing.Process(target=self.__wrapper__, args=(self.__cb__, sender, *args), kwargs=kwargs)
		self.__thread__.start()

	def update(self):
		if self.__pipe__.poll():
			state, res = self.__pipe__.recv()
			self.__responded__ = 1 if state else 2
			self.__response__ = res

	def join(self, timeout: int):
		self.__thread__.join(timeout)

	def suspend(self):
		psutil.Process(self.__thread__.pid).suspend()

	def resume(self):
		psutil.Process(self.__thread__.pid).resume()

	def kill(self):
		self.__thread__.kill()

	def response(self):
		self.update()

		if self.__responded__ == 0:
			raise RuntimeError('No response given')
		else:
			return self.__response__

	def has_erred(self) -> bool:
		self.update()

		if self.__responded__ == 0:
			raise RuntimeError('No response given')
		else:
			return self.__responded__ == 2

	def has_responded(self) -> bool:
		self.update()

		return bool(self.__responded__)


class ParallelFunction:
	def __init__(self, *callables):
		assert all(callable(x) for x in callables), 'One or more objects are not callable'

		self.__funcs__ = callables
		self.__pipes__ = []  # type: list[multiprocessing.connection.PipeConnection | multiprocessing.connection.Connection]
		self.__threads__ = []  # type: list[multiprocessing.Process]
		self.__response__ = []  # type: list
		self.__responded__ = []  # type: list[int]

	@staticmethod
	def __wrapper__(func: typing.Callable, pipe: multiprocessing.connection.PipeConnection, *args: tuple, **kwargs: dict):
		while not pipe.poll():
			pass

		try:
			pipe.send((True, func(*args, **kwargs)))
		except (SystemExit, KeyboardInterrupt, Exception) as err:
			pipe.send((False, err))

	def __call__(self, *args, **kwargs) -> None:
		for func in self.__funcs__:
			recv, sender = multiprocessing.Pipe(True)
			proc = multiprocessing.Process(target=self.__wrapper__, args=(func, sender, *args), kwargs=kwargs)
			self.__threads__.append(proc)
			self.__pipes__.append(recv)
			self.__response__.append(None)
			self.__responded__.append(0)
			proc.start()

		for pipe in self.__pipes__:
			pipe.send(True)

	def update(self):
		for i, pipe in enumerate(self.__pipes__):
			if self.__responded__[i] == 0 and pipe.poll():
				state, res = pipe.recv()
				self.__responded__[i] = 1 if state else 2
				self.__response__[i] = res

	def join(self):
		while any(p.is_alive() for p in self.__threads__):
			time.sleep(0.1)

	def suspend(self):
		for proc in self.__threads__:
			psutil.Process(proc.pid).suspend()

	def resume(self):
		for proc in self.__threads__:
			psutil.Process(proc.pid).resume()

	def kill(self):
		for proc in self.__threads__:
			psutil.Process(proc.pid).kill()

	def response(self, index: int = None) -> tuple | typing.Any:
		self.update()

		if index is None:
			if not all(self.__responded__):
				raise RuntimeError('No response given')
			else:
				return tuple(self.__response__)
		else:
			if self.__responded__[index] == 0:
				raise RuntimeError('No response given')
			else:
				return self.__response__[index]

	def has_erred(self, index: int = None) -> tuple[bool] | bool:
		self.update()

		if index is None:
			if not all(self.__responded__):
				raise RuntimeError('No response given')
			else:
				return tuple(x == 2 for x in self.__responded__)
		else:
			if self.__responded__[index] == 0:
				raise RuntimeError('No response given')
			else:
				return self.__responded__[index] == 2

	def has_responded(self, index: int = None) -> tuple[bool] | bool:
		self.update()

		if index is None:
			return tuple(x != 0 for x in self.__responded__)
		else:
			return self.__responded__[index] > 0

	def has_all_erred(self) -> bool:
		self.update()

		if not all(self.__responded__):
			raise RuntimeError('No response given')
		else:
			return all(x == 2 for x in self.__responded__)

	def has_all_responded(self) -> bool:
		self.update()
		return all(x != 0 for x in self.__responded__)

	def has_any_erred(self) -> bool:
		self.update()
		return any(x == 2 for x in self.__responded__)

	def has_any_responded(self) -> bool:
		self.update()
		return any(self.__responded__)
