# load the room table (tools/rooms.py namespace) without writing 02_rooms.js: exec(open('tools/shots/rc/rload.py').read())
import sys, os
sys.path.insert(0, os.path.abspath('tools'))
_src = open('tools/rooms.py').read().split("if __name__ == '__main__':")[0]
_ns = {'__file__': os.path.abspath('tools/rooms.py'), '__name__': 'rooms_rc'}
exec(compile(_src, 'rooms', 'exec'), _ns)
globals().update({k: v for k, v in _ns.items() if not k.startswith('__')})
