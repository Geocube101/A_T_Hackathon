from FileSystem import *
import os

if __name__ == '__main__':
	d = Directory(os.path.dirname(__file__))
	print(d.files()[0].basename())
