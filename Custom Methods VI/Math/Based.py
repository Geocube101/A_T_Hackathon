import math


class BaseNumber:
	@classmethod
	def little(cls, base: int, digits: tuple[int]) -> 'BaseNumber':
		return cls(base, tuple(reversed(digits)))

	@classmethod
	def big(cls, base: int, digits: tuple[int]) -> 'BaseNumber':
		return cls(base, digits)

	def __init__(self, base: int, digits: tuple[int]):
		self.__base__ = int(base)  # type: int
		self.__digits__ = digits

	def to_base(self, base: int) -> 'BaseNumber':
		whole = sum(d * self.__base__ ** i for i, d in enumerate(reversed(self.__digits__)))
		return BaseN(base).convert(whole)

	def __repr__(self):
		return str(self)

	def __str__(self):
		return ''.join(str(x) if x < 9 else chr(x - 9 + 64) for x in self.__digits__)


class BaseN:
	def __init__(self, base: int):
		assert base >= 2, f'Minimum base is 2, got {base}'
		self.__base__ = int(base)  # type: int

	def __repr__(self):
		return str(self)

	def __str__(self):
		return f"Base<{self.__base__}> Converter"

	def convert(self, x: int | BaseNumber) -> BaseNumber:
		if type(x) is BaseNumber:
			return x.to_base(self.__base__)
		elif type(x) is int:
			if x == 0:
				return BaseNumber(self.__base__, (0,))
			elif x < 0:
				raise ValueError('Negative numbers not supported')

			highest = math.floor(math.log(x, self.__base__))
			digits = [0] * (highest + 1)

			for exp in range(highest, -1, -1):
				powed = self.__base__ ** exp

				if x == 0:
					break
				elif x >= powed:
					delta = x // powed
					x -= powed * delta
					digits[exp] = delta

			return BaseNumber.little(self.__base__, tuple(digits))
		else:
			raise TypeError(f"Expected type 'int' or type 'BaseNumber', got '{type(x).__name__}'")
