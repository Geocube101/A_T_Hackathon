import typing


class JSONObject:
	def __init__(self, key: str, value):
		self.__key__ = key
		self.__val__ = value

	def __repr__(self):
		return f'<JSON_VALUE {self.__key__} = {self.__val__}>'

	def __str__(self):
		return f'"{self.__key__}": "{self.__val__}"' if type(self.__val__) is str else f'"{self.__key__}": {self.__val__}'

	def __write__(self, indent: int) -> str:
		return '\t' * indent + (f'"{self.__key__}": "{self.__val__}"' if type(self.__val__) is str else f'"{self.__key__}": {self.__val__}')


class JSONMap:
	def __init__(self, key: str | int | None, value: dict):
		self.__key__ = key
		self.__val__ = value

	def __len__(self):
		return len(self.__val__)

	def __repr__(self):
		return f'<JSON_MAP {"ROOT" if self.__key__ is None else self.__key__} with {len(self)} elements>'

	def __write__(self, indent: int) -> str:
		if len(self) == 0:
			keystr = '' if self.__key__ is None else f'"{self.__key__}": '
			return '\t' * indent + keystr + '{}'
		elif self.is_array():
			output = (('\t' * indent) + ('' if self.__key__ is None else f'"{self.__key__}": ')) + '['
			array = dict(self.__val__.values())

			for i, k in enumerate(sorted(array.keys())):
				output += ('\n' + '\t' * indent) + array[k].__write__(indent + 1) + ',' if i + 1 < len(array.keys()) else ''

			output += f'\n' + '\t' * indent + ']'
			return output
		else:
			output = ('\t' * indent) + ('' if self.__key__ is None or type(self.__key__) is int else f'"{self.__key__}": ') + '{'

			for v in self.__val__.values():
				output += ('\n' + '\t' * indent) + v.__write__(indent + 1)

			output += f'\n' + ('\t' * indent) + '}'
			return output

	def is_array(self) -> bool:
		return all(type(k) is int for k in self.__val__.keys())

	def print(self):
		print(self.__write__(0))


class JSON:
	@staticmethod
	def parse(data: str) -> JSONMap:
		if len(data) == 0:
			return JSONMap('', {})
		elif data[0] != '{':
			raise SyntaxError('Expected \'{\' to open JSON map')
		elif data[-1] != '}':
			raise SyntaxError('Expected \'{\' to close JSON map')
		else:
			tokens = JSON.__tokenize__(data[1:-1])
			json = dict(JSON.__parse__(key, val) for key, val in tokens.items())
			return JSONMap(None, json)

	@staticmethod
	def __check_key__(key: str) -> str:
		if len(key) == 0:
			raise SyntaxError('Empty key')
		elif len(key) < 2:
			raise SyntaxError(f'Malformed key: {key}')
		elif key[0] != '"' and key[-1] != '"':
			raise SyntaxError(f'Expected string literal as key, got {key}')
		else:
			return key[1:-1]

	@staticmethod
	def __parse__(key: str | int, value: str) -> tuple[str, JSONObject | JSONMap]:
		key = key if type(key) is int else JSON.__check_key__(key)

		if value.isnumeric():
			return key, JSONObject(key, int(value))
		elif value == 'true':
			return key, JSONObject(key, True)
		elif value == 'false':
			return key, JSONObject(key, False)
		elif value == 'null':
			return key, JSONObject(key, None)
		elif len(value) < 2:
			raise SyntaxError(f'Malformed value: {value}')
		elif value[0] == '"' and value[-1] == '"':
			return key, JSONObject(key, value[1:-1])
		elif value[0] == '[' and value[-1] == ']':
			tokens = JSON.__tokenize__(value[1:-1], True)
			return key, JSONMap(key, {i: JSON.__parse__(i, token) for i, token in enumerate(tokens)})
		elif value[0] == '{' and value[-1] == '}':
			tokens = JSON.__tokenize__(value[1:-1])
			json = dict(JSON.__parse__(key, val) for key, val in tokens.items())
			return key, JSONMap(key, json)
		else:
			try:
				return key, JSONObject(key, float(value))
			except ValueError:
				raise SyntaxError(f'Malformed value: {value}') from None

	@staticmethod
	def __tokenize__(data: str, isarray: bool = False) -> dict[str, typing.Any] | tuple:
		keys = []
		vals = []
		separated = False
		isstring = False
		token = ''
		controls = []
		controllers = {'}': '{', ']': '[', ')': '('}

		for c in data:
			if c == '"':
				if not isstring and len(controls) == 0 and len(token) > 0:
					raise SyntaxError(f'Expected \',\' to separate data (last token is \'{token}\')')
				elif isstring and len(controls) == 0:
					vals.append(token + c) if separated else keys.append(token + c)
					token = ''
				elif not isstring and len(controls) == 0:
					vals.append(token) if separated else keys.append(token)
					token = c
				else:
					token += c

				isstring = not isstring
			elif isstring:
				token += c
			elif c in controllers.values():
				if len(controls) == 0:
					vals.append(token) if separated else keys.append(token)
					token = c
				else:
					token += c

				controls.append(c)
			elif len(controls) > 0 and c in controllers and controllers[c] == controls[-1]:
				del controls[-1]

				if len(controls) == 0:
					token += c
					vals.append(token) if separated else keys.append(token)
					token = ''
				else:
					token += c
			elif len(controls) == 0 and c == ':':
				separated = True
				keys.append(token)
				token = ''
			elif len(controls) == 0 and c == ',':
				separated = False
				vals.append(token)
				token = ''
			elif not c.isspace():
				token += c

		if len(controls) > 0:
			if controls[-1] == '(':
				raise SyntaxError("Unclosed parenthesis in JSON string")
			elif controls[-1] == '[':
				raise SyntaxError("Unclosed square bracket in JSON string")
			elif controls[-1] == '{':
				raise SyntaxError("Unclosed curly bracket in JSON string")
		elif isstring:
			raise SyntaxError("Unclosed literal in JSON string")

		vals.append(token) if separated else keys.append(token)
		keys = [k for k in keys if len(k.strip()) > 0]
		vals = [v for v in vals if len(v.strip()) > 0]
		return tuple(keys) if isarray else {key: vals[i] for i, key in enumerate(keys)}
