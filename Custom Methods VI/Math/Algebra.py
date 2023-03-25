class __SolvableTerm__:
	def __init__(self, coefficient: complex | int | float, exponent: complex | int | float):
		assert isinstance(coefficient, (complex, float, int)), 'Coefficient must be a complex, float, or int'
		assert isinstance(exponent, (complex, float, int)), 'Exponent must be a complex, float, or int'
		self.coefficient = coefficient
		self.exponent = exponent

	def is_negative(self) -> bool:
		return self.coefficient < 0


class Term(__SolvableTerm__):
	def __init__(self, coefficient: complex | int | float, letter: str, exponent: complex | int | float):
		super().__init__(coefficient, exponent)
		self.letter = str(letter)[0]

	def __eq__(self, other) -> bool:
		if type(other) is type(self):
			return other.letter == self.letter
		elif type(other) is str:
			return self.letter == other
		else:
			return False

	def __repr__(self) -> str:
		return str(self)

	def __str__(self) -> str:
		return f'{self.coefficient if self.coefficient != 1 else ""}{self.letter}{f"^{self.exponent}" if self.exponent != 1 else ""}'

	def __neg__(self) -> 'Term':
		return Term(-self.coefficient, self.letter, self.exponent)

	def __pos__(self) -> 'Term':
		return Term(self.coefficient, self.letter, self.exponent)

	def __add__(self, other) -> 'Term | AddedTerm':
		if isinstance(other, type(self)):
			if other.letter == self.letter and other.exponent == self.exponent:
				return Term(self.coefficient + other.coefficient, self.letter, self.exponent)
			else:
				return AddedTerm(1, 1, self, other)
		elif issubclass(type(other), __SolvableTerm__):
			return AddedTerm(1, 1, self, other)
		else:
			raise TypeError(f'Unsupported operands \'+\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __sub__(self, other) -> 'Term | AddedTerm':
		if isinstance(other, type(self)):
			if other.letter == self.letter and other.exponent == self.exponent:
				return Term(self.coefficient + other.coefficient, self.letter, self.exponent)
			else:
				return AddedTerm(1, 1, self, -other)
		elif issubclass(type(other), __SolvableTerm__):
			return AddedTerm(1, 1, self, -other)
		else:
			raise TypeError(f'Unsupported operands \'-\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __mul__(self, other) -> 'Term | MultipliedTerm':
		if type(other) is type(self):
			if other.letter == self.letter:
				return Term(self.coefficient * other.coefficient, self.letter, self.exponent + other.exponent)
			else:
				return MultipliedTerm(1, 1, self, other)
		elif issubclass(type(other), (int, float, complex)):
			return Term(self.coefficient * other, self.letter, self.exponent)
		elif issubclass(type(other), __SolvableTerm__):
			return MultipliedTerm(1, 1, self, other)
		else:
			raise TypeError(f'Unsupported operands \'*\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __truediv__(self, other) -> 'Term | DividedTerm':
		if type(other) is type(self):
			if other.letter == self.letter:
				return Term(self.coefficient / other.coefficient, self.letter, self.exponent - other.exponent)
			else:
				return DividedTerm(1, 1, self, other)
		elif issubclass(type(other), (int, float, complex)):
			return Term(self.coefficient / other, self.letter, self.exponent)
		elif issubclass(type(other), __SolvableTerm__):
			return DividedTerm(1, 1, self, other)
		else:
			raise TypeError(f'Unsupported operands \'/\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def solve(self, value: complex | int | float) -> complex | int | float:
		return self.coefficient * value ** self.exponent


class AddedTerm(__SolvableTerm__):
	def __init__(self, coefficient: complex | int | float, exponent: complex | int | float, *terms):
		super().__init__(coefficient, exponent)
		assert all(issubclass(type(t), __SolvableTerm__) for t in terms), 'One or more terms is not a subclass of \'__SolvableTerm__\''
		self.terms = []

		for term in terms:
			if type(term) is Term:
				self.__add_term__(term)
			elif isinstance(term, type(self)) and term.exponent == self.exponent:
				for t in term.terms:
					self.__add_term__(-t if term.is_negative() else t)
				self.coefficient += term.coefficient
			else:
				self.terms.append(term)

	def __add_term__(self, term: Term):
		matched = [i for i, x in enumerate(self.terms) if x.letter == term.letter and x.exponent == term.exponent]
		if len(matched) == 1:
			self.terms[matched[0]] += term
		else:
			self.terms.append(term)

	def __repr__(self) -> str:
		return str(self)

	def __str__(self) -> str:
		parts = []

		for term in self.terms:
			if type(term) is Term:
				parts.append(repr(term))
			elif isinstance(term, type(self)) and not any(x.is_negative() for x in term.terms):
				parts.append(repr(term))
			else:
				parts.append(f'({repr(term)})')

		terms = ' + '.join(parts)
		terms = f'{terms}' if self.coefficient == 1 and self.exponent == 1 else f'({terms})'
		return f'{self.coefficient if self.coefficient != 1 else ""}{terms}{f"^{self.exponent}" if self.exponent != 1 else ""}'

	def __neg__(self) -> 'AddedTerm':
		return AddedTerm(-self.coefficient, self.exponent, *self.terms)

	def __pos__(self) -> 'AddedTerm':
		return AddedTerm(self.coefficient, self.exponent, *self.terms)

	def __add__(self, other) -> 'AddedTerm':
		if isinstance(other, Term):
			res = AddedTerm(self.coefficient, self.exponent, *self.terms)
			res.__add_term__(other)
			return res
		elif issubclass(type(other), __SolvableTerm__):
			return AddedTerm(1, 1, self, other)
		else:
			raise TypeError(f'Unsupported operands \'+\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def __sub__(self, other) -> 'AddedTerm':
		if isinstance(other, Term):
			res = AddedTerm(self.coefficient, self.exponent, *self.terms)
			res.__add_term__(-other)
			return res
		elif issubclass(type(other), __SolvableTerm__):
			return AddedTerm(1, 1, self, -other)
		else:
			raise TypeError(f'Unsupported operands \'-\' for type \'{type(self).__name__}\' and type \'{type(other).__name__}\'')

	def has_letter(self, letter: str) -> bool:
		assert len(letter) == 1, f'\'letter\' must be a single char, got: \'{letter}\''
		return any(x.letter == letter for x in self.terms)

	def solve(self, **kwargs) -> complex | float | int:
		values = {}
		total = 0

		for letter, value in kwargs.items():
			if self.has_letter(letter):
				assert issubclass(type(value), (int, float, complex)), f'Value for \'{letter}\' must be an integer, float, or complex'
				values[letter] = value

		for term in self.terms:
			assert term.letter in values, f'Unsupplied value for letter: \'{term.letter}\''
			total += term.solve(values[term.letter])

		return total


class MultipliedTerm(__SolvableTerm__):
	def __init__(self, coefficient: complex | int | float, exponent: complex | int | float, *terms):
		super().__init__(coefficient, exponent)
		assert all(issubclass(type(t), __SolvableTerm__) for t in terms), 'One or more terms is not a subclass of \'__SolvableTerm__\''
		self.terms = terms

	def __repr__(self) -> str:
		return str(self)

	def __str__(self) -> str:
		terms = ' * '.join(map(repr, self.terms))
		terms = f'{terms}' if self.coefficient == 1 and self.exponent == 1 else f'({terms})'
		return f'{self.coefficient if self.coefficient != 1 else ""}{terms}{f"^{self.exponent}" if self.exponent != 1 else ""}'

	def has_letter(self, letter: str) -> bool:
		assert len(letter) == 1, f'\'letter\' must be a single char, got: \'{letter}\''
		return any(x.letter == letter for x in self.terms)

	def solve(self, **kwargs) -> complex | float | int:
		values = {}
		total = 1

		for letter, value in kwargs.items():
			if self.has_letter(letter):
				assert issubclass(type(value), (int, float, complex)), f'Value for \'{letter}\' must be an integer, float, or complex'
				values[letter] = value

		for term in self.terms:
			assert term.letter in values, f'Unsupplied value for letter: \'{term.letter}\''
			total *= term.solve(values[term.letter])

		return total


class DividedTerm(__SolvableTerm__):
	def __init__(self, coefficient: complex | int | float, exponent: complex | int | float, *terms):
		super().__init__(coefficient, exponent)
		assert all(issubclass(type(t), __SolvableTerm__) for t in terms), 'One or more terms is not a subclass of \'__SolvableTerm__\''
		self.terms = terms

	def __repr__(self) -> str:
		return str(self)

	def __str__(self) -> str:
		terms = ' / '.join(map(repr, self.terms))
		terms = f'{terms}' if self.coefficient == 1 and self.exponent == 1 else f'({terms})'
		return f'{self.coefficient if self.coefficient != 1 else ""}{terms}{f"^{self.exponent}" if self.exponent != 1 else ""}'

	def has_letter(self, letter: str) -> bool:
		assert len(letter) == 1, f'\'letter\' must be a single char, got: \'{letter}\''
		return any(x.letter == letter for x in self.terms)

	def solve(self, **kwargs) -> complex | float | int:
		if len(self.terms) == 0:
			return self.coefficient ** self.exponent

		values = {}

		for letter, value in kwargs.items():
			if self.has_letter(letter):
				assert issubclass(type(value), (int, float, complex)), f'Value for \'{letter}\' must be an integer, float, or complex'
				values[letter] = value

		total = self.terms[0].solve(values[self.terms[0].letter])

		for i in range(1, len(self.terms)):
			term = self.terms[i]
			assert term.letter in values, f'Unsupplied value for letter: \'{term.letter}\''
			total /= term.solve(values[term.letter])

		return total
