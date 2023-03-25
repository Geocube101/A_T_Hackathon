import typing
import sys


class TypedList:
	def __init__(self, cls: type, *data, converter: typing.Callable = None):
		self.__type__ = cls
		self.__converter__ = converter
		self.__buffer__ = [self.__check_return_value__(e, i) for i, e in enumerate(data)]

		for attr in dir(cls):
			if attr not in dir(self) and callable(getattr(cls, attr)):
				setattr(self, attr, lambda *args, __name=attr, **kwargs: self.__attr_wrapper__(__name, *args, **kwargs))

	# Unary

	def __pos__(self):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name)

	def __neg__(self):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name)

	def __abs__(self):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name)

	def __invert__(self):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name)

	def __round__(self, n: int = 0):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, n)

	def __floor__(self):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name)

	def __ceil__(self):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name)

	def __trunc__(self):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name)

	# Augmented

	def __iadd__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __isub__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __imul__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __ifloordiv__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __idiv__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __itruediv__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __imod__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __ipow__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __ilshift__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __irshift__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __iand__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __ior__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __ixor__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	# Str Methods

	def __str__(self):
		return f'[{", ".join(map(repr, self.__buffer__))}]'

	def __repr__(self):
		return str(self)

	def __unicode__(self):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name)

	def __format__(self, formstr):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, formstr)

	def __hash__(self):
		return id(self)

	# Operator Methods

	def __add__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __sub__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __mul__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __floordiv__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __truediv__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __mod__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __pow__(self, other, modulo=None):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other, modulo)

	def __lt__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __gt__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __le__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __ge__(self, other):
		return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __eq__(self, other):
		if type(other) is type(self):
			return self.__type__ == other.__type__ and self.__buffer__ == other.__buffer__
		else:
			return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	def __ne__(self, other):
		if type(other) is type(self):
			return not self.__eq__(other)
		else:
			return self.__magic_wrapper__(sys._getframe().f_code.co_name, other)

	# Iteration

	def __getitem__(self, item):
		return self.__buffer__[item]

	def __setitem__(self, key: int, value):
		self.__buffer__[key] = self.__check_return_value__(value)

	def __delitem__(self, key: int):
		del self.__buffer__[key]

	def __iter__(self):
		return iter(self.__buffer__)

	# Extra Private Methods

	def __attr_wrapper__(self, attr, *args, **kwargs) -> list:
		output = []

		for e in self.__buffer__:
			output.append(getattr(e, attr)(*args, **kwargs))

		return output

	def __magic_wrapper__(self, magic: str, *args, **kwargs):
		if len(self.__buffer__) == 0:
			return TypedList(self.__type__)
		elif hasattr(self.__buffer__[0], magic):
			funcs = (getattr(x, magic) for x in self.__buffer__)
			results = []

			for i, func in enumerate(funcs):
				res = func(*args, **kwargs)

				if res is NotImplemented and len(args) > 0:
					res = getattr(args[0], f'__r{magic.lstrip("_")}')(self.__buffer__[i])

				results.append(res)

			return TypedList(type(results[0]), *results)
		elif magic.lstrip('_')[0] == 'i' and hasattr(self.__buffer__[0], (method := f'__{magic.lstrip("_")[1:]}')):
			funcs = (getattr(x, method) for x in self.__buffer__)
			results = []

			for i, func in enumerate(funcs):
				res = func(*args, **kwargs)

				if res is NotImplemented and len(args) > 0:
					res = getattr(args[0], f'__r{method.lstrip("_")}')(self.__buffer__[i])

				results.append(res)

			arr = TypedList(type(results[0]), *results)
			self.__type__ = arr.__type__
			self.__buffer__ = arr.__buffer__
			return arr
		else:

			raise TypeError(f'Elements in \'TypedList\' ( type {self.__type__.__name__} ) do not overload \'{magic}\'')

	def __check_return_value__(self, value, index: int = None):
		if isinstance(value, self.__type__):
			return value
		elif callable(self.__converter__):
			try:
				res = self.__converter__(value)
				assert isinstance(res, self.__type__), f'Converter for {f"element at index {index}" if type(index) is int else "new value"} does not match type \'{self.__type__.__name__}\''
				return res
			except AssertionError as err:
				raise err from None
			except Exception:
				raise TypeError(f'{f"Element at index {index}" if type(index) is int else "New value"} does not match type \'{self.__type__.__name__}\' and cannot be coerced') from None
		else:
			try:
				return self.__type__(value)
			except Exception:
				raise TypeError(f'{f"Element at index {index}" if type(index) is int else "New value"} does not match type \'{self.__type__.__name__}\' and cannot be coerced') from None

	def __check_value_valid__(self, value) -> bool:
		if isinstance(value, self.__type__):
			return True
		elif callable(self.__converter__):
			try:
				return isinstance(self.__converter__(value), self.__type__)
			except Exception:
				return False
		else:
			try:
				self.__type__(value)
				return True
			except Exception:
				return False

	# Public Methods

	def to(self, cls: type):
		assert type(cls) is type, f'Expected class-type for TypedList conversion, got: \'{type(cls).__name__}\''
		return TypedList(cls, *[cls(x) for x in self.__buffer__])

	def apply(self, func, *args, **kwargs):
		assert callable(func), f'Expected callable object for TypedList application'
		res = [func(x, *args, **kwargs) for x in self.__buffer__]
		return TypedList(self.__type__ if len(res) == 0 else type(res[0]), *res)

	def type(self) -> type:
		return self.__type__

	def append(self, value) -> 'TypedList':
		self.__buffer__.append(self.__check_return_value__(value))
		return self

	def insert(self, index: int, value) -> 'TypedList':
		self.__buffer__.insert(index, self.__check_return_value__(value))
		return self

	def pop(self, index: int = -1):
		return self.__buffer__.pop(index)

	def clear(self) -> 'TypedList':
		self.__buffer__.clear()
		return self

	def index(self, value, start: int = 0, stop: int = None) -> int:
		return self.__buffer__.index(value, start, len(self.__buffer__) if stop is None else stop)

	def copy(self):
		return TypedList(self.__type__, *self.__buffer__)

	def extend(self, iterable, skip_invalid: bool = False) -> 'TypedList':
		assert hasattr(iterable, '__iter__'), f'Cannot extend from non-iterable: \'{type(iterable).__name__}\''

		if skip_invalid:
			self.__buffer__.extend([x for x in iterable if self.__check_value_valid__(x)])
		else:
			self.__buffer__.extend([self.__check_return_value__(x) for x in iterable])

		return self

	def reverse(self) -> 'TypedList':
		self.__buffer__.reverse()
		return self

	def reversed(self) -> 'TypedList':
		res = self.copy()
		res.__buffer__.reverse()
		return self

	def sort(self, key=None, reverse: bool = False) -> 'TypedList':
		self.__buffer__.sort(key=key, reverse=reverse)
		return self

	def sorted(self, key=None, reverse: bool = False) -> 'TypedList':
		res = self.copy()
		res.__buffer__.sort(key=key, reverse=reverse)
		return res

	def remove(self, value) -> 'TypedList':
		self.__buffer__.remove(value)
		return self

	def count(self, value) -> int:
		return self.__buffer__.count(value)


class SortedList:
	def __init__(self, *args):
		if len(args) == 0:
			self.__buffer__ = []
		elif len(args) == 1 and isinstance(args[0], type(self)):
			self.__buffer__ = args[0].__buffer__.copy()
		elif len(args) == 1:
			assert hasattr(args[0], '__iter__'), 'Set argument must be an iterable'
			self.__buffer__ = list(sorted(args[0]))
		else:
			self.__buffer__ = list(sorted(args))

	def __contains__(self, item: typing.Any) -> bool:
		return self.bin_search(item) != -1

	def __eq__(self, other: typing.Any) -> bool:
		return self.__buffer__ == other.__buffer__ if isinstance(other, type(self)) else False

	def __ne__(self, other: typing.Any) -> bool:
		return not self == other

	def __gt__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) > len(other)
		else:
			raise TypeError(f'Unsupported operands \'>\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __lt__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) < len(other)
		else:
			raise TypeError(f'Unsupported operands \'<\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __ge__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) >= len(other)
		else:
			raise TypeError(f'Unsupported operands \'>=\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __le__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) <= len(other)
		else:
			raise TypeError(f'Unsupported operands \'<=\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __add__(self, other: typing.Iterable) -> 'SortedList':
		if hasattr(other, '__iter__'):
			return self.extended(other)
		else:
			raise TypeError(f'Unsupported operands \'+\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __iadd__(self, other) -> 'SortedList':
		if hasattr(other, '__iter__'):
			self.extend(other)
			return self
		else:
			raise TypeError(f'Unsupported operands \'+=\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __radd__(self, other: typing.Iterable) -> 'SortedList':
		if hasattr(other, '__iter__'):
			return self.extended(other)
		else:
			raise TypeError(f'Unsupported operands \'+\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __mul__(self, times: int) -> 'SortedList':
		if type(times) is int:
			if len(self) == 0:
				return self.copy()

			copied = self.copy()

			for i in range(0, len(copied) * 2, 2):
				copied.__buffer__.insert(i, copied.__buffer__[i])

			return copied
		else:
			raise TypeError(f'Unsupported operands \'*\' for type \'{type(self).__name__}\' and type \'{type(times).__name__}\'')

	def __imul__(self, times: int) -> 'SortedList':
		if type(times) is int:
			if len(self) == 0:
				return self

			for i in range(0, len(self) * 2, 2):
				self.__buffer__.insert(i, self.__buffer__[i])

			return self
		else:
			raise TypeError(f'Unsupported operands \'*=\' for type \'{type(self).__name__}\' and type \'{type(times).__name__}\'')

	def __rmul__(self, times: int) -> 'SortedList':
		if type(times) is int:
			if len(self) == 0:
				return self.copy()

			copied = self.copy()

			for i in range(0, len(copied) * 2, 2):
				copied.__buffer__.insert(i, copied.__buffer__[i])

			return copied
		else:
			raise TypeError(f'Unsupported operands \'*\' for type \'{type(self).__name__}\' and type \'{type(times).__name__}\'')

	def __len__(self) -> int:
		return len(self.__buffer__)

	def __repr__(self) -> str:
		return str(self)

	def __str__(self) -> str:
		return str(self.__buffer__)

	def __iter__(self) -> typing.Iterator:
		return iter(self.__buffer__)

	def __getitem__(self, index: tuple | slice | int) -> typing.Any:
		def getter(key: tuple | slice | int) -> tuple[typing.Any, bool]:
			if type(key) is tuple:
				output = []
				for i in key:
					elem, iterable = getter(i)
					output.extend(elem) if iterable else output.append(elem)
				return SortedList(output), True
			elif type(key) is slice:
				return SortedList(self.__buffer__[key]), True
			else:
				return self.__buffer__[key], False

		return getter(index)[0]

	def __delitem__(self, index: int) -> None:
		def getter(key: tuple | slice | int) -> None:
			if type(key) is tuple:
				for i in key:
					getter(i)
			elif type(key) is slice:
				for i in range(key.start, key.stop, 1 if key.step is None else key.step):
					self.__buffer__[i] = None
			else:
				self.__buffer__[key] = None

		getter(index)

		while None in self.__buffer__:
			self.__buffer__.remove(None)

	def __reversed__(self) -> typing.Generator:
		for i in range(len(self), 0, -1):
			yield self.__buffer__[i - 1]

	def append(self, item: typing.Any) -> None:
		if len(self) == 0:
			self.__buffer__.append(item)
			return

		mid = len(self) // 2

		while True:
			if item >= self.__buffer__[-1]:
				self.__buffer__.append(item)
				break
			elif item <= self.__buffer__[0]:
				self.__buffer__.insert(0, item)
				break
			elif item == self.__buffer__[mid]:
				self.__buffer__.insert(mid, item)
				break
			elif mid + 1 < len(self) and self.__buffer__[mid] < item < self.__buffer__[mid + 1]:
				self.__buffer__.insert(mid + 1, item)
				break
			elif item < self.__buffer__[mid]:
				mid = round(mid / 2)
			elif item > self.__buffer__[mid]:
				mid = round(mid + (len(self) - mid) / 2)
			else:
				print(mid)

	def extend(self, iterable: typing.Iterable) -> None:
		for e in iterable:
			self.append(e)

	def clear(self) -> None:
		self.__buffer__.clear()

	def remove(self, item: typing.Any) -> None:
		if item in self:
			self.__buffer__.remove(item)

	def remove_all(self, item: typing.Any) -> None:
		while item in self:
			self.__buffer__.remove(item)

	def resort(self, *iterables) -> None:
		for i in iterables:
			if not hasattr(i, '__iter__'):
				raise TypeError('Arguments in resort must be iterables')
			else:
				self.__buffer__.extend(i)

		self.__buffer__.sort()

	def set_resort(self, *iterables) -> None:
		buffer = set(self.__buffer__)

		for i in iterables:
			if not hasattr(i, '__iter__'):
				raise TypeError('Arguments in resort must be iterables')
			else:
				buffer.update(i)

		self.__buffer__ = list(sorted(buffer))

	def bin_search(self, item: typing.Any, lbound: int = None, ubound: int = None) -> int:
		if len(self) == 0 or item > self.__buffer__[-1] or item < self.__buffer__[0]:
			return -1

		lower = 0
		upper = len(self)
		mid = upper // 2

		while True:
			if self[mid] == item:
				return mid
			elif mid == 0 or mid == len(self) - 1 or (lbound is not None and mid < lbound) or (ubound is not None and mid > ubound):
				return -1
			elif item > self[mid]:
				lower = mid
				mid = (lower + upper) // 2
			elif item < self[mid]:
				upper = mid
				mid = (lower + upper) // 2

	def lin_search(self, item: typing.Any, lbound: int = None, ubound: int = None) -> int:
		lbound = 0 if lbound is None else int(lbound)
		ubound = len(self) if ubound is None else int(ubound)

		for i in range(lbound, ubound):
			if self[i] == item:
				return i

		return -1

	def rlin_search(self, item: typing.Any, lbound: int = None, ubound: int = None) -> int:
		lbound = 0 if lbound is None else int(lbound)
		ubound = len(self) if ubound is None else int(ubound)

		for i in range(ubound - 1, lbound - 1, -1):
			if self[i] == item:
				return i
		return -1

	def index(self, value: typing.Any, start: int = None, stop: int = None):
		return self.bin_search(value, start, stop)

	def count(self, item: typing.Any) -> int:
		start = self.bin_search(item)

		if start == -1:
			return 0

		lb, up = self.get_bounds(item)
		return up - lb + 1

	def get_bounds(self, item: typing.Any) -> tuple[int, int]:
		start = self.bin_search(item)

		if start == -1:
			raise ValueError(f'Item \'{item}\' is not in sorted list')

		forward = start + 1
		backward = start - 1

		while backward >= 0 and self.__buffer__[backward] == item:
			backward -= 1

		while forward < len(self) and self.__buffer__[forward] == item:
			forward += 1

		return backward + 1, forward - 1

	def copy(self) -> 'SortedList':
		return SortedList(self.__buffer__.copy())

	def extended(self, iterable: typing.Iterable) -> 'SortedList':
		copied = self.copy()
		copied.extend(iterable)
		return copied

	def removed_dupls(self) -> 'SortedList':
		return SortedList(set(self.__buffer__))

	def reversed(self) -> 'ReverseSortedList':
		return ReverseSortedList(self.__buffer__)

	def pop(self, index: int) -> typing.Any:
		return self.__buffer__.pop(index)


class ReverseSortedList:
	def __init__(self, *args):
		if len(args) == 0:
			self.__buffer__ = []
		elif len(args) == 1 and isinstance(args[0], type(self)):
			self.__buffer__ = args[0].__buffer__.copy()
		elif len(args) == 1:
			assert hasattr(args[0], '__iter__'), 'Set argument must be an iterable'
			self.__buffer__ = list(sorted(args[0], reverse=True))
		else:
			self.__buffer__ = list(sorted(args, reverse=True))

	def __contains__(self, item: typing.Any) -> bool:
		return self.bin_search(item) != -1

	def __eq__(self, other: typing.Any) -> bool:
		return self.__buffer__ == other.__buffer__ if isinstance(other, type(self)) else False

	def __ne__(self, other: typing.Any) -> bool:
		return not self == other

	def __gt__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) > len(other)
		else:
			raise TypeError(f'Unsupported operands \'>\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __lt__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) < len(other)
		else:
			raise TypeError(f'Unsupported operands \'<\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __ge__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) >= len(other)
		else:
			raise TypeError(f'Unsupported operands \'>=\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __le__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) <= len(other)
		else:
			raise TypeError(f'Unsupported operands \'<=\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __add__(self, other: typing.Iterable) -> 'ReverseSortedList':
		if hasattr(other, '__iter__'):
			return self.extended(other)
		else:
			raise TypeError(f'Unsupported operands \'+\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __iadd__(self, other) -> 'ReverseSortedList':
		if hasattr(other, '__iter__'):
			self.extend(other)
			return self
		else:
			raise TypeError(f'Unsupported operands \'+=\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __radd__(self, other: typing.Iterable) -> 'ReverseSortedList':
		if hasattr(other, '__iter__'):
			return self.extended(other)
		else:
			raise TypeError(f'Unsupported operands \'+\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __mul__(self, times: int) -> 'ReverseSortedList':
		if type(times) is int:
			if len(self) == 0:
				return self.copy()

			copied = self.copy()

			for i in range(0, len(copied) * 2, 2):
				copied.__buffer__.insert(i, copied.__buffer__[i])

			return copied
		else:
			raise TypeError(f'Unsupported operands \'*\' for type \'{type(self).__name__}\' and type \'{type(times).__name__}\'')

	def __imul__(self, times: int) -> 'ReverseSortedList':
		if type(times) is int:
			if len(self) == 0:
				return self

			for i in range(0, len(self) * 2, 2):
				self.__buffer__.insert(i, self.__buffer__[i])

			return self
		else:
			raise TypeError(f'Unsupported operands \'*=\' for type \'{type(self).__name__}\' and type \'{type(times).__name__}\'')

	def __rmul__(self, times: int) -> 'ReverseSortedList':
		if type(times) is int:
			if len(self) == 0:
				return self.copy()

			copied = self.copy()

			for i in range(0, len(copied) * 2, 2):
				copied.__buffer__.insert(i, copied.__buffer__[i])

			return copied
		else:
			raise TypeError(f'Unsupported operands \'*\' for type \'{type(self).__name__}\' and type \'{type(times).__name__}\'')

	def __len__(self) -> int:
		return len(self.__buffer__)

	def __repr__(self) -> str:
		return str(self)

	def __str__(self) -> str:
		return str(self.__buffer__)

	def __iter__(self) -> typing.Iterator:
		return iter(self.__buffer__)

	def __getitem__(self, index: tuple | slice | int) -> typing.Any:
		def getter(key: tuple | slice | int) -> tuple[typing.Any, bool]:
			if type(key) is tuple:
				output = []
				for i in key:
					elem, iterable = getter(i)
					output.extend(elem) if iterable else output.append(elem)
				return ReverseSortedList(output), True
			elif type(key) is slice:
				return ReverseSortedList(self.__buffer__[key]), True
			else:
				return self.__buffer__[key], False

		return getter(index)[0]

	def __delitem__(self, index: int) -> None:
		def getter(key: tuple | slice | int) -> None:
			if type(key) is tuple:
				for i in key:
					getter(i)
			elif type(key) is slice:
				for i in range(key.start, key.stop, 1 if key.step is None else key.step):
					self.__buffer__[i] = None
			else:
				self.__buffer__[key] = None

		getter(index)

		while None in self.__buffer__:
			self.__buffer__.remove(None)

	def __reversed__(self) -> typing.Generator:
		for i in range(len(self), 0, -1):
			yield self.__buffer__[i - 1]

	def append(self, item: typing.Any) -> None:
		if len(self) == 0:
			self.__buffer__.append(item)
			return

		mid = len(self) // 2

		while True:
			if item <= self.__buffer__[-1]:
				self.__buffer__.append(item)
				break
			elif item >= self.__buffer__[0]:
				self.__buffer__.insert(0, item)
				break
			elif item == self.__buffer__[mid]:
				self.__buffer__.insert(mid, item)
				break
			elif mid - 1 >= 0 and self.__buffer__[mid - 1] < item < self.__buffer__[mid]:
				self.__buffer__.insert(mid - 1, item)
				break
			elif item > self.__buffer__[mid]:
				mid = round(mid / 2)
			elif item < self.__buffer__[mid]:
				mid = round(mid + (len(self) - mid) / 2)
			else:
				print(mid)

	def extend(self, iterable: typing.Iterable) -> None:
		for e in iterable:
			self.append(e)

	def clear(self) -> None:
		self.__buffer__.clear()

	def remove(self, item: typing.Any) -> None:
		if item in self:
			self.__buffer__.remove(item)

	def remove_all(self, item: typing.Any) -> None:
		while item in self:
			self.__buffer__.remove(item)

	def resort(self, *iterables) -> None:
		for i in iterables:
			if not hasattr(i, '__iter__'):
				raise TypeError('Arguments in resort must be iterables')
			else:
				self.__buffer__.extend(i)

		self.__buffer__.sort(reverse=True)

	def set_resort(self, *iterables) -> None:
		buffer = set(self.__buffer__)

		for i in iterables:
			if not hasattr(i, '__iter__'):
				raise TypeError('Arguments in resort must be iterables')
			else:
				buffer.update(i)

		self.__buffer__ = list(sorted(buffer, reverse=True))

	def bin_search(self, item: typing.Any, lbound: int = None, ubound: int = None) -> int:
		if len(self) == 0 or item < self.__buffer__[-1] or item > self.__buffer__[0]:
			return -1

		lower = 0
		upper = len(self)
		mid = upper // 2

		while True:
			if self[mid] == item:
				return mid
			elif mid == 0 or mid == len(self) - 1 or (lbound is not None and mid < lbound) or (ubound is not None and mid > ubound):
				return -1
			elif item < self[mid]:
				lower = mid
				mid = (lower + upper) // 2
			elif item > self[mid]:
				upper = mid
				mid = (lower + upper) // 2

	def lin_search(self, item: typing.Any, lbound: int = None, ubound: int = None) -> int:
		lbound = 0 if lbound is None else int(lbound)
		ubound = len(self) if ubound is None else int(ubound)

		for i in range(lbound, ubound):
			if self[i] == item:
				return i

		return -1

	def rlin_search(self, item: typing.Any, lbound: int = None, ubound: int = None) -> int:
		lbound = 0 if lbound is None else int(lbound)
		ubound = len(self) if ubound is None else int(ubound)

		for i in range(ubound - 1, lbound - 1, -1):
			if self[i] == item:
				return i
		return -1

	def index(self, value: typing.Any, start: int = None, stop: int = None):
		return self.bin_search(value, start, stop)

	def count(self, item: typing.Any) -> int:
		start = self.bin_search(item)

		if start == -1:
			return 0

		lb, up = self.get_bounds(item)
		return up - lb + 1

	def get_bounds(self, item: typing.Any) -> tuple[int, int]:
		start = self.bin_search(item)

		if start == -1:
			raise ValueError(f'Item \'{item}\' is not in sorted list')

		forward = start + 1
		backward = start - 1

		while backward >= 0 and self.__buffer__[backward] == item:
			backward -= 1

		while forward < len(self) and self.__buffer__[forward] == item:
			forward += 1

		return backward + 1, forward - 1

	def copy(self) -> 'ReverseSortedList':
		return ReverseSortedList(self.__buffer__.copy())

	def extended(self, iterable: typing.Iterable) -> 'ReverseSortedList':
		copied = self.copy()
		copied.extend(iterable)
		return copied

	def removed_dupls(self) -> 'ReverseSortedList':
		return ReverseSortedList(set(self.__buffer__))

	def reversed(self) -> 'SortedList':
		return SortedList(self.__buffer__)

	def pop(self, index: int) -> typing.Any:
		return self.__buffer__.pop(index)


class String:
	def __init__(self, string: str = ''):
		self.__buffer__ = list(string if hasattr(string, '__iter__') else str(string))

	def __len__(self) -> int:
		return len(self.__buffer__)


class FixedArray:
	@classmethod
	def sized(cls, length: int) -> 'FixedArray':
		arr = cls(None for i in range(length))
		return arr

	def __init__(self, *items):
		self.__size__ = len(items)
		self.__buffer__ = list(items[0] if hasattr(items[0], '__iter__') else items)

	def __contains__(self, item: typing.Any) -> bool:
		return item in self.__buffer__

	def __eq__(self, other: typing.Any) -> bool:
		return self.__buffer__ == other.__buffer__ if isinstance(other, type(self)) else False

	def __ne__(self, other: typing.Any) -> bool:
		return not self == other

	def __gt__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) > len(other)
		else:
			raise TypeError(f'Unsupported operands \'>\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __lt__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) < len(other)
		else:
			raise TypeError(f'Unsupported operands \'<\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __ge__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) >= len(other)
		else:
			raise TypeError(f'Unsupported operands \'>=\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __le__(self, other) -> bool:
		if hasattr(other, '__len__'):
			return len(self) <= len(other)
		else:
			raise TypeError(f'Unsupported operands \'<=\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __len__(self) -> int:
		return len(self.__buffer__)

	def __repr__(self) -> str:
		return str(self)

	def __str__(self) -> str:
		return str(self.__buffer__)

	def __iter__(self) -> typing.Iterator:
		return iter(self.__buffer__)

	def __getitem__(self, index: tuple | slice | int) -> typing.Any:
		def getter(key: tuple | slice | int) -> tuple[typing.Any, bool]:
			if type(key) is tuple:
				output = []
				for i in key:
					elem, iterable = getter(i)
					output.extend(elem) if iterable else output.append(elem)
				return SortedList(output), True
			elif type(key) is slice:
				return SortedList(self.__buffer__[key]), True
			else:
				return self.__buffer__[key], False

		return getter(index)[0]

	def __setitem__(self, index: tuple | slice | int, item: typing.Any) -> None:
		def setter(key: tuple | slice | int) -> None:
			if type(key) is tuple:
				for i in key:
					setter(i)
			elif type(key) is slice:
				for i in range(key.start, key.stop, 1 if key.step is None else key.step):
					self.__buffer__[i] = item
			else:
				self.__buffer__[key] = item

		setter(index)

	def __delitem__(self, index: int) -> None:
		def getter(key: tuple | slice | int) -> None:
			if type(key) is tuple:
				for i in key:
					getter(i)
			elif type(key) is slice:
				for i in range(key.start, key.stop, 1 if key.step is None else key.step):
					self.__buffer__[i] = None
			else:
				self.__buffer__[key] = None

		getter(index)

		while None in self.__buffer__:
			self.__buffer__.remove(None)

	def __reversed__(self) -> typing.Generator:
		for i in range(len(self), 0, -1):
			yield self.__buffer__[i - 1]


