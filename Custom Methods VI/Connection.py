# [=[ Connections.py for various socket based classes ]=]

import asyncio
import threading
import socketio
import flask_socketio as fsocketio
import flask

PRIVATE_IDS = ('connect', 'disconnect', 'error', 'join', 'leave')


class FlaskSocketioServer:
	'''
	[FlaskSocketioServer]: Operations for socketio server-side interface (Flask)\n
	Attributes:\n
	Methods:\n
	\t"@WITH": Allows for with/as use (returns FlaskSocketioServer)
	\t"listen": Opens server at host:port (returns None)
	\t"asyncListen": Opens server asyncronously (returns None)
	\t"close": Closes server via exit(0); call this last (returns None)
	\t"on": Bind callback to event id (returns function)
	\t"of": Creates a new socketio namespace (returns FlaskSocketioNamespace)
	\t"off": Remove callback from event id (returns None)
	\t"emit": Send data to all sockets (returns None)
	'''

	def __init__(self, app):
		self.__app = app
		self.__socket = fsocketio.SocketIO(app)
		self.__spaces = [FlaskSocketioNamespace(self, '/')]
		self.__state = False

	def __enter__(self, app):
		return FlaskSocketioServer(app)

	def __exit__(self, e1, e2, e3, tb):
		self.close()

	def listen(self, host: str='0.0.0.0', port: int=443):
		for nspace in self.__spaces:
			nspace.__prepare__(self.__socket)

		self.__state = True
		self.__socket.run(self.__app, host, port)

	def asyncListen(self, host: str='0.0.0.0', port: int=443):
		threading.Thread(target=self.listen, args=(host, port)).start()

	def close(self):
		self.__state = False
		exit(0)

	def on(self, eid, func=None):
		if func == None:
			def binder(func):
				self.__spaces[0].on(eid, func)
			return binder
		else:
			self.__spaces[0].on(eid, func)

	def of(self, namespace: str):
		nspace = FlaskSocketioNamespace(self, namespace)
		self.__spaces.append(nspace)
		(self.__state) and nspace.__prepare__(self.__socket)
		return nspace

	def off(self, eid):
		self.__spaces[0].off(eid)

	def emit(self, eid, *data, wl=(), bl=()):
		for nspace in self.__spaces:
			nspace.emit(eid, *data, wl=wl, bl=bl)


class FlaskSocketioNamespace:
	'''
	[FlaskSocketioNamespace]: Flask socketio namespace object\n
	Attributes:\n
	\t"ready": Checks if namespace has been prepared (bool) [GET]
	Methods:\n
	\t"on": Bind callback to event id (returns function)
	\t"off": Remove callback from event id (returns None)
	\t"emit": Send data to all sockets in namespace (returns None)
	'''

	def __init__(self, server: FlaskSocketioServer, namespace: str):
		self.__server = server
		self.__ready = False
		self.__namespace__ = namespace
		self.__events__ = {}
		self.__sockets__ = {}
		self.__socketEvents__ = {}

	def __exec__(self, eid, *args, **kwargs):
		if eid in self.__events__:
			self.__events__[eid](*args, **kwargs)

	def __prepare__(self, socket):
		@socket.on('connect', namespace=self.__namespace__)
		def onconnect(auth):
			sid = flask.request.sid
			socket = FlaskSocketioSocket(self.__server, self, sid, auth)
			self.__sockets__[sid] = socket
			self.__exec__('connect', socket)

		@socket.on('disconnect', namespace=self.__namespace__)
		def ondisconnect():
			sid = flask.request.sid
			if sid in self.__sockets__:
				self.__sockets__[sid].__exec__('disconnect', self.__sockets__[sid].__is_disconnector__)
				self.__sockets__[sid].connected = False
				del self.__sockets__[sid]

		self.__socket = socket
		self.__ready = True

	def __bindSocketEvent__(self, socket, eid):
		if eid in self.__socketEvents__:
			self.__socketEvents__[eid][socket.uid] = socket
		else:
			self.__socketEvents__[eid] = {socket.uid: socket}

			@self.__socket.on(eid, namespace=self.__namespace__)
			def onevent(*data):
				sid = flask.request.sid
				if sid in self.__socketEvents__[eid]:
					self.__socketEvents__[eid][sid].__exec__(eid, *data)

	def __unbindSocketEvent__(self, socket, eid):
		if eid in self.__socketEvents__ and socket in self.__socketEvents__[eid]:
			self.__socketEvents__[eid].remove(socket)
			if len(self.__socketEvents__[eid]) == 0:
				del self.__socketEvents__[eid]

	def __emitToSocket__(self, socket, eid, data=()):
		self.__socket.emit(eid, data, to=socket.uid, namespace=self.__namespace__)

	def on(self, eid, func=None):
		if func == None:
			def binder(func):
				if callable(func):
					self.__events__[eid] = func
				else:
					raise TypeError(f"Cannot bind non-callable object '{func}'")
			return binder
		elif callable(func):
			self.__events__[eid] = func
		else:
			raise TypeError(f"Cannot bind non-callable object '{func}'")

	def off(self, eid):
		if eid in self.__events__:
			del self.__events__[eid]

	def emit(self, eid, *data, wl=(), bl=()):
		wl = tuple([s.uid if type(s) is FlaskSocketioSocket else s for s in wl])
		bl = tuple([s.uid if type(s) is FlaskSocketioSocket else s for s in bl])

		if len(wl) > 0:
			sockets = tuple([s for s in self.__sockets__ if s in wl])
		elif len(bl) > 0:
			sockets = tuple([s for s in self.__sockets__ if s not in bl])
		else:
			sockets = self.__sockets__

		for sid in sockets:
			self.__socket.emit(eid, data, to=sid, namespace=self.__namespace__)

	@property
	def ready(self):
		return self.__ready


class FlaskSocketioSocket:
	'''
	[FlaskSocketioSocket]: Flask socketio socket object\n
	Attributes:\n
	\t"auth": Authentication info provided on connection (\x01)
	\t"uid": UID of socket (str)
	Methods:\n
	\t"on": Bind callback to event id (returns function)
	\t"off": Remove callback from event id (returns None)
	\t"emit": Send data to all sockets (returns None)
	\t"disconnect": Disconnects the socket (returns None)
	'''

	def __init__(self, server: FlaskSocketioServer, namespace: FlaskSocketioNamespace, uid: str, auth):
		self.__server = server
		self.__space = namespace
		self.__is_disconnector__ = False
		self.__uid = uid
		self.__events__ = {}
		self.auth = auth
		self.connected = True
		
	def __exec__(self, eid, *args, **kwargs):
		if eid in self.__events__:
			self.__events__[eid](*args, **kwargs)

	def __bindEvent__(self, eid, func):
		if callable(func):
			self.__events__[eid] = func

			if eid not in PRIVATE_IDS:
				self.__space.__bindSocketEvent__(self, eid)
		else:
			raise TypeError(f"Cannot bind non-callable object '{func}'")

	def on(self, eid, func=None):
		if func == None:
			def binder(func):
				self.__bindEvent__(eid, func)
			return binder
		else:
			self.__bindEvent__(eid, func)

	def off(self, eid):
		if eid in self.__events__:
			del self.__events__[eid]

			if eid not in PRIVATE_IDS:
				self.__space.__unbindSocketEvent__(self, eid)

	def emit(self, eid, *data):
		self.__space.__emitToSocket__(self, eid, data)
	
	def disconnect(self):
		self.__is_disconnector__ = True
		self.connected = False
		fsocketio.disconnect(self.__uid, self.__space.__namespace__)

	@property
	def uid(self):
		return self.__uid


class SocketioClient:
	'''
	[SocketioClient]: Operations for socketio client-side interface\n
	Attributes:\n
	Methods:\n
	\t"@WITH": Allows for with/as use (returns SocketioClient)
	\t"on": Bind callback to event id (returns function)
	\t"emit": Send data to server (returns None)
	\t"ubind": Remove callback from event id (returns None)
	\t"connect": Connect to server (returns None)
	\t"asyncConnect": Connect to server concurrently (returns None)
	\t"disconnect": Close connection (returns None)
	'''

	def __init__(self, host: str, namespace: str='/'):
		self.__host = host if host[-1] != '/' else host[0:-1]
		self.__space = namespace if namespace[0] == '/' else '/' + namespace

		self.__events = {}
		self.__soc = socketio.Client()

	def __enter__(self):
		return self

	def __exit__(self, e1, e2, e3, tb):
		self.__soc.disconnect()
    
	def __mainloop__(self):
		@self.__soc.on('connect', namespace=self.__space)
		def connection():
			while not self.__soc.connected:
				pass
			self.__exec__('connect')

		@self.__soc.on('disconnect', namespace=self.__space)
		def disconnection():
			self.__exec__('disconnect', self.__is_disconnector__)

		@self.__soc.on('error', namespace=self.__space)
		def error():
			self.__exec__('error')

		self.__soc.connect(self.__host, namespaces=self.__space, wait=False, wait_timeout=3)

	def __exec__(self, id_, *args, **kwargs):
		if id_ in self.__events:
			if asyncio.iscoroutinefunction(self.__events[id_]) == True:
				asyncio.run(self.__events[id_](*args, **kwargs))
			else:
				self.__events[id_](*args, **kwargs)

	def on(self, id_: str, func=None):
		if func == None:
			def bindEvent(callback):
				if callable(callback):
					self.__events[id_] = callback
					@self.__soc.on(id_, namespace=self.__space)
					def handler(*args, **kwargs):
						self.__exec__(id_, *args, **kwargs)
				else:
					raise TypeError('Cannot bind non-callable \'{}\''.format(callback))
			return bindEvent
		elif callable(func):
			self.__events[id_] = func
			@self.__soc.on(id_, namespace=self.__space)
			def handler(*args, **kwargs):
				self.__exec__(id_, *args, **kwargs)

	def off(self, eid: str):
		del self.__soc.handlers[self.__space][eid]

	def emit(self, id_: str, *data):
		self.__soc.emit(id_, data, namespace=self.__space)

	def ubind(self, id_: str):
		if id_ in self.__events:
			del self.__events[id_]
		else:
			raise KeyError('No bound event found with trigger \'{}\''.format(id_))

	def connect(self):
		self.__is_disconnector__ = False
		self.__mainloop__()
		self.__soc.wait()

	def asyncConnect(self):
		self.__is_disconnector__ = False
		self.__mainloop__()

	@property
	def connected(self):
		return self.__soc.connected

	def disconnect(self):
		self.__is_disconnector__ = True
		self.__soc.disconnect()
