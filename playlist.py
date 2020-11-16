#!/usr/bin/env python3

import os
from datetime import datetime

import mutagen
#from mutagen.id3 import ID3, ID3NoHeaderError, TALB, TPE1, TPE2, TBPM, COMM, TCMP, TCOM, TPE3, TDRC, TPOS, TCON, TSRC, TEXT, TPUB, TIT2, TRCK, UFID, TXXX, TSOP, TSO2, APIC, TSOT, TSOA
#from mutagen.flac import FLAC


# Set up logging
import logging
log = logging.getLogger("playlister")
log_formatter = logging.Formatter("%(asctime)s - %(message)s")
log_console = logging.StreamHandler()
log_console.setFormatter(log_formatter)
log.addHandler(log_console)


def dirwalk(dir):
	"""walk a directory tree returning each directory, using a generator"""
	yield dir
	for f in sorted( os.listdir(dir) ):
		fullpath = os.path.join(dir,f)
		if os.path.isdir(fullpath) and not os.path.islink(fullpath):
			for x in dirwalk(fullpath):  # recurse into subdir
				yield x


def date_from_string(s):
	if len(s) == 4: # e.g. 2004
		return datetime.strptime(s, '%Y')
	elif len(s) == 7: # 2004-03
		return datetime.strptime(s, '%Y-%m')
	elif len(s) == 10: # 2004-03-30
		return datetime.strptime(s, '%Y-%m-%d')
	elif len(s) == 19: # 2011-04-27 10:48:00
		return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
	else:
		log.warning("Unknown format: %s", s)
		return None
		
def get_date(meta):
	'''Return a datetime of the original recording for this meta data'''
	if 'originaldate' in meta:
		return date_from_string(meta['originaldate'][0])
	elif 'date' in meta:
		return date_from_string(meta['date'][0])
	elif 'TDRC' in meta:
# TDRC: "Recording time [...] when the audio was recorded".
# TDRL: "Release time [...] when the audio was first released"
# TDOR: "Original release time [...] when the original recording of the audio was released"
		return date_from_string(str(meta['TDRC']))
		return None #meta['TDRC']
	else:
		# TODO Consider having a default date (epoch, now, user-specified)
		return None

all = dict()

def parse_single_dir(directory):
	global all
	
	# Find all files (not dirs) in this directory
	filenames = list()
	allnames = os.listdir(directory)
	for name in allnames:
		if not os.path.isdir(os.path.join(directory, name)):
			filenames.append(name)
	filenames.sort()

	media = list()
	
	runtime = 0.0
	for name in filenames:
		if name.lower().endswith(".flac") or name.lower().endswith(".mp3"):
			media.append(name)

			try:
				filepath = os.path.join(directory, name)
				meta = mutagen.File(filepath)
				if meta != None:
					runtime = runtime + meta.info.length
			except:
				pass

	# Check there are some media files in this directory
	if len(media) == 0:
		return;

	log.debug("%s %s minutes", directory, int(runtime / 60))

	for filename in media:
		filepath = os.path.join(directory, filename)
		try:
			meta = mutagen.File(filepath)
		except:
			log.error("Error parsing data from %s", filepath)
			continue
		
		date = get_date(meta)
		
		if filename.startswith("01"):
			#print date, filepath
			log.debug("%s %s", date, filepath)
		
		if date == None:
			#if filename.startswith("01"):
			#	print sorted(meta.keys()), meta['TDRC'], type(meta['TDRC']), dir(meta['TDRC'])
				#print meta
			continue
		
		if date not in all:
			all[date] = list()
		
		all[date].append(filepath)
	
		
def make_chrono_list(source_root, playlist_path = None):
	for x in dirwalk(source_root):
		parse_single_dir(x)

	# Write a playlist
	if playlist_path != None:
		log.info("Writing a playlist to %s", playlist_path)
		f  = open(playlist_path, "w")
		for date in sorted(all.keys()):
			f.write("# tracks released %s\n" % (date))
			for filepath in sorted(all[date]):
				f.write(filepath[len(source_root):] + "\n")
		f.close()


#
# Implement the command-line functionality
#
def main():
	from optparse import OptionParser

	usage = ("Usage: %prog [options]\n" +
			"\n" +
			"Create a chrolonogical playlist of all media files in the specified root directory")

	parser = OptionParser(usage=usage, version="%prog v0.1")
	parser.add_option("-o", "--playlist-path", dest="playlist_path",
					  default=None,
					  help="The path (and filename) of the playlist to generate")
	parser.add_option("-s", "--source", dest="sourcedir",
#					  default="Y:/music",
					  help="The root of the source media tree.")
	parser.add_option("-v", "--verbose", dest="debug",
                      action="store_true", default=False,
                      help="Print more information for debugging purposes")
	(options, args) = parser.parse_args()

	if options.debug:
		log.setLevel(logging.DEBUG)
	else:
		log.setLevel(logging.INFO)

	# Read the options into the global variables
	source_root = options.sourcedir
	playlist_path = options.playlist_path

	#
	# Check for required 'options'
	#
	if source_root == None:
		parser.error("Source root must be specified.")

	if playlist_path == None:
		playlist_path = os.path.join(source_root, "chronological.m3u")


	#
	# Check all directories that lie under the source root
	#
	log.info('Starting to create list from %s to %s' % (source_root, playlist_path))
	make_chrono_list(source_root, playlist_path)


if __name__ == "__main__":
	#make_chrono_list("/var/opt/source/nerina pallot/")
	main()

